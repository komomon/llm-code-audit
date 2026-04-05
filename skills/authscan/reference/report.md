# Phase 3: Aggregation, Report & Self-Learning

**Goal:** Aggregate all per-endpoint results, perform cross-endpoint correlation, generate final report, and capture newly discovered auth patterns.

## Step 1 — Aggregate Results

1. Load all `analysis.json` files from `results/{project_name}/*/`
2. Collect:
   - Total endpoints analyzed
   - Endpoints with risks (by severity)
   - All unique risk findings
   - All trust anchors encountered

## Step 2 — Cross-Endpoint Correlation

Look for patterns that only become visible when analyzing multiple endpoints together:

**2a. Shared Vulnerable Functions**
- If the same service/DAO function appears as `at_risk` across multiple endpoints → elevate risk severity
- Example: `OrderDAO.findById(orderId)` without auth appears in 5 endpoints → systemic issue

**2b. Global Auth Gaps**
- Compare the endpoint list from recon with global auth coverage
- Any endpoint NOT covered by global auth AND has no endpoint-level auth → flag as unauthorized access risk
- Batch report: "N endpoints lack authentication"

**2c. Inconsistent Auth Patterns**
- Same entity (e.g., Order) accessed with auth in some endpoints but without in others → flag inconsistency
- This often indicates developer oversight

## Step 3 — Risk Prioritization

Sort all findings by severity:

| Priority | Risk Type | Severity | Description |
|----------|-----------|----------|-------------|
| P0 | Unauthorized access | CRITICAL | Endpoint has no auth at all |
| P1 | Identity impersonation | CRITICAL | User-controlled identity param (userId/accountId/tenantId) used where session identity should be — attacker acts as ANY user |
| P2 | Vertical privilege escalation | HIGH | Insufficient role/permission check for the endpoint's function |
| P3 | BOLA — write (resource) | HIGH | Resource ID reaches write datasink without auth binding |
| P4 | Post-auth write risk pending | HIGH | Write operation executed before auth validation (R6) |
| P5 | BOLA — read (resource) | MEDIUM | Resource ID reaches read datasink without auth binding |
| P6 | Mass assignment | MEDIUM | Sensitive field writable from user input without filtering |
| P7 | Data leakage via output | MEDIUM | Untrusted query results returned to user |
| P8 | Information oracle | LOW | Boolean/enum return allows enumeration |
| P9 | Filter/scope param risk | LOW | Filter param without auth may expose cross-user aggregation |
| P10 | Needs manual review | INFO | Exceeded depth limit or circular call |

## Step 4 — Generate Final Report

### report.md (Human-Readable)

```markdown
# AuthScan Report — {project_name}

**Scan Date:** {date}
**Endpoints Analyzed:** {count}
**Findings:** {risk_count} risks across {endpoint_count} endpoints

## Risk Summary

| Severity | Count | Types |
|----------|-------|-------|
| CRITICAL | {n} | Unauthorized access, Identity impersonation |
| HIGH | {n} | Vertical PE, Horizontal PE (write), Post-auth write |
| MEDIUM | {n} | Horizontal PE (read), Mass assignment, Data leakage |
| LOW | {n} | Information oracle, Filter/scope param risk |

## Detailed Findings (Per Endpoint)

**Phase 3 transforms analysis.json conclusions into a clear, actionable report.** The analysis intelligence was spent in Phase 2. Here you PRESENT it so the user can immediately see: what's at risk, why, the code path, and how to fix.

**For EACH endpoint with risks, generate ALL 7 sections below. Do NOT skip any section or parameter.**

```markdown
### {endpoint} ({method}) — {highest_severity}

**Handler:** `{function}` @ `{file}:{line_start}-{line_end}`
**Trust Anchor:** {anchor} from `{source}` @ `{file}:{line}` | Credibility: {trusted/compromised}

---

#### 1. Risk Parameter Overview

| Parameter | Source | Semantic Role | Controllable When | Status | Rule | Risk Alone | Risk Combined | Severity |
|-----------|--------|---------------|-------------------|--------|------|------------|---------------|----------|
| `applyNo` | RequestBody | Resource | Always (user input) | at_risk | R8 | Access any validation record | + enterpriseId: locate any enterprise's record | HIGH |
| `enterpriseId` | RequestBody | Identity | Always (user input) | at_risk | R8+R9 | Specify any enterprise | + applyNo: full record targeting + identity substitution | CRITICAL |
| `verifyId` | RequestBody | Resource | Always (user input) | risk_pending | R8/R6 | Complete any verification | + above: complete attack chain with own verification | HIGH |

