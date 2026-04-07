# AuthScan 架构指南

> 写给未来维护者/模型的说明文档。在用任何模型调整此项目之前，请先阅读本文件。

---

## 零、文档状态说明

| 文件 | 状态 | 说明 |
|------|------|------|
| 本文件 `docs/ARCHITECTURE-GUIDE.md` | ✅ 最新 | 以本文件为准 |
| `docs/2026-04-05-authscan-design.md` | ⚠️ 部分过时 | 架构思路仍有参考价值，但以下内容已过时：① 仅列 R1-R8（实际 R1-R10）② analysis.json schema 是旧版（缺 exploitation/attack_scenarios/business_function）③ 输出路径格式为 `results/{project_name}/`（实际为 `results/yyyyMMddHHmm_{project_name}/`）④ Phase 3 输出列的是 report.md（现已禁用，改为 report-summary.md） |
| `skills/authscan/SKILL.md` | ✅ 最新 | 执行入口，始终以此为准 |

---

## 一、项目的本质

AuthScan 是一个**让模型执行越权漏洞挖掘的方法论载体**，不是传统的规则扫描器。

核心设计哲学：
- **方法论 > 规则列表**：教模型"如何思考"，而不是"匹配什么关键词"
- **按需加载**：SKILL.md 是入口，reference/ 文件在执行特定阶段时才加载
- **语义理解 > 模式匹配**：依赖 LLM 的语义能力跨越语言边界，规则文件是辅助而非替代

---

## 二、文件职责地图

```
SKILL.md                          ← 总指挥。每次调用必读。包含：核心定义、执行 checklist、
                                    Key References 索引。不要在这里放大量内容。

reference/
├── recon.md                      ← Phase 1 方法论（扫描阶段），Phase 1 step 2 加载
├── endpoint-analysis.md          ← Phase 2 方法论（分析阶段），Phase 2 step 3 加载 ★
├── trust-propagation-rules.md    ← R1-R10 信任规则，Phase 2 step 3.0 加载（必读）
├── output-analysis.md            ← Layer 2 输出分析详细方法论，Phase 2 step 3.3 按需加载
├── datasink-patterns.md          ← 数据操作模式，Phase 2 step 3.0 加载
├── mass-assignment-patterns.md   ← 批量赋值模式，Phase 2 step 3.4（Layer 3）按需加载
│
├── auth-patterns-java.md         ← Java 框架认证模式，Phase 1 step 2.2 按语言加载
├── auth-patterns-python.md       ← Python 框架认证模式，Phase 1 step 2.2 按语言加载
├── auth-patterns-nodejs.md       ← Node.js 框架认证模式，Phase 1 step 2.2 按语言加载
├── auth-patterns-common.md       ← 跨语言模式 JWT/OAuth2/RBAC，已知模式均不匹配时加载
│
├── report.md                     ← Phase 3 聚合方法论 + report.json schema，Phase 3 加载
├── report-summary-template.md    ← 中文综合报告模板（9模块），Phase 3 step 4.5 显式加载
├── report-template.md            ← 英文技术报告模板（当前禁用，不在 Key References 中）
│
└── extended-knowledge.md         ← 运行时发现的新模式（用户确认后追加，禁止自动写入）
                                    Phase 1 step 2.2 / Phase 2 step 3.0 随主参考文件加载
```

**加载时机汇总：**

| 文件 | 何时加载 |
|------|---------|
| `trust-propagation-rules.md` | Phase 2 每个端点分析前（step 3.0，强制） |
| `datasink-patterns.md` | Phase 2 每个端点分析前（step 3.0，强制） |
| `output-analysis.md` | Phase 2 Layer 2 时（step 3.3，按需） |
| `mass-assignment-patterns.md` | Phase 2 Layer 3 时（step 3.4，写操作才触发） |
| `report-summary-template.md` | Phase 3 step 4.5 生成报告前（强制，需显式 read） |
| `extended-knowledge.md` | 随认证模式/分析参考一起加载 |
| `report-template.md` | 当前禁用，不加载 |

---

## 三、稳定核心（不建议修改）

以下是整个项目的骨架，修改会破坏分析一致性：

### 3.1 信任链分析范式（SKILL.md Principle 1 & 2）

```
越权漏洞 = 用户可控参数 在未与认证锚点建立信任关系的情况下 到达数据操作
```

这个定义是所有分析的出发点。**不要修改措辞**，否则模型会产生不一致的判断。

Per-Endpoint Independence Principle（独立端点原则）同样不可动：每个端点必须假设攻击者直接独立调用，不能因为另一个端点有鉴权就认为数据"安全"。

