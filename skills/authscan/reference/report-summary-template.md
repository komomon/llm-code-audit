# report-summary.md 生成模板 — 综合安全报告 (Human-Readable)

**用途：** 生成一份**既易懂又有技术深度**的综合报告。安全运营/数据安全同学能读懂风险和攻击逻辑，开发/安全工程师能直接定位代码问题。

**生成时机：** 在 Phase 3 聚合所有 analysis.json 后，基于同一份分析数据，转换为以下格式。

**数据来源映射：**

| 报告模块 | analysis.json 字段 |
|---------|-------------------|
| ① 接口功能 / 信任锚点 | `handler.business_function` + `trust_anchors[]` |
| ② 接口定义 | `handler` + `input_params` |
| ③ 参数风险表 | `parameter_risk_list[].exploitation` + `attack_scenarios[].multi_param_interaction` |
| ④ 信任链可视化 | `trust_chain_summary.propagation_tree` |
| ⑤ 关键代码片段 | `parameter_risk_list[].flow_path[is_datasink=true]` |
| ⑥ 参数数据流追踪 | `parameter_risk_list[].flow_path` |
| ⑦ 函数调用链 | `cross_function_cache` + `flow_path` |
| ⑧ 攻击路径 | `attack_scenarios[].steps`（直接渲染，不重新推理） |
| ⑨ 根因分析与修复 | `affected_datasinks` + `trust_rule` |

---

## 报告模板

```markdown
# 越权漏洞审计报告 — {project_name/app_name}

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

**每个风险用"卡片"呈现，包含 9 个模块。非技术同学重点看模块 ①③⑧⑨，开发同学重点看模块 ④⑤⑥⑦。**

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
| **可利用性** | 高 — 只需获取有效的 applyNo 即可发起攻击 |
| **攻击复杂度** | 中 — 需要先获取目标的 applyNo（可通过日志泄露、接口返回等方式） |

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

| 参数 | 语义角色 | 通俗含义 | 适用规则 | 单独风险 | 与其他参数组合后的风险 | 严重程度 |
|------|---------|---------|---------|---------|---------------------|---------|
| `applyNo` | resource | 申请编号 — 标识哪一条申请 | R8 | 可以访问任意申请记录 | + `enterpriseId`：精确定位任意企业的申请 | 🟠 高危 |
| `enterpriseId` | identity | 企业标识 — 标识哪个企业 | R8 + R9 | 可以指定任意企业 | + `applyNo`：冒充该企业完成开户 | 🔴 严重 |
| `verifyId` | resource | 身份验证标识 — 对应一次核身验证 | R8/R6 | 可以使用自己的验证完成他人的申请 | + 以上两个：完整攻击链 | 🟠 高危 |

**系统用来确认"你是谁"的信息（🔒信任锚点）：**
- `currentUserId` — 来自 `SecurityContext.getCurrentUserId()`
- ⚠️ 但此接口标注了 `noLoginExchangeUid = true`（允许无登录态），信任锚点可能不可靠

#### ④ 信任链可视化

**直接从 `trust_chain_summary.propagation_tree` 渲染。展示🔒信任锚点与各参数的信任关系树，标出 R9 Check 结果和数据汇点（datasink）类型。**

```
🔒 信任锚点: currentUserId @ AccountServiceImpl.java:171
   状态: ⚠️ COMPROMISED（noLoginExchangeUid=true，可能降级为用户输入 — R10）
  │
  ├─✗ [🟠 高危] applyNo（resource，用户可控）
  │     → accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223
  │     ✗ R8: 查询条件中无🔒信任锚点
  │     └─→ validateMO（不可信查询结果）
  │           └─✗ [🔴 严重] operatorUserId — 未与 currentUserId 比较 → R9 Check 1 未通过
  │
  ├─✗ [🔴 严重] enterpriseId（identity，用户可控）
  │     → accountRepository.load() @ AccountRepositoryImpl.java:223 — R8
  │     → account.setEnterpriseId(request.enterpriseId) @ AccountServiceImpl.java:204
  │           └─ R9 Check 2 未通过: 系统存储值 accountParam.enterpriseId 存在但未使用
  │           ↓
  │           INSERT INTO accounts (..., enterprise_id, ...) [写入 datasink]
  │
  └─✗ [🟠 高危] verifyId（resource，用户可控）
        → verifyService.completeVerification(verifyId) @ AccountServiceImpl.java:193
        ✗ R8/R6: 外部服务调用有副作用，无锚点 [写入 datasink — side effect]
```

#### ⑤ 关键代码片段

**以下是存在问题的代码，已标注关键信息。取自 analysis.json 的 `flow_path[is_datasink=true]` 和 `affected_datasinks`。**

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

#### ⑥ 参数数据流追踪（风险传播链）

**展示每个风险参数从"用户输入"到"最终影响"的完整路径。取自 analysis.json 的 `parameter_risk_list[].flow_path` 数组，每个节点含 file:line。**

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

#### ⑦ 函数调用链

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

#### ⑧ 攻击路径（组合攻击场景）

**攻击者如何一步步利用这些漏洞。直接将 analysis.json 中 `attack_scenarios[i].steps` 翻译为中文呈现，不要重新推理。多个场景分别呈现。**

**前置条件：** {从 attack_scenarios[0].steps 中 exploited_params 为空的步骤提取，如：攻击者通过网络抓包、日志泄露、或其他接口返回，获取到企业A的申请编号（`applyNo`）和企业ID（`enterpriseId`）。}

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

#### ⑨ 根因分析与修复建议

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

（同样的 ①-⑨ 模块结构）

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

---

## 写作原则

- **双重可读性**：业务人员看 ①③⑧⑨ 理解风险，技术人员看 ④⑤⑥⑦ 定位代码
- 代码片段保留但加**标注**（⬆️用户可控、🔒信任锚点、📦存储数据、❌漏洞），不需要理解语法也能看出问题
- 数据流用**带标注的 ASCII 图**，每一步标明 file:line 和问题所在
- 函数调用链展示**从入口到数据库的完整路径**，每个节点标注职责和问题
- ⑧ 攻击路径**直接渲染 attack_scenarios 数据**，不在 Phase 3 重新推理
- 参数表同时展示**通俗含义**和**单独/组合风险**
- 修复建议分**业务层面**（非技术人员可推进）和**代码层面**（开发可直接改）