**Key:** "Controllable When" describes under what conditions the attacker can control this parameter (always / conditional / requires info leakage). "Risk Combined" describes what happens when this parameter is exploited together with other at-risk parameters.

---

#### 2. Per-Parameter Data Flow Trace

**For each at-risk parameter, trace the complete data flow with code at each step:**

##### `applyNo` (Resource) — HIGH
```
User Input: request.getApplyNo()
  │
  ↓ @ AccountServiceImpl.java:176
  │   accountRepository.load(request.getEnterpriseId(), request.getApplyNo())
  │
  ↓ @ AccountRepositoryImpl.java:223-226
  │   SQL: SELECT * FROM account_validate WHERE enterprise_id = ? AND apply_no = ?
  │   ✗ NO trust anchor in WHERE clause — R8: No Association
  │
  ↓ @ AccountServiceImpl.java:203
  │   account.setApplyNo(request.getApplyNo())  → flows to INSERT
  │
  ↓ @ AccountRepositoryImpl.java:230-233
      INSERT INTO accounts (apply_no, ...) VALUES (?, ...)
      ✗ User-controlled value written to database — AT RISK
```

##### `enterpriseId` (Identity) — CRITICAL
```
User Input: request.getEnterpriseId()
  │
  ├─ ↓ @ AccountServiceImpl.java:175
  │     accountRepository.load(request.getEnterpriseId(), request.getApplyNo())
  │     ✗ NO trust anchor — R8
  │
  └─ ↓ @ AccountServiceImpl.java:204
        account.setEnterpriseId(request.getEnterpriseId())  ← uses user input!
        ✗ Stored value accountParam.getEnterpriseId() EXISTS but NOT used — R9 Check 2 violated
        │
        ↓ @ AccountRepositoryImpl.java:231
          INSERT INTO accounts (..., enterprise_id, ...) VALUES (..., ?, ...)
          ✗ Attacker-controlled enterprise identity written — CRITICAL
```

##### `verifyId` (Resource) — HIGH
```
User Input: request.getVerifyId()
  │
  ↓ @ AccountServiceImpl.java:193
      verifyService.completeVerification(request.getVerifyId())
      ✗ External service call with side effect, NO trust anchor — R8/R6
      ✗ Attacker can complete verification using their own verifyId
```

---

#### 3. Attack Scenario

**When multiple parameters are at risk, describe how they COMBINE to form a complete attack chain.**

**Scenario: Cross-Enterprise Account Takeover**

| Step | Attacker Action | Exploited Parameter(s) | System Behavior | Code Location |
|------|----------------|----------------------|-----------------|---------------|
| 1 | Enterprise A user calls Phase 1, creates application | — | Stores: applyNo_A, enterpriseId_A, operatorUserId_A | AccountServiceImpl.java:128-143 |
| 2 | Attacker obtains applyNo_A + enterpriseId_A (interception/leakage) | — | — | — |
| 3 | Attacker calls Phase 2 with victim's applyNo + enterpriseId + own verifyId | `applyNo` + `enterpriseId` + `verifyId` | Loads victim's record, completes attacker's verification | AccountServiceImpl.java:174-195 |
| 4 | System opens account under victim's enterprise with victim's operator identity | All 3 params | **Account opened for Enterprise A — attacker succeeded** | AccountRepositoryImpl.java:230-233 |

**Parameter Interaction:**
- `applyNo` + `enterpriseId` → together locate any enterprise's validation record (combined query without anchor)
- `verifyId` → completes the verification step using attacker's own identity proof
- Three params together form a complete attack chain: locate → authenticate → execute

---

#### 4. Trust Chain Visualization

```
Trust Anchor: currentUserId @ AccountServiceImpl.java:171
  Status: COMPROMISED (noLoginExchangeUid=true, may fallback to user input — R10)
  │
  ├─✗ [HIGH] applyNo (resource)
  │     → accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223
  │     → No anchor in query → R8
  │     └─→ validateMO (untrusted result)
  │           └─✗ [CRITICAL] operatorUserId — NOT compared with currentUserId → R9 Check 1
  │
  ├─✗ [CRITICAL] enterpriseId (identity)
  │     → accountRepository.load() @ AccountRepositoryImpl.java:223 → R8
  │     → account.setEnterpriseId(request.enterpriseId) @ AccountServiceImpl.java:204
  │           └─ R9 Check 2: stored value accountParam.enterpriseId EXISTS but NOT used
  │
  └─✗ [HIGH] verifyId (resource)
        → verifyService.completeVerification(verifyId) @ AccountServiceImpl.java:193
        → External side-effect call, no anchor → R8/R6
```

