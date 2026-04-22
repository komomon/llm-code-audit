# multiagents_simple

This repo is now a skill-first sample for learning how to design an LLM
`main agent + subagents` project.

Study this skill:

- `skills/agent-teams-privilege-audit`

Start with:

- `skills/agent-teams-privilege-audit/SKILL.md`
- `skills/agent-teams-privilege-audit/references/architecture.md`
- `skills/agent-teams-privilege-audit/references/subagent-prompts.md`





现在这个仓库里，核心可以按两层来看：`skills/` 是“方法包”，`projects/` 是“学习型项目骨架”。

**顶层目录**

[skills](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills)  
这里放的是各种 **skill 项目**。它们更像“给大模型看的可复用工作说明书”，定义什么时候触发、主 agent 怎么拆任务、subagent 怎么分工、输出格式是什么、怎么裁决。

[projects](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/projects)  
这里放的是 **学习型项目脚手架**。它们更像“一个最小项目雏形”，用目录、prompt、sample artifacts、输出模板来教你怎么把 skill 真正组织成项目。

---

**`skills/` 下面每个目录的作用**

[agent-teams-privilege-audit](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills/agent-teams-privilege-audit)  
这是最早的“agent teams 概念型 skill”。  
它的作用是教你：

- 什么是 `main agent + subagents`
- 什么是更泛化的 `agent teams`
- 主 agent 负责什么
- subagent 怎么拆
- 团队结构和 prompt 大概怎么写

它偏“入门理解”和“抽象方法”。

[code-vuln-agent-teams-template](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills/code-vuln-agent-teams-template)  
这是 **通用代码漏洞审计母版**。  
它不绑定某个具体漏洞，作用是给你一个总模板：

- 通用 agent team 架构
- 通用 workflow
- 通用 agent contract
- 通用 output schema
- 通用 prompt 模板
- 通用 checklist 入口

你以后做注入、SSRF、越权、业务逻辑漏洞，都可以从它改。

[broken-access-control-agent-team](D:/ccode/aicode\aicode002-claudecode\multiagents_simple/skills/broken-access-control-agent-team)  
这是 **越权/BAC 专项 skill**。  
它适合审计：

- 水平越权
- 垂直越权
- 跨租户
- 缺失 ownership check
- 缺失 server-side authz
- 审批流权限绕过

它比通用模板更专，已经把这些内容都落好了：

- BAC 专用团队结构
- BAC checklist
- BAC finding rubric
- BAC dispatch 示例
- BAC execution demo
- BAC subagent 输出样例
- BAC 主 agent 决策规则和操作手册

[idor-agent-team](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills/idor-agent-team)  
这是 **IDOR / 对象级授权专项 skill**，也是目前最细粒度的一套。  
它的核心作用是解决你提到的那个问题：**模型上下文有限时，要把越权进一步拆小**。

它默认把审计拆成这些 lane：

- `input-parameter-agent`
- `auth-context-agent`
- `call-chain-agent`
- `input-auth-relation-agent`
- `output-auth-relation-agent`
- 再往后是 hypothesis / evidence / judge / reporter

这个 skill 适合专门审：

- 路由参数 ID 控制对象访问
- 对象读取/修改是否真正绑定当前用户
- 返回对象是否真的属于当前身份
- 更新/删除是否只是“登录了就行”

如果你以后重点做 IDOR，这个是最值得直接扩展的。

---

**`projects/` 下面每个目录的作用**

[bac-agent-team-learning-scaffold](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/projects/bac-agent-team-learning-scaffold)  
这是 **BAC 学习型项目脚手架**。  
它的作用不是提供一个大而全的框架，而是给你一个“项目应该怎么摆”的可模仿样子：

- `prompts/` 放各 agent 提示词
- `workflow/` 放流程说明
- `tasks/` 放用户请求和主 agent 计划模板
- `sample_artifacts/` 放样例代码
- `outputs/` 放预期输出样例

它适合用来学“越权专项项目该怎么组织”。

[idor-agent-team-learning-scaffold](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/projects/idor-agent-team-learning-scaffold)  
这是 **IDOR 学习型项目脚手架**，而且现在已经升级成了 **可运行的最小 orchestrator 骨架**。

它除了 `prompts/`、`workflow/`、`tasks/`、`sample_artifacts/`、`outputs/` 之外，还多了：

- [run_demo.py](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/projects/idor-agent-team-learning-scaffold/run_demo.py)
- [src/idor_scaffold](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/projects/idor-agent-team-learning-scaffold/src/idor_scaffold)

它的作用是让你不仅能看“方法”，还能直接看：

- 一个最小 orchestrator 怎么组织
- 各 lane 怎么顺序执行
- 怎么加载 sample artifacts
- 怎么产出 agent trace 和 final report

这是目前最接近“可继续开发成真实项目”的目录。

---

**每个 skill/project 内部常见子目录作用**

以 skill 为例：

`SKILL.md`  
核心入口。定义 skill 什么时候用、主流程是什么、团队怎么拆。

`agents/openai.yaml`  
skill 的元信息，相当于 skill 名片。

`references/`  
详细说明书。这里一般放：

- 架构
- workflow
- agent contract
- output schema
- checklist
- prompt 模板
- dispatch 示例
- execution demo
- playbook / decision rules

以 scaffold 为例：

`prompts/`  
每个 agent 的 prompt 文件。

`workflow/`  
流程文档，比如生命周期、merge 规则。

`tasks/`  
用户请求示例、主 agent 计划模板。

`sample_artifacts/`  
被审计的样例代码。

`outputs/`  
预期中间输出和最终报告样例。

`src/`  
只有 runnable scaffold 才会有，放最小 orchestrator 代码。

---

**如果你现在要按学习顺序看，我建议这样**

1. 先看通用母版  
[code-vuln-agent-teams-template](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills/code-vuln-agent-teams-template)

2. 再看 BAC 专项  
[broken-access-control-agent-team](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills/broken-access-control-agent-team)

3. 再看 IDOR 细粒度专项  
[idor-agent-team](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/skills/idor-agent-team)

4. 最后看可运行脚手架  
[idor-agent-team-learning-scaffold](D:/ccode/aicode/aicode002-claudecode/multiagents_simple/projects/idor-agent-team-learning-scaffold)

如果你愿意，我下一条可以继续给你画一个“这整个仓库的地图图”，把 `skills/` 和 `projects/` 的关系用一张结构图画出来。