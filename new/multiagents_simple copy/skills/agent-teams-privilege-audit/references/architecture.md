# Architecture

This reference explains how to structure an LLM skill project around a `main
agent + subagents` model.

## 1. Make the main agent the control plane

The main agent should own:

- user intent parsing
- planning
- delegation
- synthesis
- conflict resolution
- final answer generation

This is the difference between a true main agent and a loose collection of
parallel workers.

## 2. Split subagents by question

Bad split:

- `big-model-agent`
- `small-model-agent`
- `backup-agent`

Good split:

- `recon-subagent`
- `threat-model-subagent`
- `policy-subagent`
- `evidence-subagent`

The role should describe ownership, not model size.

## 3. Keep merge logic centralized

Subagents should return analysis artifacts.

The main agent should merge those artifacts into:

1. facts
2. candidate findings
3. accepted final findings

This keeps the final answer auditable.

## 4. Prefer skill-first when teaching

If the learning goal is "how do I build an agent team", a skill project is more
useful than a code-heavy demo because it exposes the reusable parts directly:

- trigger condition
- team topology
- delegation rules
- prompt contracts
- merge pattern

## 5. Add framework code later

Only after the workflow is stable should you add implementation details such as:

- SDK transport
- retries
- tracing
- persistence
- evaluation harnesses