---

#### 5. Key Vulnerable Code

**Show the exact code lines where the vulnerability occurs. User can jump directly to these locations.**

**Vulnerability 1 — Unscoped query (R8):** `AccountRepositoryImpl.java:223-226`
```java
// ❌ Both parameters user-controlled, no trust anchor (currentUserId) in WHERE clause
public AccountValidateMO load(String enterpriseId, String applyNo) {
    String sql = "SELECT * FROM account_validate WHERE enterprise_id = ? AND apply_no = ?";
    return jdbcTemplate.queryForObject(sql, new Object[]{enterpriseId, applyNo}, mapper);
}
```

**Vulnerability 2 — Stored identity not verified (R9 Check 1):** `AccountServiceImpl.java:189-190`
```java
// ❌ Missing: currentUserId.equals(accountParam.getOperatorUserId())
// The code proceeds directly to business operations without verifying
// that the current caller is the same person who initiated Phase 1
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
// ... no identity comparison here ...
```

**Vulnerability 3 — User input replaces stored value (R9 Check 2):** `AccountServiceImpl.java:204`
```java
// ❌ Uses request.getEnterpriseId() (user input) instead of accountParam.getEnterpriseId() (stored)
account.setEnterpriseId(request.getEnterpriseId());  // attacker can substitute any enterprise
```

---

#### 6. Remediation

**For each vulnerability, provide before/after code:**

**Fix 1 — Add trust anchor to query:**
```java
// Before (vulnerable):
accountRepository.load(request.getEnterpriseId(), request.getApplyNo());

// After (fixed) — add currentUserId to query, or validate after load:
AccountValidateMO mo = accountRepository.loadByApplyNo(request.getApplyNo());
if (!currentUserId.equals(mo.getOperatorUserId())) {
    throw new AccessDeniedException("Not the original operator");
}
```

**Fix 2 — Verify stored identity (R9 Check 1):**
```java
// Before (vulnerable): no comparison
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);

// After (fixed): add identity verification
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
if (!currentUserId.equals(accountParam.getOperatorUserId())) {
    throw new BusinessException("非本人操作，拒绝执行");
}
```

**Fix 3 — Use stored values (R9 Check 2):**
```java
// Before (vulnerable):
account.setEnterpriseId(request.getEnterpriseId());

// After (fixed):
account.setEnterpriseId(accountParam.getEnterpriseId());  // use stored value
```

---
```

(Repeat the above 7-section structure for each endpoint with findings)

**Key guidelines:**
- Do NOT skip parameters. If 3 params are at_risk, all 3 must appear in sections 1-2.
- Do NOT write isolated per-parameter attack stories. Section 3 must show how params COMBINE.
- Section 5 (Key Vulnerable Code) is critical — show the actual code so users can verify immediately.
- Every code reference must include `file:line` for direct navigation.
- Data flow traces (section 2) use the `flow_path` from analysis.json — expand into readable format.

## Cross-Endpoint Issues

### Shared Vulnerable Functions
{list}

### Auth Coverage Gaps
{list}

## Remediation Recommendations

### For Unauthorized Access (P0)
Add authentication to the endpoint. Ensure global auth filter/interceptor covers the path.

### For Vertical Privilege Escalation (P1)
Add role/permission check matching the endpoint's privilege requirement.

### For Horizontal Privilege Escalation (P2-P3)
Add trust anchor (session user ID) to the data operation's constraint:
- Query: add `WHERE ... AND user_id = {session_uid}`
- Or: add ownership check before data access

### For Post-Auth Write (P4)
Move the authorization check BEFORE the write operation.

### For Mass Assignment (P5)
Use explicit field whitelists or dedicated DTOs that exclude sensitive fields.

## Appendix: All Analyzed Endpoints
| Endpoint | Risk Level | Findings |
|----------|-----------|----------|
| ... | ... | ... |
```

### report.json (Machine-Readable)

