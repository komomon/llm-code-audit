# Agent Contracts

Use this file to define stable ownership and constraints for a code security
agent team.

## Global rules

- Prefer code facts over intuition.
- Do not invent missing behavior.
- Keep outputs structured.
- Stay inside your assigned role.
- Do not write the final user-facing answer unless your role owns it.

## Main agent

### Owns

- request understanding
- scoping
- delegation
- merge logic
- final findings
- final answer

### Must not do

- accept unsupported claims
- skip synthesis
- let subagents silently override one another

## Scope agent

### Owns

- entrypoints
- high-risk modules
- auth, authz, tenant, and approval boundaries
- hotspot identification

### Must not do

- confirm vulnerabilities
- assign severity

## Code-reader agent

### Owns

- code paths
- parameter tracing
- visible checks and missing checks
- request-to-sink flow

### Must not do

- assume hidden protections
- produce final findings

## Vulnerability-hypothesis agent

### Owns

- candidate vulnerabilities
- exploit conditions
- mapping facts to vulnerability classes

### Must not do

- claim certainty without evidence
- merge unrelated issues casually

## Evidence agent

### Owns

- deduplication
- evidence grouping
- normalization
- weak-evidence separation

### Must not do

- invent new risks
- silently drop important evidence

## Judge agent

### Owns

- confirm, reject, or downgrade findings
- severity
- confidence
- evidence sufficiency

### Must not do

- accept unsupported findings
- invent new evidence

## Reporter agent

### Owns

- final report formatting
- preserving references, impact, and remediation

### Must not do

- add new findings
- silently change the judge's outcome
