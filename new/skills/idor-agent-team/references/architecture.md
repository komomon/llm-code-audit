# Architecture

This file defines the recommended topology for a fine-grained IDOR review.

## Default topology

```text
User
  |
  v
Main Agent
  |
  +--> Scope Agent
  +--> Input Parameter Agent
  +--> Auth Context Agent
  +--> Call Chain Agent
  +--> Input/Auth Relation Agent
  +--> Output/Auth Relation Agent
  +--> IDOR Hypothesis Agent
  +--> Evidence Agent
  +--> Judge Agent
  +--> Reporter Agent
  |
  v
Final Answer
```

## Why this split works

This split is optimized for context limits and for IDOR-specific reasoning:

- `input-parameter-agent` keeps attacker-controlled IDs explicit
- `auth-context-agent` keeps trusted identity parameters explicit
- `call-chain-agent` keeps flow reasoning precise
- `input-auth-relation-agent` asks whether the chosen object is ever constrained by trusted identity
- `output-auth-relation-agent` asks whether the returned or mutated object is actually scoped to the caller

These are often the key questions in IDOR, and they are easy to lose in a
single broad review lane.

## Compact mode

For small paths, the main agent may use a compact set:

- `scope-agent`
- `input-parameter-agent`
- `auth-context-agent`
- `call-chain-agent`
- `judge-agent`

For larger or ambiguous paths, use the full fine-grained team.

## Parallelism

The main agent can often run these in parallel:

- `scope-agent`
- `input-parameter-agent`
- `auth-context-agent`
- `call-chain-agent`

The relation lanes usually depend on earlier facts:

- `input-auth-relation-agent`
- `output-auth-relation-agent`

Downstream lanes:

- `idor-hypothesis-agent`
- `evidence-agent`
- `judge-agent`
- `reporter-agent`

## Merge rules

- merge facts before relation conclusions
- keep input/auth relation and output/auth relation separate if they answer different questions
- keep read-path and write-path issues separate when impact differs
- let the judge see grouped evidence, not raw notes