```json
{
  "project": "{project_name}",
  "scan_date": "{date}",
  "summary": {
    "total_endpoints": 0,
    "endpoints_with_risks": 0,
    "total_findings": 0,
    "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
    "by_type": {
      "unauthorized_access": 0,
      "identity_impersonation": 0,
      "vertical_privilege_escalation": 0,
      "bola_write": 0,
      "bola_read": 0,
      "mass_assignment": 0,
      "data_leakage": 0,
      "parameter_leakage": 0,
      "info_oracle": 0
    }
  },
  "endpoints": [
    {
      "endpoint": "/api/account/confirm",
      "method": "POST",
      "handler": {
        "function": "AccountServiceImpl.confirmAccount",
        "file": "src/main/java/com/example/service/AccountServiceImpl.java",
        "line_start": 170,
        "line_end": 214
      },
      "overall_severity": "CRITICAL",
      "trust_anchors": [
        {
          "name": "currentUserId",
          "source": "SecurityContext.getCurrentUserId()",
          "file": "src/main/java/com/example/service/AccountServiceImpl.java",
          "line": 171,
          "credibility": "compromised",
          "credibility_reason": "noLoginExchangeUid=true, may fallback to user input (R10)"
        }
      ],
      "parameter_risks": [
        {
          "param": "applyNo",
          "semantic_role": "resource",
          "trust_status": "at_risk",
          "trust_rule": "R8",
          "severity": "HIGH",
          "reason": "applyNo flows to repository.load() without trust anchor binding",
          "flow_path": [
            "request.getApplyNo() @ AccountServiceImpl.java:176",
            "accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223",
            "SELECT WHERE enterprise_id=? AND apply_no=? (no anchor) @ AccountRepositoryImpl.java:226"
          ],
          "datasink": {
            "function": "AccountRepositoryImpl.load",
            "file": "src/main/java/com/example/repo/AccountRepositoryImpl.java",
            "line_start": 223,
            "line_end": 227,
            "op_type": "read"
          }
        },
        {
          "param": "enterpriseId",
          "semantic_role": "identity",
          "trust_status": "at_risk",
          "trust_rule": "R8+R9",
          "severity": "CRITICAL",
          "reason": "Identity param used in query without anchor (R8). Stored value exists but code uses user input instead (R9 Check 2).",
          "flow_path": [
            "request.getEnterpriseId() @ AccountServiceImpl.java:175",
            "accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223",
            "account.setEnterpriseId(request.getEnterpriseId()) @ AccountServiceImpl.java:204",
            "INSERT INTO accounts (..., enterprise_id, ...) @ AccountRepositoryImpl.java:231"
          ],
          "datasink": {
            "function": "AccountRepositoryImpl.openAccount",
            "file": "src/main/java/com/example/repo/AccountRepositoryImpl.java",
            "line_start": 230,
            "line_end": 234,
            "op_type": "write"
          }
        }
      ],
      "r9_analysis": {
        "triggered": true,
        "stored_identity_fields": ["operatorUserId", "ipRoleId"],
        "check1_identity_comparison": {
          "passed": false,
          "detail": "No code compares currentUserId with accountParam.getOperatorUserId()"
        },
        "check2_stored_value_usage": {
          "passed": false,
          "detail": "account.setEnterpriseId(request.getEnterpriseId()) uses input, not accountParam.getEnterpriseId()"
        }
      },
      "combination_risks": [
        {
          "params": ["applyNo", "enterpriseId"],
          "combined_severity": "CRITICAL",
          "description": "Both params combine in repository.load() to locate any enterprise's validation record without trust anchor constraint",
          "trust_anchor_present": false
        },
        {
          "params": ["applyNo", "enterpriseId", "verifyId"],
          "combined_severity": "CRITICAL",
          "description": "Full attack chain: locate victim record + substitute enterprise + complete with attacker's verification",
          "trust_anchor_present": false
        }
      ],
      "output_risks": [],
      "mass_assignment_risks": [],
      "remediation_summary": "Add currentUserId ownership check (R9 Check 1), use stored values for business fields (R9 Check 2), add trust anchor to repository.load() query"
    }
  ],
  "cross_endpoint_issues": {
    "shared_vulnerable_functions": [],
    "auth_coverage_gaps": [],
    "inconsistent_patterns": []
  },
  "discovered_patterns": []
}
```

### report-summary.md (综合安全报告 — 面向安全团队+开发团队)

