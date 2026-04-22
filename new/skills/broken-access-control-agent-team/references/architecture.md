# Architecture

This file defines the recommended topology for source-code broken access control
audits.

## Default topology

```text
User
  |
  v
Main Agent
  |
  +--> Scope Agent
  +--> Authz Mapper Agent
  +--> Code Path Agent
  +--> Access Control Hypothesis Agent
  +--> Evidence Agent
  +--> Judge Agent
  +--> Reporter Agent
  |
  v
Final Answer
```

## Why this split works

- `scope-agent` prevents the team from auditing random files without focus
- `authz-mapper-agent` keeps authentication and authorization boundaries explicit
- `code-path-agent` traces actual control flow instead of relying on assumptions
- `access-control-hypothesis-agent` turns verified facts into candidate BAC findings
- `evidence-agent` makes later judgment easier by grouping support cleanly
- `judge-agent` keeps the final finding standard strict
- `reporter-agent` preserves human readability without changing substance

## Key analysis dimensions

Broken access control reviews usually need to separate these dimensions:

- authentication
- role-based access
- ownership-based access
- tenant isolation
- approval or workflow authority

Do not collapse all of these into one vague "auth" bucket.

## Parallelism

The main agent can often run these in parallel:

- `scope-agent`
- `authz-mapper-agent`
- `code-path-agent`

The following usually depend on earlier outputs:

- `access-control-hypothesis-agent`
- `evidence-agent`
- `judge-agent`
- `reporter-agent`

## Merge rules

- merge facts before merging findings
- separate read-path and write-path issues when they differ
- separate horizontal, vertical, and tenant-isolation issues when impact differs
- let the judge see grouped evidence rather than raw duplicate notes

## Extension patterns

Add an extra agent only if it owns a distinct question, for example:

- `query-scope-agent` for ORM or repository-heavy systems
- `workflow-agent` for approval and state-machine-heavy systems
- `batch-job-agent` when offline tasks can bypass normal authorization paths
