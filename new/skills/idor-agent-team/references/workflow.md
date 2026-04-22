# Workflow

Use this workflow for a fine-grained IDOR review.

## 1. Intake

The main agent should identify:

- the route or function under review
- the resource type
- whether the path is read, download, update, delete, or export
- what artifacts are available

## 2. Stabilize the two key sides

Before reasoning about IDOR, stabilize:

- attacker-controlled input identifiers
- trusted authentication or identity context

These are distinct and should be analyzed separately.

## 3. Trace the path

The call-chain agent should trace:

- how the resource identifier moves through the system
- how trusted identity context moves through the system
- where the object is fetched, filtered, serialized, or mutated

## 4. Run relation checks

The main agent should explicitly ask:

- is the attacker-controlled object selector ever constrained by trusted identity
- is the returned or mutated object actually verified against trusted identity

## 5. Generate candidate findings

The IDOR hypothesis agent should use only verified facts and relation results.

## 6. Normalize evidence

The evidence agent should:

- group evidence by finding
- drop weak duplication
- preserve unresolved gaps

## 7. Judge findings

The judge agent should:

- confirm or reject findings
- assign severity and confidence
- keep missing layers explicit

## 8. Report

The reporter agent should:

- preserve scope
- preserve exploit path
- preserve evidence
- preserve uncertainty
