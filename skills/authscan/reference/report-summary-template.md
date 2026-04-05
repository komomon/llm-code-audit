# report-summary.md 生成模板 — 综合安全报告 (Human-Readable)

**用途：** 生成一份既易懂又有技术深度的综合报告。安全运营/数据安全同学能读懂风险和攻击逻辑，开发/安全工程师能直接定位代码问题。

**生成时机：** 在 Phase 3 聚合所有 `analysis.json` 后，基于同一份分析数据，转换为以下格式。

**数据来源映射：**

| 报告模块 | analysis.json 字段 |
|---------|-------------------|
| ① 风险概述 + 接口定义 | `handler.business_function` + `trust_anchors[]` + `handler`（含 file/line/business_function）|
| ② 参数风险表 | `parameter_risks[].exploitation` + `.semantic_role` + `attack_scenarios[].multi_param_interaction` |
| ③ 攻击路径 | `attack_scenarios[].steps`（直接渲染，不重新推理）|
| ④ 信任链可视化 | `trust_chain_summary.propagation_tree` |
| ⑤ 参数数据流 + 漏洞代码 | `parameter_risks[].flow_path` + `parameter_risks[].affected_datasinks` |
| ⑥ 根因分析与修复 | `affected_datasinks` + `trust_rule` + `r9_analysis` |

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
| 严重 | {n} | 可被外部攻击者直接利用，影响范围大 |
| 高危 | {n} | 需要一定条件才能利用，但影响严重 |
| 中危 | {n} | 存在风险但利用难度较高或影响有限 |
| 低危 | {n} | 理论上存在风险，实际利用可能性小 |

**一句话总结：** {如："企业账户二阶段确认接口未校验操作人身份，攻击者可为任意企业开通账户。"}

---

## 二、详细风险分析

---

### 风险 1：{风险标题，如"任意企业账户可被他人开通"} — 严重

#### ① 风险概述 + 接口定义

| 维度 | 说明 |
|------|------|
| **接口标识** | RPC：`com.example.service.facade.mobile.AccountFacade.confirmAccount` / HTTP：`POST /api/account/confirm` |
| **处理函数** | `AccountServiceImpl.confirmAccount()` @ `biz/src/main/java/com/example/service/AccountServiceImpl.java:170-214` |
| **业务功能** | 企业账户开通二阶段确认，完成核身验证后正式开通账户 |
| **认证方式** | `@ServiceAnnotation(noLoginExchangeUid = true)` 注意：允许无登录态调用 |
| **信任锚点** | `currentUserId`（Token 换取的用户ID） — 注意：noLoginExchangeUid=true 时可能降级为用户输入（R10）|
| **风险类型** | 越权操作 + 身份冒用（R9）|
| **影响范围** | 所有企业的待开通申请都可能被攻击者操作 |
| **攻击条件** | 获取目标企业的 transNo/applyNo（可通过抓包、日志泄露、接口返回） |
| **可利用性** | 高 — 只需有效的 transNo 即可发起攻击 |
| **业务影响** | 严重 — 攻击者可为任意企业完成开户，可能导致资金风险和数据错乱 |

**通俗解释：**
> 这个接口就像"确认开户"的窗口。正常流程：用户先申请（拿到流水号），再来此窗口确认。但窗口没有核实来人是不是申请人本人——只要拿着别人的流水号，就能替别人完成开户。

---

#### ② 参数风险表

| 参数 | 来源 | 语义角色 | 通俗含义 | 适用规则 | 单独风险 | 与其他参数组合后的风险 | 严重程度 |
|------|------|---------|---------|---------|---------|---------------------|---------|
| `applyNo` | 用户输入 | resource | 申请流水号 — 标识哪一条申请 | R8 | 访问任意申请记录 | + `enterpriseId`：精确定位任意企业的申请 | 高危 |
| `enterpriseId` | 用户输入 | identity | 企业标识 — 标识哪个企业 | R8 + R9 | 指定任意企业 | + `applyNo`：冒充该企业完成开户，且企业ID写入数据库 | 严重 |
| `verifyId` | 用户输入 | resource | 核身验证标识 — 对应一次核身 | R8 / R6 | 用自己的验证完成他人申请 | + 以上两个：构成完整攻击链 | 高危 |

**信任锚点：** `currentUserId` 来自 `SecurityContext.getCurrentUserId()` @ `AccountServiceImpl.java:171`
注意：接口标注 `noLoginExchangeUid = true`，信任锚点在无登录态时可能不可靠（R10）

---

#### ③ 攻击路径

**直接渲染 `attack_scenarios[i].steps`，不重新推理。每个 scenario 单独呈现。**

**场景：跨企业身份冒用开户**

**前提：** 攻击者通过日志泄露或接口返回，获取到企业A的申请流水号（`applyNo`）。

