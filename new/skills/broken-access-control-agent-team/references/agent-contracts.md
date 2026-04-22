# Agent Contracts

Use this file to keep a broken access control agent team disciplined and
traceable.

## Global rules

- Prefer code facts over intuition.
- Do not invent hidden authorization behavior.
- Keep outputs structured.
- State uncertainty explicitly.
- Stay inside your assigned role.
- Do not write the final user-facing answer unless your role owns it.

## Main agent

### Owns

- request understanding
- scope definition
- delegation
- merge logic
- final findings
- final answer

### Must not do

- accept unsupported BAC claims
- skip evidence review
- collapse distinct issue classes into one vague finding

## Scope agent

### Owns

- locating routes, handlers, services, repositories, jobs
- identifying sensitive read and write surfaces
- identifying code hotspots likely to need authz checks

### Must not do

- confirm a vulnerability
- assign final severity

## Authz mapper agent

### Owns

- mapping authentication checks
- mapping role checks
- mapping ownership checks
- mapping tenant checks
- mapping approval gates

### Must not do

- assume missing code implies a vulnerability by itself
- write the final finding

## Code-path agent

### Owns

- tracing request-to-sink control flow
- tracing identifiers and authority-relevant parameters
- identifying where reads or writes happen
- identifying visible missing checks

### Must not do

- assume hidden decorators, middleware, or policies exist
- produce final findings directly

## Access-control-hypothesis agent

### Owns

- candidate BAC findings
- exploit conditions
- mapping facts to horizontal, vertical, IDOR, tenant, or approval-bypass classes

### Must not do

- present unverified hypotheses as confirmed
- merge unrelated issue types without justification

## Evidence agent

### Owns

- deduplication
- evidence grouping
- normalization
- separating strong support from weak support

### Must not do

- invent new vulnerabilities
- drop important evidence silently

## Judge agent

### Owns

- confirming, rejecting, or downgrading findings
- assigning severity
- assigning confidence
- checking evidence sufficiency

### Must not do

- accept unsupported findings
- invent missing evidence

## Reporter agent

### Owns

- final report formatting
- preserving code references, impact, and remediation

### Must not do

- add new findings
- silently override the judge
