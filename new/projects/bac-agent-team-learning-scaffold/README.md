# BAC Agent Team Learning Scaffold

This directory is a learning-oriented project scaffold for building a
broken-access-control code-audit workflow around a `main agent + subagents`
team.

It is not a runnable framework implementation. It is a study scaffold that
shows how to package:

- prompts
- workflow notes
- sample artifacts
- review tasks
- expected outputs

Use it when you want a repo shape you can extend into a real project.

## Layout

```text
projects/bac-agent-team-learning-scaffold/
├── README.md
├── prompts/
│   ├── main-agent.md
│   ├── scope-agent.md
│   ├── authz-mapper-agent.md
│   ├── code-path-agent.md
│   ├── access-control-hypothesis-agent.md
│   ├── evidence-agent.md
│   ├── judge-agent.md
│   └── reporter-agent.md
├── workflow/
│   ├── review-lifecycle.md
│   └── merge-rules.md
├── tasks/
│   ├── user-request.md
│   └── review-plan-template.md
├── sample_artifacts/
│   ├── routes.py
│   ├── controllers/
│   │   └── order.py
│   ├── services/
│   │   └── order_service.py
│   └── repositories/
│       └── order_repo.py
└── outputs/
    ├── expected-subagent-shapes.md
    └── sample-final-report.md
```

## How to use this scaffold

1. Replace the sample artifacts with your real code or representative excerpts.
2. Keep the prompt files role-specific and compact.
3. Use the workflow notes to control sequencing and merge discipline.
4. Use the tasks folder to store user requests and main-agent plans.
5. Use the outputs folder to define what good intermediate and final outputs look like.

## Suggested first extension

If you want to turn this into a real project, add:

- a transport layer for your model API
- trace logging for each agent step
- structured parsing for subagent outputs
- retry and validation rules around the judge step

## Relationship to the skill

This scaffold complements:

- `skills/broken-access-control-agent-team`

The skill describes the reusable method. This scaffold shows how that method can
be organized as a learning project.