### 3.2 R1-R10 信任规则（trust-propagation-rules.md）

10 条规则是分析引擎的核心。以下表格来自实际文件，如有疑问以 `trust-propagation-rules.md` 为准：

| 规则 | 名称 | 含义 | 结果 |
|------|------|------|------|
| R1 | Direct Association | 用户参数与锚点在**同一约束**中（`WHERE a=x AND userId=anchor`）| trusted |
| R2 | Derived Trust | 来自受锚点约束查询的结果，其**所有字段**均受信任 | trusted |
| R3 | Transitive Trust | 基于已受信任数据（R1/R2/R3结果）的操作，结果也受信任 | trusted |
| R4 | Conditional Guard | `if(param != anchor) throw/return` → 守卫通过后的分支受信任 | trusted（守卫通过分支） |
| R5 | Post-Auth Read | 读操作使用未受信任参数，但结果**在返回前**经锚点过滤 | trusted（事后追溯） |
| R6 | Post-Auth Write | **写操作**在锚点验证之前执行，写操作已不可逆 | at_risk (Risk Pending) |
| R7 | Transform Neutral | toString/split/parseInt 等变换**不改变**信任状态 | 不变 |
| R8 | No Association | 整个数据流中**无任何**锚点关联 | at_risk ← 最常见的 BOLA 根因 |
| R9 | Stored Identity Re-validation | DB 结果含身份字段（operatorUserId/ownerId），必须与当前锚点显式比对 | 触发双重检查 |
| R10 | Trust Anchor Credibility | 锚点本身可被用户控制（noLogin/fallback/灰度开关），所有信任结论失效 | 全部降级为 at_risk |

**规则间依赖不可打破**：R9 的分析前提是 R8 已确认有数据操作；R10 是对整个信任链的元判断，R10 触发则 R1-R9 的结论全部无效。

**R5 vs R6 的对称性**：这是最容易混淆的一对。读操作可以事后过滤（数据还没给用户），写操作不行（副作用已发生）。

### 3.3 analysis.json schema（Phase 2 → Phase 3 的接口契约）

这是最重要的接口定义。完整字段：

```
endpoint                          ← API 路径
method                            ← HTTP method
handler
  .function                       ← ClassName.methodName
  .file                           ← 完整相对路径（从项目根目录）
  .line_start / .line_end
  .business_function              ← 接口业务功能（一句话，Phase 2 分析时填写）

endpoint_level_risks[]            ← Layer 0 BFLA/unauthorized access 发现
  .type / .detail / .severity / .location

trust_anchors[]                   ← 信任锚点列表
  .name / .source / .file / .line
  .credibility                    ← "trusted" | "compromised"
  .credibility_reason             ← 若 compromised 的原因（R10）

parameter_risks[]                 ← Layer 1 每参数分析结果（核心字段）
  .param / .semantic_role         ← identity/resource/filter/action
  .trust_status                   ← trusted/at_risk/risk_pending/anchor
  .trust_rule / .severity
  .reason                         ← 技术链路描述
  .exploitation                   ← 攻击者视角："攻击者能做什么"（具体操作，非泛泛）
  .flow_path[]                    ← 逐步代码路径（每步含 file:line）
  .datasink                       ← 最终数据操作位置
  .affected_datasinks[]           ← 所有受影响的数据操作

r9_analysis                       ← 若触发 R9
  .triggered / .stored_identity_fields
  .check1_identity_comparison     ← currentUserId == storedIdentity？
  .check2_stored_value_usage      ← 是否使用存储值而非用户输入？

combination_risks[]               ← 多参数组合风险
attack_scenarios[]                ← 完整攻击步骤（★ Phase 2 时生成，Phase 3 直接渲染）
  .title / .severity / .involved_params
  .steps[].attacker_action        ← 具体 API 调用/参数值，不能写"攻击者操纵参数X"
  .steps[].system_behavior        ← 实际执行的代码路径/SQL
  .steps[].code_location
  .impact / .root_cause / .multi_param_interaction

output_risk_list[]                ← Layer 2 输出字段分析
  .field / .trust_status / .source_chain[] / .trust_rule / .severity

mass_assignment_risks[]           ← Layer 3 批量赋值风险

trust_chain_summary               ← 信任链可视化数据
  .anchors / .trusted_params / .at_risk_params / .risk_free_params
  .propagation_tree               ← ASCII 信任链树结构的数据来源

functions_analyzed[]              ← 所有分析过的函数（含 datasink 角色标注）
```