**用途：** 生成一份**既易懂又有技术深度**的综合报告。安全运营/数据安全同学能读懂风险和攻击逻辑，开发/安全工程师能直接定位代码问题。

**生成时机：** 在 report.md（纯技术报告）生成后，基于同一份分析数据，转换为以下格式。

```markdown
# 越权漏洞审计报告 — {project_name}

**审计日期：** {date}
**审计范围：** {count} 个接口
**发现问题：** {risk_count} 个风险点

---

## 一、总体结论

| 风险等级 | 数量 | 说明 |
|---------|------|------|
| 🔴 严重 | {n} | 可被外部攻击者直接利用，影响范围大 |
| 🟠 高危 | {n} | 需要一定条件才能利用，但影响严重 |
| 🟡 中危 | {n} | 存在风险但利用难度较高或影响有限 |
| 🟢 低危 | {n} | 理论上存在风险，实际利用可能性小 |

**一句话总结：** {如："账户开通确认接口存在越权漏洞，攻击者可以为任意企业开通账户。"}

---

## 二、详细风险分析

**每个风险用"卡片"呈现，包含 8 个模块。非技术同学重点看模块 ①③⑦⑧，开发同学重点看模块 ④⑤⑥。**

---

### 风险 1：{风险标题，如"任意企业账户可被他人开通"} — 🔴 严重

#### ① 风险概述

| 维度 | 说明 |
|------|------|
| **涉及接口** | `POST /api/account/confirm`（账户开通确认） |
| **接口功能** | 用户提交申请后，通过此接口完成身份验证并正式开通账户 |
| **风险类型** | 越权操作 + 身份冒用 |
| **影响范围** | 所有企业的待开通申请都可能被攻击者操作 |
| **攻击条件** | 攻击者需要获取目标企业的申请编号（可通过抓包、日志泄露等途径） |
| **业务影响** | 攻击者可以为非本人/非本企业开通账户，造成业务数据错乱和资金风险 |

**通俗解释：**
> 这个接口就像一个"确认开户"的窗口。正常流程是：用户先申请（拿到申请编号），然后到这个窗口确认。但这个窗口**没有核实来人是不是申请人本人**——只要你拿着别人的申请编号，就能替别人确认开户。

#### ② 接口定义

**请求：** `POST /api/account/confirm`

**请求参数：**

| 参数名 | 类型 | 说明 | 来源 |
|--------|------|------|------|
| `applyNo` | String | 申请流水号（一阶段返回给用户的） | 用户输入 |
| `enterpriseId` | String | 企业ID | 用户输入 |
| `verifyId` | String | 身份验证ID（一阶段返回给用户的） | 用户输入 |

**处理函数：** `AccountServiceImpl.confirmAccount()` @ `AccountServiceImpl.java:170-214`

**身份验证方式：** `@AuthAnnotation(noLoginExchangeUid = true)` ⚠️ 允许无登录态调用

#### ③ 参数风险表

| 参数 | 通俗含义 | 是否可篡改 | 单独风险 | 与其他参数组合后的风险 | 严重程度 |
|------|---------|-----------|---------|---------------------|---------|
| `applyNo` | 申请编号 — 标识哪一条申请 | ✅ 用户可改成任意值 | 可以访问任意申请记录 | + `enterpriseId`：精确定位任意企业的申请 | 🟠 高危 |
| `enterpriseId` | 企业标识 — 标识哪个企业 | ✅ 用户可改成任意值 | 可以指定任意企业 | + `applyNo`：冒充该企业完成开户 | 🔴 严重 |
| `verifyId` | 身份验证标识 — 对应一次核身验证 | ✅ 用户可改成任意值 | 可以使用自己的验证完成他人的申请 | + 以上两个：完整攻击链 | 🟠 高危 |

**系统用来确认"你是谁"的信息（🔒信任锚点）：**
- `currentUserId` — 来自 `SecurityContext.getCurrentUserId()`
- ⚠️ 但此接口标注了 `noLoginExchangeUid = true`（允许无登录态），信任锚点可能不可靠

#### ④ 关键代码片段

**以下是存在问题的代码，已标注关键信息：**

**漏洞点 1 — 查询时未校验"你是谁"：** `AccountRepositoryImpl.java:223-226`
```java
public AccountValidateMO load(String enterpriseId, String applyNo) {
    //                              ⬆️ 用户可控         ⬆️ 用户可控
    String sql = "SELECT * FROM account_validate WHERE enterprise_id = ? AND apply_no = ?";
    //           ❌ 漏洞：WHERE 条件中没有当前用户ID（🔒信任锚点），任何人都能查到任何记录
    return jdbcTemplate.queryForObject(sql, new Object[]{enterpriseId, applyNo}, mapper);
}
```

**漏洞点 2 — 未验证操作人身份：** `AccountServiceImpl.java:184-190`
```java
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
// accountParam.getOperatorUserId() = 一阶段申请人的ID（📦 数据库中存储的身份）

