# report.md 生成模板 (Human-Readable)

> **DISABLED — not currently generated.** Template preserved for future use. To re-enable, add `Write {output_dir}/report.md` to SKILL.md step 4.5.

---

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

**For EACH endpoint with risks, generate ALL 6 sections below. Do NOT skip any section or parameter.**

```markdown
### {endpoint} ({method}) — {highest_severity}

**Handler:** `{function}` @ `{file}:{line_start}-{line_end}`
**业务功能:** {本接口完成什么业务操作，一句话，例如：企业账户升级二阶段确认，完成开户流程}
**Trust Anchor:** {anchor} from `{source}` @ `{file}:{line}` | Credibility: {trusted/compromised}
{如果 compromised，另起一行：} ⚠️ Compromised Reason: {例如 noLoginExchangeUid=true 允许无登录态调用，信任锚点可能不可靠}

**影响评估:**
| 维度 | 评估 |
|------|------|
| 可利用性 | {High/Medium/Low} — {攻击者需要什么前置条件} |
| 影响范围 | {High/Medium/Low} — {受影响的用户/资源范围} |
| 业务影响 | {严重/高/中/低} — {具体业务后果} |
| 攻击复杂度 | {High/Medium/Low} — {利用难度：所需知识/权限/步骤} |

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

**CRITICAL: Render DIRECTLY from `attack_scenarios` in analysis.json. Do NOT re-infer or re-synthesize attack logic here — that was computed in Phase 2 with full code context. If analysis.json is missing attack_scenarios, go back and re-run Phase 2 for this endpoint.**

**For EACH entry in `attack_scenarios`, generate one scenario block:**

**Scenario: {attack_scenarios[i].title}** *(from `title` field)*

| Step | Attacker Action | Exploited Parameter(s) | System Behavior | Code Location |
|------|----------------|----------------------|-----------------|---------------|
| {step} | {attacker_action} | `{exploited_params}` | {system_behavior} | `{code_location}` |
| **Result** | **{impact}** | | | |

*(Repeat this table for each object in attack_scenarios array)*

**Parameter Interaction:**
{multi_param_interaction from attack_scenarios — copy verbatim, do not paraphrase}

---

#### 4. Trust Chain Visualization

**Render from `trust_chain_summary.propagation_tree` in analysis.json. Must show: anchor credibility status, R9 Check 1/2 results, datasink type (read/write) at leaf nodes.**

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

**Show the exact code lines where the vulnerability occurs. Taken from `affected_datasinks` and `flow_path` in analysis.json. User can jump directly to these locations to verify.**

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
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
// ... no identity comparison here ...
```

**Vulnerability 3 — User input replaces stored value (R9 Check 2):** `AccountServiceImpl.java:204`
```java
// ❌ Uses request.getEnterpriseId() (user input) instead of accountParam.getEnterpriseId() (stored)
account.setEnterpriseId(request.getEnterpriseId());
```

---

#### 6. Remediation

**For each vulnerability, provide before/after code:**

**Fix 1 — Add trust anchor to query:**
```java
// Before (vulnerable):
accountRepository.load(request.getEnterpriseId(), request.getApplyNo());

// After (fixed):
AccountValidateMO mo = accountRepository.loadByApplyNo(request.getApplyNo());
if (!currentUserId.equals(mo.getOperatorUserId())) {
    throw new AccessDeniedException("Not the original operator");
}
```

**Fix 2 — Verify stored identity (R9 Check 1):**
```java
// Before: no comparison
// After:
if (!currentUserId.equals(accountParam.getOperatorUserId())) {
    throw new BusinessException("非本人操作，拒绝执行");
}
```

**Fix 3 — Use stored values (R9 Check 2):**
```java
// Before: account.setEnterpriseId(request.getEnterpriseId());
// After:  account.setEnterpriseId(accountParam.getEnterpriseId());
```

---
```

(Repeat the above 6-section structure for each endpoint with findings)

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