**为什么 `attack_scenarios` 必须在 Phase 2 生成**：Phase 3 不读源码，只聚合 JSON。如果攻击场景留到 Phase 3 生成，则只能从 `reason` 字符串推理，输出空洞抽象。Phase 2 时代码在上下文中，生成的 `steps` 含具体行号和 SQL，Phase 3 直接渲染即可。这是防止攻击场景退化的核心修复。

### 3.4 三阶段执行顺序与边界

```
Phase 1 (recon) → 输出 recon_context.md
Phase 2 (per-endpoint, 循环每个端点) → 输出 {output_dir}/{endpoint_slug}/analysis.json
Phase 3 (aggregate) → 输出 report-summary.md + report.json
```

**阶段边界不可打破**：
- Phase 3 不能重新读源码推理漏洞，只能从 analysis.json 渲染
- Phase 2 不能假设其他端点的分析结果，每个端点独立分析
- Phase 1 结果（recon_context.md）作为 Phase 2 的背景，不替代 Phase 2 的逐参数分析

---

## 四、扩展点（推荐按此方式扩展）

```
新语言   → 新建 auth-patterns-{language}.md，按附录 A 模板写
新例子   → endpoint-analysis.md 末尾追加，按附录 B 模板写，attack_scenarios 必填
改任何文件 → 对照第五节的级联依赖表检查是否有其他文件需要同步
```

### 4.1 添加新语言支持

创建 `reference/auth-patterns-{language}.md`，同时在 SKILL.md Phase 1 步骤 2.2 的加载指令中按条件加载：

```markdown
- [ ] 2.2 Load `reference/auth-patterns-{language}.md` (java/python/nodejs/go/...) + ...
```

文件结构见 **附录 A：新语言认证模式模板**。

### 4.2 添加新的 Worked Example

在 `endpoint-analysis.md` 末尾追加，结构见 **附录 B：Worked Example 模板**。

**选例原则：**
- 每个例子应展示一种新的漏洞模式组合（不要重复已有例子的核心机制）
- 优先覆盖真实业务场景（二阶段操作、批量操作、跨实体关联）
- 必须包含 `attack_scenarios` 的完整 JSON（这是对模型最有指导价值的部分）

**现有例子覆盖范围：**

| Example | 语言/框架 | 核心机制 | 主要规则 |
|---------|-----------|----------|----------|
| 1 | Java | 简单 BOLA（单参数 orderId）| R8 |
| 2 | Java | 复杂 BOLA（二阶段 applyNo+enterpriseId）| R8+R9 |
| 3 | Python/Django | BOLA + 输出泄漏 | R8+R2+Output Layer |
| 4 | Java Spring | BFLA + BOLA（垂直+水平越权组合）| Layer0+R8 |
| 5 | Node.js Express+JWT | 简单 BOLA + PII 泄漏 | R8+Output Layer |

**尚未覆盖的有价值场景（供参考）：**
- 批量操作（`POST /api/batch` 含 ids 数组，R8 per-item）
- 间接关联（通过 JOIN 到锚点相关表，R4）
- 多租户隔离缺失（tenantId 未绑定锚点）
- 文件访问越权（路径构造含用户输入）

### 4.3 更新 extended-knowledge.md

运行时发现的新模式，**必须经用户确认后才能写入**。不要修改其他任何 reference 文件。

```markdown
### {Framework} — {Pattern Name}
- **Type:** auth-pattern / datasink / trust-rule-extension / methodology-note
- **Framework/Language:** {info}
- **Search keywords:** `keyword1`, `keyword2`
- **Description:** {一句话}
- **Example:**
  ```{lang}
  {code}
  ```
- **Confirmed:** {date}, project: {project_name}
```

---

## 五、需要同步修改的地方（级联依赖表）

以下几处有**级联依赖**，改一处必须检查其他处：

| 改动 | 必须同步检查 |
|------|------------|
| 修改 analysis.json schema（增删字段）| `reference/report.md` schema 定义、`reference/report-summary-template.md` 数据来源表、`reference/endpoint-analysis.md` Worked Examples 中的 JSON 示例、`reference/report-template.md`（如需启用） |
| 增加输出文件（新的 Phase 3 报告）| `SKILL.md` step 4.5、`reference/report.md` Completion Criteria |
| 新增 reference 文件 | `SKILL.md` Key References（★ 凡是需要模型按需加载的文件，必须在 Key References 中注册）、使用该文件的 phase 的加载指令 |
| 修改输出目录格式 | `SKILL.md` step 1、`reference/recon.md` Completion Criteria、`reference/report.md` Step 1、所有 `{output_dir}` 引用 |
| 增/改 Worked Example 的 JSON 结构 | 确认与 `reference/report.md` schema 中对应字段一致 |
| 修改 Phase 阶段数量或顺序 | `SKILL.md` checklist、设计文档、所有 reference 文件的 Prerequisites |