// ❌ 漏洞：缺少以下关键校验：
// if (!currentUserId.equals(accountParam.getOperatorUserId())) {
//     throw new BusinessException("非本人操作");
// }
// 没有核对"当前操作人（🔒信任锚点）"是不是"一阶段的申请人（📦 存储身份）"
```

**漏洞点 3 — 使用用户输入而非系统存储值：** `AccountServiceImpl.java:204`
```java
account.setEnterpriseId(request.getEnterpriseId());  // ⬆️ 用户可控 — 攻击者可以填入任意企业ID
//                      ❌ 应该使用：accountParam.getEnterpriseId()（📦 一阶段存储的正确值）
```

**标注说明：**
- `⬆️ 用户可控` — 这个值来自用户请求，攻击者可以任意修改
- `🔒 信任锚点` — 系统用来确认用户身份的可信信息（如登录态中的用户ID）
- `📦 存储数据` — 系统在之前的步骤中保存到数据库的信息
- `❌ 漏洞` — 问题代码所在位置

#### ⑤ 参数数据流追踪

**展示每个风险参数从"用户输入"到"最终影响"的完整路径：**

```
applyNo 的数据流：
─────────────────
用户请求 request.getApplyNo()                                     ⬆️ 用户可控
  │
  ↓ AccountServiceImpl.java:176
  │  传入 accountRepository.load(enterpriseId, applyNo)
  │
  ↓ AccountRepositoryImpl.java:223
  │  SQL: SELECT * FROM account_validate
  │       WHERE enterprise_id = ? AND apply_no = ?               ❌ 无🔒信任锚点
  │  → 返回任意企业的申请记录
  │
  ↓ AccountServiceImpl.java:203
  │  account.setApplyNo(request.getApplyNo())
  │
  ↓ AccountRepositoryImpl.java:230
     INSERT INTO accounts (apply_no, ...)                        ❌ 攻击者控制的值写入数据库


enterpriseId 的数据流：
──────────────────────
用户请求 request.getEnterpriseId()                                ⬆️ 用户可控
  │
  ├─→ AccountServiceImpl.java:175
  │   传入 accountRepository.load(enterpriseId, applyNo)         ❌ 无🔒信任锚点
  │
  └─→ AccountServiceImpl.java:204
      account.setEnterpriseId(request.getEnterpriseId())         ❌ 应使用📦存储值
      │
      ↓ AccountRepositoryImpl.java:231
        INSERT INTO accounts (..., enterprise_id, ...)           ❌ 攻击者指定的企业ID写入


verifyId 的数据流：
──────────────────
用户请求 request.getVerifyId()                                    ⬆️ 用户可控
  │
  ↓ AccountServiceImpl.java:193
     verifyService.completeVerification(request.getVerifyId())   ❌ 无🔒信任锚点
     → 攻击者可以用自己的验证ID完成他人的申请验证                     ❌ 不可逆的外部操作
```

#### ⑥ 函数调用链

**展示请求从入口到数据库的完整调用路径：**

```
用户请求 POST /api/account/confirm
  │
  ↓ [入口] AccountServiceImpl.confirmAccount()
  │         文件: AccountServiceImpl.java:170-214
  │         职责: 接收请求，协调业务逻辑
  │
  ├─→ [数据查询] AccountRepositoryImpl.load(enterpriseId, applyNo)
  │               文件: AccountRepositoryImpl.java:223-227
  │               SQL:  SELECT * FROM account_validate WHERE enterprise_id=? AND apply_no=?
  │               问题: ❌ 查询条件全部来自⬆️用户输入，没有🔒信任锚点
  │
  ├─→ [外部调用] VerifyService.completeVerification(verifyId)
  │               问题: ❌ verifyId 来自⬆️用户输入，未验证归属
  │
  └─→ [数据写入] AccountRepositoryImpl.openAccount(account)
                  文件: AccountRepositoryImpl.java:230-233
                  SQL:  INSERT INTO accounts (apply_no, enterprise_id, account_no, operator_id, status)
                  问题: ❌ enterprise_id 来自⬆️用户输入而非📦存储值
                        ❌ operator_id 来自📦存储值但未与🔒信任锚点核对