| 步骤 | 攻击者操作 | 利用参数 | 系统行为 | 代码位置 |
|------|-----------|---------|---------|---------|
| 1 | 填入企业A的申请流水号 | `applyNo` = 企业A的值 | 查询数据库，找到企业A的申请记录（无身份校验） | `AccountRepositoryImpl.java:223` |
| 2 | 填入企业A的企业ID | `enterpriseId` = 企业A的值 | 以此ID写入最终开户记录 | `AccountServiceImpl.java:204` |
| 3 | 填入自己的核身验证ID | `verifyId` = 攻击者自己的 | 核身通过，完成开户 | `AccountServiceImpl.java:193` |
| **结果** | **攻击者为企业A开通账户，系统记录操作人为企业A原申请人** | | | |

**攻击结果：** 攻击者成功为任意企业完成开户，绕过所有身份校验，系统无法区分合法操作人与攻击者。

---

#### ④ 信任链可视化

**渲染自 `trust_chain_summary.propagation_tree`。标出锚点可信度、R9 双重检查结果、datasink 类型。**

```
信任锚点: currentUserId @ AccountServiceImpl.java:171
  状态: COMPROMISED（noLoginExchangeUid=true，无登录态时降级为用户输入 — R10）
  |
  |-- [高危] applyNo（resource，用户可控）
  |     -> accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223
  |     R8：查询条件无信任锚点
  |     -> validateMO（不可信查询结果）
  |           -> [严重] operatorUserId — 未与 currentUserId 比较 -> R9 Check 1 未通过
  |
  |-- [严重] enterpriseId（identity，用户可控）
  |     -> accountRepository.load() @ AccountRepositoryImpl.java:223 — R8
  |     -> account.setEnterpriseId(request.enterpriseId) @ AccountServiceImpl.java:204
  |           R9 Check 2：系统存储值 accountParam.enterpriseId 存在但未使用
  |           -> INSERT INTO accounts (..., enterprise_id, ...)   [写入 datasink]
  |
  +-- [高危] verifyId（resource，用户可控）
        -> verifyService.completeVerification(verifyId) @ AccountServiceImpl.java:193
        R8/R6：外部服务调用有不可逆副作用，无锚点约束                [写入 datasink — side effect]
```

---

#### ⑤ 参数数据流 + 漏洞代码

**每个风险参数的完整传播路径，在 datasink 节点处展示实际漏洞代码。渲染自 `flow_path` + `affected_datasinks`。**

---

**`applyNo`（resource）— 高危**

```
用户请求 request.getApplyNo()                                    [用户可控]
  |
  -> AccountServiceImpl.java:176
  |  传入 accountRepository.load(enterpriseId, applyNo)
  |
  -> AccountRepositoryImpl.java:223                              [READ datasink]
     public AccountValidateMO load(String enterpriseId[用户可控], String applyNo[用户可控]) {                                      
         String sql = "SELECT * FROM account_validate WHERE enterprise_id = ? AND apply_no = ?";
         // 漏洞：WHERE 条件无信任锚点，任何人都能查到任何记录
         return jdbcTemplate.queryForObject(sql, new Object[]{enterpriseId, applyNo}, mapper);
     }
  |
  -> AccountServiceImpl.java:203
  |  account.setApplyNo(request.getApplyNo())
  |
  -> AccountRepositoryImpl.java:230                              [WRITE datasink]
     INSERT INTO accounts (apply_no, ...)                        // 漏洞：用户控制的值写入数据库
```

---

**`enterpriseId`（identity）— 严重**

```
用户请求 request.getEnterpriseId()                               [用户可控]
  |
  |-> AccountServiceImpl.java:175
  |   传入 accountRepository.load(enterpriseId, applyNo)         // R8：无锚点（见上方查询）
  |
  +-> AccountServiceImpl.java:184（R9 触发）
      AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
      // 存储值: accountParam.getOperatorUserId() = 一阶段申请人ID
      // 漏洞：缺失 if (!currentUserId.equals(accountParam.getOperatorUserId())) throw ...
      //       R9 Check 1 未通过：当前操作人未与一阶段申请人比对
      |
      -> AccountServiceImpl.java:204
      account.setEnterpriseId(request.getEnterpriseId());        // 漏洞 R9 Check 2：使用用户输入
      // 应该用: account.setEnterpriseId(accountParam.getEnterpriseId()); // 存储值
      |
      -> AccountRepositoryImpl.java:231                          [WRITE datasink]
        INSERT INTO accounts (..., enterprise_id, ...)           // 漏洞：攻击者指定的企业ID写入
```

---

**`verifyId`（resource）— 高危**