---

## 附录 A：新语言认证模式模板

文件名：`reference/auth-patterns-{language}.md`

```markdown
# {Language} Auth Patterns

**Priority order:** Check patterns top-to-bottom. Stop when matched.

## Priority 1 — {Framework Name} (最主流框架)

**Characteristic:** {框架的认证特征，一句话}

**Search keywords:** `keyword1`, `keyword2`, `keyword3`

### Global Auth Mechanism

```{lang}
// 典型的全局认证配置代码（interceptor/middleware/filter）
// 注意标出：覆盖范围、白名单路径、锚点获取方式
```

**Scope:** {哪些路径被覆盖，哪些路径被排除}
**Strength:** login-only / role-check / permission-check / custom
**Trust anchor source:** `{function_or_object.field}` — returns `{what}`, obtained via `{how}`

### Endpoint-Level Auth Declarations

| Pattern | Meaning | Example |
|---------|---------|---------|
| `@Annotation` / decorator | {含义} | `@Annotation("ROLE_X")` |

### In-Function Auth Patterns

```{lang}
// 典型的函数内认证检查代码
// if (!currentUser.hasPermission(...)) throw ...
```

---

## Priority 2 — {Second Framework}

{同上结构}

---

## Trust Anchor Quick Reference

| Source | Code Pattern | Credibility | Notes |
|--------|-------------|-------------|-------|
| {来源类型} | `{获取代码}` | trusted / needs-check | {注意事项，特别关注 noLogin/fallback/toggle 模式} |

---

## Known Whitelist / Anonymous Access Patterns

{列举该语言/框架中常见的"跳过认证"注解/装饰器/配置}

- `@Anonymous` — {含义}
- `permitAll()` path: `{典型路径模式}`
```

---

## 附录 B：Worked Example 模板

在 `endpoint-analysis.md` 末尾追加（在最后一个 `---` 分隔符之后）：

````markdown
---

## Worked Example {N}: {场景名称} ({语言/框架} — {漏洞类型})

**Scenario:** {一句话描述业务场景}
**Key teaching point:** {这个例子要教会模型什么判断，与已有例子的差异}
**Vulnerability type:** {BOLA / BFLA / Mass Assignment / BOLA+BFLA / ...}
**Primary rules:** {R8 / R8+R9 / Layer0+R8 / ...}

### Code

```{lang}
// 文件 1：认证中间件/框架配置
// 标出：① trust anchor 从哪里获取 ② 覆盖哪些路径 ③ 是否有白名单
{auth_setup_code}
```

```{lang}
// 文件 2：Controller/Handler
// 标出：① 入参（全部） ② trust anchor 获取 ③ datasink 调用点
{handler_code}
```

```{lang}
// 文件 3：Service/DAO/Model（如有）
// 标出：实际的数据操作（datasink），含参数传入方式
{datasink_code}
```

### Analysis

**Layer 0 — Endpoint-Level Auth Check**

- Global auth: {covered / not covered，说明原因}
- Endpoint auth: {有无注解/装饰器，写明声明的权限级别}
- Auth sufficiency assessment: {PASS / FAIL — 如 FAIL：说明接口语义要求何种权限，实际只有何种检查 → BFLA}
- `endpoint_level_risks`: `[{type, severity, reason}]` 或 `[]`

**Layer 0.5 — Trust Anchor Credibility**

- Anchor: `{variable_name}` from `{source_expression}` @ `{file}:{line}`
- Source type: server-session / JWT-verified / framework-injection / internal-sdk
- Credibility patterns to check: noLogin annotation? fallback to user input? gray toggle?
- **Verdict: ✅ TRUSTED** / **⚠️ COMPROMISED** ({原因，触发 R10})

**Layer 1 — Parameter Analysis**

`[GATE]` Parameter table（先列全，再分析，数量必须与函数签名一致）：

| Parameter | Source | Semantic Role | Trust Status | Rule | Severity |
|-----------|--------|---------------|-------------|------|----------|
| `{param}` | RequestBody/PathVar/QueryParam/... | identity/resource/filter/action | trusted/at_risk/anchor | R{n} | CRITICAL/HIGH/MEDIUM/LOW |

**Per-Parameter Trace（仅 at_risk/risk_pending 参数需要完整 trace）：**

