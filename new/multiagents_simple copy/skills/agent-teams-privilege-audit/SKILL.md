---
name: agent-teams-privilege-audit
description: Use this skill when the user wants a skill-first LLM project built around a main agent coordinating subagents or agent teams for privilege-escalation audits, prompt-security reviews, tool-risk analysis, or other evidence-driven multi-agent workflows.
---

# Agent Teams Privilege Audit

Use this skill when the goal is to build or teach a real `main agent +
subagents` workflow, not a generic code demo.

## What the skill should teach

This skill is for learning how to design an LLM project where:

- the main agent owns planning and synthesis
- subagents own narrow specialist lanes
- the team returns evidence before final conclusions
- the final answer is written only after merge and review

## Main agent responsibilities

The main agent is the orchestrator.

It should own:

1. understand the user goal
2. define success criteria
3. decide whether delegation is useful
4. split work into bounded subagent tasks
5. merge outputs
6. resolve contradictions
7. produce the final answer

The main agent should not dump all specialist work to subagents and disappear.

## Default subagent team

For privilege-escalation or tool-abuse audits, use this team by default:

1. `recon-subagent`
2. `threat-model-subagent`
3. `policy-subagent`
4. `evidence-subagent`

### Ownership

- `recon-subagent`: inventory the system, tools, auth flow, and trust boundaries
- `threat-model-subagent`: enumerate abuse paths and privilege-escalation paths
- `policy-subagent`: compare observed behavior against written rules or policy
- `evidence-subagent`: deduplicate and normalize evidence from the other subagents

The main agent still owns the final prioritization and final user-facing output.

## Delegation rules

- Delegate only independent, bounded tasks.
- Do not delegate the same exact question to multiple subagents unless the
  comparison is intentional.
- Do not let subagents write the final answer.
- Do not let the reporter invent new risks.

## Output contract for subagents

Ask each subagent to return compact structured sections:

- `scope`
- `facts`
- `risks`
- `evidence`
- `confidence`
- `open_questions`

The main agent should merge these into:

1. confirmed facts
2. candidate findings
3. final findings

## Suggested project shape

Keep the skill project small and reusable:

- `SKILL.md`
- `agents/openai.yaml`
- `references/architecture.md`
- `references/subagent-prompts.md`
- `references/example-flows.md`

Only add scripts if the skill really needs deterministic tooling.

## How to use references

- Read `references/architecture.md` when teaching or designing team structure.
- Read `references/subagent-prompts.md` when drafting the main-agent and
  subagent prompts.
- Read `references/example-flows.md` when you want concrete task patterns.