```
用户请求 request.getVerifyId()                                   [用户可控]
  |
  -> AccountServiceImpl.java:193                                 [WRITE datasink — side effect]
     verifyService.completeVerification(request.getVerifyId())   // 漏洞 R8/R6：外部服务无锚点，已不可逆
     // 攻击者可用自己的 verifyId 完成他人申请的核身验证
```

---

#### ⑥ 根因分析与修复建议

**根本原因：**
> 二阶段接口只检查"申请记录是否存在"，缺少三项关键校验：
> 1. 当前操作人 是否等于 一阶段申请人（R9 Check 1）
> 2. 业务字段使用系统存储值，而非用户重新传入的值（R9 Check 2）
> 3. verifyId 核身验证归属于当前申请人（R8）

| 层面 | 修复措施 | 位置 |
|------|---------|------|
| 业务逻辑 | 验证当前操作人 == 一阶段申请人（R9 Check 1） | `AccountServiceImpl.java:189` |
| 业务逻辑 | 使用存储的 enterpriseId，不接受用户重新传入（R9 Check 2） | `AccountServiceImpl.java:204` |
| 业务逻辑 | 验证 verifyId 属于当前申请人（R8） | `AccountServiceImpl.java:193` |
| 接口设计 | 评估是否真的需要 `noLoginExchangeUid=true` | `AccountServiceImpl.java:168` |
| 纵深防御 | applyNo 增加有效期和一次性使用限制 | 新增逻辑 |

**修复代码：**

```java
// 修复 1：R9 Check 1 — 验证操作人身份
AccountParam accountParam = JSON.parseObject(validateMO.getSavedParam(), AccountParam.class);
if (!currentUserId.equals(accountParam.getOperatorUserId())) {
    throw new BusinessException("非本人操作，拒绝执行");
}

// 修复 2：R9 Check 2 — 使用存储值而非用户输入
// 修复前：account.setEnterpriseId(request.getEnterpriseId());
// 修复后：
account.setEnterpriseId(accountParam.getEnterpriseId());
```

---

### 风险 2：{下一个风险标题} — {严重程度}

（同样的 ①-⑥ 模块结构）

---

## 三、风险分布总览

| 接口 | 接口标识 | 严重 | 高危 | 中危 | 低危 | 最高风险 |
|------|---------|------|------|------|------|---------|
| 账户开通确认 | `com.example.AccountFacade.confirmAccount` | 2 | 1 | 0 | 0 | 任意企业账户可被他人开通 |
| 订单详情查询 | `GET /api/order/detail` | 0 | 1 | 0 | 0 | 可查看他人订单信息 |

---

## 四、修复优先级

| 优先级 | 风险 | 建议修复时间 | 原因 |
|--------|------|------------|------|
| P0 立即修复 | 任意企业账户可被他人开通 | 1 个工作日内 | 可被外部攻击者直接利用，影响所有企业 |
| P1 尽快修复 | 可查看他人订单信息 | 3 个工作日内 | 数据泄露，影响用户隐私 |

---

## 五、附录：标注说明与名词解释(最终报告不用输出)

| 标注 | 含义 |
|------|------|
| [用户可控] | 这个值来自用户请求，攻击者可以任意修改 |
| [信任锚点] | 系统用来确认"你是谁"的可信信息（如登录后的用户ID） |
| [存储值] | 系统在之前步骤中保存到数据库的信息 |
| COMPROMISED | 信任锚点本身可被用户控制，导致所有信任判断失效 |

| 术语 | 通俗解释 |
|------|---------|
| 越权（BOLA） | 用户A能操作用户B的数据，就像拿别人的银行卡取钱 |
| 身份冒用 | 攻击者假装是别人来操作，就像冒用他人身份证办业务 |
| 信任锚点 | 系统确认"你是谁"的依据，比如登录后的会话信息 |
| 多阶段流程 | 分多步完成的操作（先申请再确认），攻击者可能在某步骤做手脚 |
| 数据流 | 参数从用户输入开始，经哪些函数处理，最终到达哪里（数据库/外部服务）|
```

---

## 写作原则

- **双重可读性**：业务人员重点看 ①②③⑥，开发看 ④⑤ 定位代码
- **接口标识格式**：RPC/Dubbo 用完整类路径 `com.example.service.facade.XxxFacade.methodName`；HTTP 用 `METHOD /path/to/endpoint`；处理函数始终写实现类 `XxxServiceImpl.methodName` + 完整文件路径
- 代码片段内联在数据流追踪中（在 datasink 节点处展开漏洞代码），而非独立章节
- ③ 攻击路径直接渲染 `attack_scenarios` 数据，不在 Phase 3 重新推理攻击逻辑
- 参数表同时展示通俗含义和单独/组合风险
- 修复建议分业务层面（接口设计）和代码层面（具体修复），各有 before/after
- 参数数据流中每个节点标注 `file:line`，datasink 节点标注类型（READ/WRITE/side effect）