```

#### ⑦ 攻击路径

**攻击者如何一步步利用这些漏洞：**

**前置条件：** 攻击者通过网络抓包、日志泄露、或其他接口返回，获取到企业A的申请编号（`applyNo`）和企业ID（`enterpriseId`）。

**攻击步骤：**

| 步骤 | 攻击者操作 | 篡改的参数 | 系统行为 | 问题所在 |
|------|-----------|-----------|---------|---------|
| 1 | 构造请求，填入企业A的申请编号 | `applyNo` = 企业A的值 ⬆️ | 查询数据库，找到企业A的申请记录 | ❌ 没有检查"请求人是不是企业A的人" |
| 2 | 填入企业A的企业ID | `enterpriseId` = 企业A的值 ⬆️ | 用此企业ID写入最终的开户记录 | ❌ 应该用系统存储的值，而不是用户传入的 |
| 3 | 填入自己的身份验证ID | `verifyId` = 攻击者自己的 ⬆️ | 调用验证服务，完成核身 | ❌ 没有检查"这个验证是不是企业A发起的" |
| 4 | 提交请求 | 以上3个参数组合 | 为企业A开通账户，操作人记录为企业A原始申请人 | ❌ 攻击成功 |

**攻击调用链（与正常流程对比）：**

```
正常流程：                                 攻击流程：
──────────                                ──────────
企业A用户发起申请（一阶段）                  攻击者获取企业A的申请信息
  ↓                                         ↓
企业A用户调用确认接口（二阶段）              攻击者调用确认接口
  ↓                                         ↓
系统查询 → 匹配企业A的记录     ✅           系统查询 → 匹配企业A的记录     ⚠️ 无身份校验
  ↓                                         ↓
系统核身 → 使用企业A的验证     ✅           系统核身 → 使用攻击者的验证     ⚠️ 未校验归属
  ↓                                         ↓
系统开户 → 企业A账户开通       ✅           系统开户 → 企业A账户被攻击者开通 ❌ 越权成功
```

**攻击结果：** 攻击者成功为企业A开通了账户，系统记录显示是企业A自己操作的。

#### ⑧ 根因分析与修复建议

**根本原因：**
> 系统在"确认开户"时，**只检查了"申请编号是否存在"，没有检查三件事**：
> 1. 当前操作人是不是最初的申请人（🔒信任锚点 vs 📦存储身份）
> 2. 企业ID是不是和申请记录中存储的一致（⬆️用户输入 vs 📦存储值）
> 3. 身份验证是不是由申请人本人发起的（verifyId 的归属）

**修复建议：**

| 层面 | 修复措施 | 修复位置 |
|------|---------|---------|
| **业务逻辑** | 确认操作时，验证当前操作人 == 一阶段申请人 | `AccountServiceImpl.java:189` |
| **业务逻辑** | 使用系统存储的企业ID，不接受用户重新传入 | `AccountServiceImpl.java:204` |
| **业务逻辑** | 验证 verifyId 属于当前申请人 | `AccountServiceImpl.java:193` |
| **接口设计** | 申请编号加密或签名后返回，防止被他人获取后直接使用 | `AccountServiceImpl.java:151` |
| **接口设计** | 评估是否真的需要 noLoginExchangeUid=true | `AccountServiceImpl.java:168` |
| **纵深防御** | 申请编号增加有效期（如 10 分钟）和一次性使用限制 | 新增逻辑 |

**修复代码示例：**
```java
// 修复 1：验证操作人身份
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
if (!currentUserId.equals(accountParam.getOperatorUserId())) {  // 🔒 vs 📦
    throw new BusinessException("非本人操作，拒绝执行");
}