`{param}` ({semantic_role}) — {severity}:
```
{param} @ {file}:{line}  [user-controlled]
  │
  ↓ @ {file}:{line}
  {function_call}({param}, ...)
  ✗ {violation description}：{R{n} — rule name}
  │
  ↓ @ {file}:{line}
  {datasink_operation}({param})   [DATASINK — {read/write}]
  ✗ {最终违规：具体 SQL 或操作，无锚点约束}
```

{若触发 R9：}

**R9 Analysis:**
- DB result contains identity fields: `{field_names}`
- Check 1 (currentUser == storedIdentity?): PASS / FAIL — {reason}
- Check 2 (uses stored value, not user input?): PASS / FAIL — {reason}

**Layer 2 — Output Analysis（若有信息泄漏）:**

| Return Field | Source | Trust Status | Severity |
|-------------|--------|-------------|---------|
| `{field}` | from untrusted query / trusted query / user input echo | at_risk / safe | HIGH/MEDIUM |

**Trust Chain Visualization:**

```
Trust Anchor: {anchor} @ {file}:{line}
  Status: ✅ TRUSTED / ⚠️ COMPROMISED ({reason})
  │
  ├─✗ [{severity}] {param} ({semantic_role})
  │     → {datasink_call} @ {file}:{line}
  │     → {violation} → {Rule}
  │         {若有 R9：}
  │         DB result.{identity_field} — NOT compared with anchor → R9 Check 1 FAIL
  │
  └─✗ [{severity}] {param2} ({semantic_role})
        → ...（或 ✅ trusted，注明原因）
```

**`attack_scenarios` for analysis.json（必填，★ Phase 2 时生成）：**

```json
"attack_scenarios": [
  {
    "title": "{具体攻击目标，如 'Read any user order via orderId enumeration'}",
    "severity": "CRITICAL/HIGH/MEDIUM",
    "involved_params": ["{param1}", "{param2}"],
    "steps": [
      {
        "step": 1,
        "attacker_action": "{具体 API 请求，含参数名和示例值，如 'Send GET /api/orders/1001 where 1001 belongs to victim'}",
        "exploited_params": ["{param}"],
        "system_behavior": "{实际执行的代码路径/SQL，如 'Order.findById(1001) returns victim order'}",
        "code_location": "{file}:{line}"
      },
      {
        "step": 2,
        "attacker_action": "{下一步攻击动作}",
        "exploited_params": ["{param}"],
        "system_behavior": "{系统行为}",
        "code_location": "{file}:{line}"
      }
    ],
    "impact": "{攻击成功的实际影响，具体到数据/操作类型}",
    "root_cause": "{根本原因，引用具体规则，如 'orderId reaches datasink without anchor binding (R8)'}",
    "multi_param_interaction": "{多参数如何组合 / 或 'Single parameter — {param} alone is sufficient'}"
  }
]
```

**Fix:**

```{lang}
// Before (vulnerable):
{vulnerable_code}

// After (fixed):
{fixed_code}
// Fix principle: {说明应用了哪条规则修复，如 R1: 在查询中加入锚点约束}
```

**Why this example matters:** {这个例子新增了什么分析能力，与已有 5 个例子的差异在哪里}
````

---

## 附录 C：给调整本项目的模型的提示

> 如果你（模型）被要求修改此项目，请先阅读本节。

**读文件的顺序：**
1. 本文件（`docs/ARCHITECTURE-GUIDE.md`）
2. `skills/authscan/SKILL.md`
3. 你要修改的具体文件

**修改前必问自己：**

1. 这个修改是否破坏了三阶段边界？（Phase 2 不应读报告模板，Phase 3 不应重新分析代码）
2. 这个修改是否影响 analysis.json schema？（是 → 同步修改所有依赖它的文件，见第五节）
3. 这个新文件是否需要在 SKILL.md 的 Key References 中注册？（是 → 同时更新 SKILL.md step 2.2 或 3.0 的加载指令）
4. 这个修改是否只改了一个文件但逻辑要求另一个文件也要改？（见第五节级联依赖表）
5. 是否在 R1-R10 表述上做了修改？（不要 — 规则措辞的一致性是分析可重复性的基础）

**严禁操作：**
- 在 SKILL.md 中堆大量内容（SKILL.md 应保持轻量，细节放 reference/）
- 修改 `trust-propagation-rules.md` 中 R1-R10 的判断逻辑
- 让 Phase 3 重新从源码推理攻击场景（必须从 attack_scenarios 渲染）
- 在未经用户确认的情况下写入 `extended-knowledge.md`
- 合并或删除现有的 Worked Examples（只追加，不修改已有例子）
- 把 `report-template.md` 加入 SKILL.md Key References（它是禁用的英文模板，不应被自动加载）
