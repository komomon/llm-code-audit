---
name: authscan
description: Use when performing authorization vulnerability audit on a codebase. Detects horizontal privilege escalation (BOLA), vertical privilege escalation (BFLA), unauthorized access, and mass assignment vulnerabilities through trust chain analysis of parameters and authentication anchors.
---

# AuthScan — Universal Authorization Vulnerability Audit

Analyze code for authorization vulnerabilities by tracing trust relationships between user-controlled parameters and authentication anchors (session IDs, auth tokens, trusted internal sources). Works across languages and frameworks through semantic understanding.

## TODO Checklist (Follow This Exact Order)

**After reading this skill, execute the following steps in order. Mark each as done when complete.**

**Legend:** `[LOOP]` = this step repeats for each item in the set. `[LOOP:param]` = repeats per parameter. `[COND]` = conditional, only runs when criteria met.

- [ ] **1. Parse invocation argument** — determine mode and target(s)
  - `--recon` → Phase 1 only, stop after step 2
  - `--all` → Phase 1 + Phase 2 for ALL discovered endpoints + Phase 3
  - Specific endpoint(s) → Phase 1 (if recon_context.md missing) + Phase 2 for specified endpoint(s) + Phase 3

- [ ] **2. Phase 1: Project Reconnaissance** — read `reference/recon.md`
  - [ ] 2.1 Identify tech stack, framework, project structure
  - [ ] 2.2 Load `reference/auth-patterns-{language}.md` + `reference/extended-knowledge.md`
  - [ ] 2.3 `[LOOP:pattern]` Match each known auth pattern by priority order (grep/glob for keywords)
  - [ ] 2.4 `[COND]` If gaps remain after all known patterns → autonomous exploration
  - [ ] 2.5 Enumerate entry points (all endpoints for `--all`, or user-specified list)
  - [ ] 2.6 Generate `recon_context.md` (record discovered patterns here for later user review)

- [ ] **3. Phase 2: Per-Endpoint Deep Analysis** — read `reference/endpoint-analysis.md`
  - [ ] 3.0 Load `reference/trust-propagation-rules.md` + `reference/datasink-patterns.md` + `reference/extended-knowledge.md`
  - **`[LOOP:endpoint]` Repeat steps 3.1–3.6 for EACH target endpoint:**
    - [ ] 3.1 **Layer 0** — Endpoint-level auth check: global auth coverage? role/permission declarations? sufficiency?
    - [ ] 3.1.5 **Layer 0.5** — Trust anchor credibility (R10): trace anchor source, check for noLogin/token-fallback/gray-toggle risks
    - [ ] 3.2 **Layer 1** — Input parameter forward trust chain:
      - [ ] 3.2a Expand all input params to primitive types, classify by source + semantic role (identity/resource/filter/data)
      - [ ] 3.2b Identify trust anchors (verify credibility per Layer 0.5)
      - [ ] 3.2c `[LOOP:param]` For EACH user-controlled param: trace data flow, apply R1-R10 at each usage point
      - [ ] 3.2d `[COND]` DB results contain identity fields? → apply R9 (stored identity re-validation check)
      - [ ] 3.2e `[LOOP:call]` Cross-function tracking: follow calls to datasinks (depth limit, cache conclusions)
      - [ ] 3.2f Compile parameter risk list (severity by semantic role)
    - [ ] 3.3 **Layer 2** — Output backward trust chain (read `reference/output-analysis.md`):
      - [ ] 3.3a Expand all return fields to primitive types
      - [ ] 3.3b `[LOOP:field]` For EACH return field: trace source backward, cross-reference Layer 1 trust conclusions
      - [ ] 3.3c `[COND]` Boolean/enum returns → assess oracle risk
    - [ ] 3.4 `[COND]` **Layer 3** — Mass assignment check (only for write operations):
      - [ ] Read `reference/mass-assignment-patterns.md`
      - [ ] Trace input fields to write datasinks, identify sensitive fields without filtering
    - [ ] 3.5 Generate `analysis.json` for this endpoint, including:
      - [ ] Per-parameter risk cards with full propagation chains (code file + line at each step)
      - [ ] `[COND]` Multiple at-risk params? → Generate combined attack scenarios showing how params interact
      - [ ] Trust chain visualization (text-based tree showing anchor → trusted → at_risk paths)
    - [ ] 3.6 **Loop check:** more endpoints remaining? → return to 3.1 for next endpoint

