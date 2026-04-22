# IDOR Agent Team Learning Scaffold

This directory is a learning-oriented scaffold for building a fine-grained IDOR
code-audit workflow around a `main agent + subagents` team.

It now includes a **minimal runnable orchestrator skeleton** that reads the
sample artifacts, applies the fine-grained review lanes, and prints a demo
trace plus final report.

It is still intentionally lightweight. The goal is to show how to package:

- role prompts
- workflow notes
- sample artifacts
- review tasks
- expected outputs

Use it when you want a project shape you can extend into a real IDOR review
system.

## Layout

```text
projects/idor-agent-team-learning-scaffold/
|-- README.md
|-- pyproject.toml
|-- run_demo.py
|-- prompts/
|   |-- main-agent.md
|   |-- scope-agent.md
|   |-- input-parameter-agent.md
|   |-- auth-context-agent.md
|   |-- call-chain-agent.md
|   |-- input-auth-relation-agent.md
|   |-- output-auth-relation-agent.md
|   |-- idor-hypothesis-agent.md
|   |-- evidence-agent.md
|   |-- judge-agent.md
|   `-- reporter-agent.md
|-- workflow/
|   |-- review-lifecycle.md
|   `-- merge-rules.md
|-- tasks/
|   |-- user-request.md
|   `-- review-plan-template.md
|-- sample_artifacts/
|   |-- routes.py
|   |-- controllers/
|   |   `-- order.py
|   |-- services/
|   |   `-- order_service.py
|   |-- repositories/
|   |   `-- order_repo.py
|   `-- serializers/
|       `-- order_serializer.py
|-- src/
|   `-- idor_scaffold/
|       |-- __init__.py
|       |-- loader.py
|       |-- models.py
|       `-- orchestrator.py
`-- outputs/
    |-- expected-subagent-shapes.md
    `-- sample-final-report.md
```

## Run the demo

From this directory:

```bash
python run_demo.py
```

What it does:

1. reads `tasks/user-request.md`
2. loads the prompt files and sample artifacts
3. runs a minimal deterministic orchestrator across the fine-grained IDOR lanes
4. prints an agent trace and final report

## How to use this scaffold

1. Run `python run_demo.py` once to understand the end-to-end shape.
2. Replace the sample artifacts with your real path or representative excerpts.
3. Keep the prompt files lane-specific and compact.
4. Use the workflow notes to preserve the fine-grained IDOR sequence.
5. Use the tasks folder to store user requests and main-agent plans.
6. Use the outputs folder to define what good intermediate and final outputs look like.

## What is intentionally minimal

This scaffold does not yet include:

- a real model API client
- subagent process spawning
- structured output validation
- retries
- tracing persistence
- evaluation harnesses

Those should be added after the lane structure and merge discipline are stable.

## Relationship to the skill

This scaffold complements:

- `skills/idor-agent-team`

The skill describes the reusable method. This scaffold shows how that method
can be organized as a learning project.
