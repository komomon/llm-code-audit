# Architecture

This file defines the generic team topology for a code-vulnerability audit
skill.

## Default topology

```text
User
  |
  v
Main Agent
  |
  +--> Scope Agent
  +--> Code Reader Agent
  +--> Vulnerability Hypothesis Agent
  +--> Evidence Agent
  +--> Judge Agent
  +--> Reporter Agent
  |
  v
Final Answer
```

## Design principles

- Split by responsibility, not by model size.
- Keep merge logic centralized.
- Prefer a small number of clearly owned agents over many overlapping agents.
- Add specialization by checklist, not by collapsing workflow discipline.

## Parallelism

The main agent may often run these lanes in parallel:

- `scope-agent`
- `code-reader-agent`
- `vulnerability-hypothesis-agent`

The following are usually downstream:

- `evidence-agent`
- `judge-agent`
- `reporter-agent`

## Merge rules

- facts should be merged before verdicts
- hypotheses should be separated from confirmed findings
- judge should see grouped evidence, not raw duplicated output
- reporter should consume accepted findings only

## Extension patterns

To extend this template, you can:

- add a `dataflow-agent` for taint-style reviews
- add a `config-agent` for infrastructure or deployment misconfiguration reviews
- add a `dependency-agent` for package and library risk analysis
- add a `business-logic-agent` for state machine and approval workflow flaws

Only add an agent if it owns a distinct question and a distinct output.
