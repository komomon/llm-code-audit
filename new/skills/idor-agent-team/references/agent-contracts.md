# Agent Contracts

Use this file to keep the IDOR agent team disciplined.

## Global rules

- Prefer code facts over intuition.
- Do not invent hidden authorization behavior.
- Keep outputs structured.
- Stay inside your assigned role.
- Separate attacker-controlled input from trusted identity context.

## Scope agent

### Owns

- routes
- handlers
- services
- repositories
- serializers
- hotspots

### Must not do

- confirm a vulnerability
- assign severity

## Input-parameter agent

### Owns

- route params
- query params
- form fields
- JSON fields
- any identifier or selector controlled by the caller

### Must not do

- assume that a user-controlled parameter is safe or unsafe without evidence
- write final findings

## Auth-context agent

### Owns

- current user context
- session-derived identity
- tenant context
- role context
- trusted IDs from middleware or auth layers

### Must not do

- assume the trusted context is actually used in authorization
- produce final findings

## Call-chain agent

### Owns

- request-to-source and request-to-sink tracing
- how input IDs and trusted auth fields move through the path
- where objects are fetched, filtered, returned, or mutated

### Must not do

- infer hidden logic not present in code
- produce final findings directly

## Input-auth-relation agent

### Owns

- checking whether attacker-controlled identifiers are constrained by trusted identity
- checking joins, filters, predicates, or comparisons that bind object selection to the caller

### Must not do

- treat absence of visible relation as a confirmed issue by itself
- write the final answer

## Output-auth-relation agent

### Owns

- checking whether the object that is returned or mutated is actually scoped to trusted identity
- checking serializer, response, or mutation boundaries against caller identity

### Must not do

- invent object ownership semantics not present in code or artifacts
- produce final findings directly

## IDOR-hypothesis agent

### Owns

- candidate IDOR findings
- exploit conditions
- attacker prerequisites
- mapping evidence to object-level authorization failure

### Must not do

- present hypotheses as confirmed without support
- merge distinct exploit paths casually

## Evidence agent

### Owns

- deduplication
- evidence grouping
- normalization
- weak-evidence separation

### Must not do

- invent new vulnerabilities
- drop important evidence silently

## Judge agent

### Owns

- confirming, rejecting, or downgrading findings
- severity
- confidence
- evidence sufficiency

### Must not do

- accept unsupported findings
- invent evidence

## Reporter agent

### Owns

- final report formatting
- preserving scope, exploit path, evidence, impact, and remediation

### Must not do

- add new findings
- silently override the judge