- [ ] **4. Phase 3: Report & Self-Learning** — read `reference/report.md`
  - [ ] 4.1 Aggregate all endpoint analysis.json results
  - [ ] 4.2 Cross-endpoint correlation (shared vulnerable functions, auth gaps, inconsistencies)
  - [ ] 4.3 Risk prioritization (CRITICAL → HIGH → MEDIUM → LOW → INFO)
  - [ ] 4.4 Generate `report.md` (per-endpoint: all affected params + propagation chains + combined attack scenarios + trust chain visualization + specific remediation code) + `report.json`
  - [ ] 4.5 `[COND]` If new patterns discovered → list in report for user review (do NOT auto-write to any file)

## Invocation

```
/authscan "/api/users/getInfo"                      # Analyze specific HTTP endpoint
/authscan "com.example.controller.UserController"    # Analyze by class/module index
/authscan --recon                                    # Project reconnaissance only
/authscan --all                                      # Full project scan
```

## Core Principles

### Principle 1: Trust Chain Analysis

**Authorization vulnerability = user-controlled parameter reaches a data operation without establishing trust relationship with an authentication anchor.**

Trust relationship can form at ANY point in the data flow — before, during, or after the data operation. The analysis traces the complete lifecycle of each parameter.

### Principle 2: Per-Endpoint Independence

**Every endpoint MUST be analyzed as if the user calls it directly and independently.**

- Do NOT assume that data in the database is "safe" because another endpoint wrote it with auth checks
- Do NOT trust data from database/cache/external sources just because it "originally came from a trusted endpoint"
- The question for each endpoint is: **if an attacker calls THIS endpoint alone, with arbitrary parameters, can they access/modify unauthorized data?**
- Each input parameter must establish its OWN trust chain to an auth anchor WITHIN THIS endpoint's execution scope
- Data from database queries is only trusted if the query itself includes an auth anchor constraint — the data's origin from another endpoint is irrelevant

**Example of the trap to avoid:**
```java
// Endpoint A (has auth): creates order with userId from session
POST /api/orders  →  INSERT INTO orders (id, userId, data) VALUES (?, sessionUserId, ?)

// Endpoint B (the one we're analyzing): reads order by ID
GET /api/orders/{orderId}  →  SELECT * FROM orders WHERE id = orderId
//
// WRONG analysis: "orderId maps to an order created with auth, so it's safe"
// CORRECT analysis: "orderId has NO trust chain to auth anchor in THIS endpoint → AT RISK"
// An attacker can call GET /api/orders/123 with any orderId to access anyone's order
```

## Key References (load on demand)

**Methodology (read in order during execution):**
- `reference/recon.md` — Phase 1 detailed methodology
- `reference/endpoint-analysis.md` — Phase 2 detailed methodology (Layer 0-3)
- `reference/output-analysis.md` — Phase 2 Layer 2 detailed methodology
- `reference/report.md` — Phase 3 detailed methodology

**Knowledge Base (prioritized pattern matching — check these FIRST before autonomous exploration):**
- `reference/trust-propagation-rules.md` — 10 core trust rules (R1-R10) with examples (MUST read during Phase 2)
- `reference/auth-patterns-java.md` — Java auth patterns by priority (load during Phase 1 for Java projects)
- `reference/auth-patterns-python.md` — Python auth patterns by priority (load during Phase 1 for Python projects)
- `reference/auth-patterns-common.md` — Cross-language auth patterns (JWT, OAuth2, RBAC, etc.)
- `reference/datasink-patterns.md` — Data operation patterns that require authorization
- `reference/mass-assignment-patterns.md` — Mass assignment risk patterns

**Extended knowledge (load alongside reference files):**
- `reference/extended-knowledge.md` — User-confirmed discoveries from previous analyses (supplements, does NOT replace built-in references)

## Pattern Matching Strategy

**Reference-first, autonomous-second:**
1. During Phase 1 (recon), load the language-specific auth patterns reference
2. Match known patterns by priority order using grep/glob
3. If all known patterns checked and gaps remain → autonomous exploration
4. During Phase 2, load trust-propagation-rules and datasink-patterns references
5. Also load `reference/extended-knowledge.md` for any previously confirmed patterns
6. Apply known rules and patterns before making semantic judgments

## Self-Learning Protocol

If you discover an auth pattern, datasink pattern, or analysis insight NOT covered in the reference files:
1. Complete the current analysis using your semantic understanding
2. After analysis, in the report, list all newly discovered items with full details
3. **Present the list to the user for confirmation** — do NOT write to any file automatically
4. After user approval, write confirmed entries to `reference/extended-knowledge.md`
5. **Never modify existing reference files** — extended-knowledge.md is the append-only knowledge extension
6. Whether to merge extended knowledge into main references is the developer's decision

## Result JSON Location Tracking

**Every function reference in output JSON MUST include:**
```json
{
  "function": "ClassName.methodName",
  "file": "src/main/java/com/example/Controller.java",
  "line_start": 45,
  "line_end": 78
}
```
This enables re-verification — the LLM or human can jump directly to the code location to confirm findings.