// 修复 2：使用存储值
account.setEnterpriseId(accountParam.getEnterpriseId());  // 📦 不再使用 ⬆️ 用户输入
```

---

### 风险 2：{下一个风险标题} — {严重程度}

（同样的 ①-⑧ 模块结构）

---

## 三、风险分布总览

| 接口 | 功能说明 | 🔴 | 🟠 | 🟡 | 🟢 | 最高风险 |
|------|---------|-----|-----|-----|-----|---------|
| `POST /api/account/confirm` | 账户开通确认 | 2 | 1 | 0 | 0 | 🔴 任意企业账户可被他人开通 |
| `GET /api/order/detail` | 订单详情查询 | 0 | 1 | 0 | 0 | 🟠 可查看他人订单信息 |

---

## 四、修复优先级

| 优先级 | 风险 | 建议修复时间 | 原因 |
|--------|------|------------|------|
| P0 立即修复 | 任意企业账户可被他人开通 | 1 个工作日内 | 可直接被外部攻击者利用，影响所有企业 |
| P1 尽快修复 | 可查看他人订单信息 | 3 个工作日内 | 数据泄露风险，影响用户隐私 |

---

## 五、附录：标注说明与名词解释

**报告中使用的标注：**

| 标注 | 含义 |
|------|------|
| ⬆️ 用户可控 | 这个值来自用户请求，攻击者可以任意修改 |
| 🔒 信任锚点 | 系统用来确认"你是谁"的可信信息（如登录后的用户ID） |
| 📦 存储数据 | 系统在之前步骤中保存到数据库的信息 |
| ❌ 漏洞 | 问题代码所在位置 |
| ⚠️ 风险 | 需要注意的安全隐患 |

**安全术语：**

| 术语 | 通俗解释 |
|------|---------|
| 越权（BOLA） | 用户A能操作用户B的数据，就像你能用别人的银行卡取钱 |
| 身份冒用 | 攻击者假装是别人来操作，就像冒用他人身份证办业务 |
| 信任锚点 | 系统用来确认"你是谁"的依据，比如登录后的会话信息 |
| 参数篡改 | 攻击者修改请求中的参数值来达到非法目的 |
| 多阶段流程 | 需要分多步完成的操作（如：先申请→再确认），攻击者可能在某一步做手脚 |
| 数据流 | 一个参数从用户输入开始，经过哪些函数处理，最终到达哪里（数据库/外部服务） |
```

**report-summary.md 写作原则：**
- **双重可读性**：业务人员看 ①③⑦⑧ 理解风险，技术人员看 ④⑤⑥ 定位代码
- 代码片段保留但加**标注**（⬆️用户可控、🔒信任锚点、📦存储数据、❌漏洞），不需要理解语法也能看出问题
- 数据流用**带标注的 ASCII 图**，每一步标明 file:line 和问题所在
- 函数调用链展示**从入口到数据库的完整路径**，每个节点标注职责和问题
- 攻击路径用**对话式流程图**（攻击者 ←→ 系统），标注哪些参数被篡改
- 参数表同时展示**通俗含义**和**单独/组合风险**
- 修复建议分**业务层面**（非技术人员可推进）和**代码层面**（开发可直接改）

## Step 5 — Discovered Patterns Review (Present to User)

Review all analysis notes for auth patterns that were identified through autonomous exploration (not matched from references).

**Do NOT write directly to any reference file. Instead, present findings to the user.**

In the report, add a section:

```markdown
## Discovered Patterns & Insights (Pending User Review)

The following items were found during analysis but are not yet in the reference library.
Please review and confirm which ones should be added to the extended knowledge base.

### Pattern 1: {Pattern Name}
- **Type:** auth-pattern / datasink / trust-rule-extension / methodology-note
- **Framework/Language:** {info}
- **Search keywords:** `keyword1`, `keyword2`
- **Description:** {description}
- **Example:**
  ```{language}
  {code}
  ```
- **Source project:** {project_name}, {date}
- **Recommendation:** Add to extended knowledge / Skip / Needs further validation

### Pattern 2: ...
```

After the user reviews and approves specific entries, THEN append the approved ones to `extended-knowledge.md` (in the reference directory).

**Important:**
- Never modify existing reference files (auth-patterns-*.md, datasink-patterns.md, etc.)
- `extended-knowledge.md` is the append-only external knowledge extension
- Whether to eventually merge extended knowledge into main references is the developer's decision

## Completion Criteria

- [ ] All endpoint results aggregated
- [ ] Cross-endpoint correlation completed
- [ ] Findings sorted by priority
- [ ] report.md generated (technical report for developers/security engineers)
- [ ] report-summary.md generated (easy-read summary for non-code-audit security team)
- [ ] report.json generated (machine-readable structured data)
- [ ] Discovered patterns listed in report for user review (NOT auto-written to files)
