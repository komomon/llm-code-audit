# Phase 3: Aggregation, Report & Self-Learning

**Goal:** Aggregate all per-endpoint results, perform cross-endpoint correlation, generate final report, and capture newly discovered auth patterns.

## Step 1 — Aggregate Results

1. Load all `analysis.json` files from `results/{project_name}/*/`
2. Collect:
   - Total endpoints analyzed
   - Endpoints with risks (by severity)
   - All unique risk findings
   - All trust anchors encountered

## Step 2 — Cross-Endpoint Correlation

Look for patterns that only become visible when analyzing multiple endpoints together:

**2a. Shared Vulnerable Functions**
- If the same service/DAO function appears as `at_risk` across multiple endpoints → elevate risk severity
- Example: `OrderDAO.findById(orderId)` without auth appears in 5 endpoints → systemic issue

**2b. Global Auth Gaps**
- Compare the endpoint list from recon with global auth coverage
- Any endpoint NOT covered by global auth AND has no endpoint-level auth → flag as unauthorized access risk
- Batch report: "N endpoints lack authentication"

**2c. Inconsistent Auth Patterns**
- Same entity (e.g., Order) accessed with auth in some endpoints but without in others → flag inconsistency
- This often indicates developer oversight

## Step 3 — Risk Prioritization

Sort all findings by severity:

| Priority | Risk Type | Severity | Description |
|----------|-----------|----------|-------------|
| P0 | Unauthorized access | CRITICAL | Endpoint has no auth at all |
| P1 | Identity impersonation | CRITICAL | User-controlled identity param (userId/accountId/tenantId) used where session identity should be — attacker acts as ANY user |
| P2 | Vertical privilege escalation | HIGH | Insufficient role/permission check for the endpoint's function |
| P3 | BOLA — write (resource) | HIGH | Resource ID reaches write datasink without auth binding |
| P4 | Post-auth write risk pending | HIGH | Write operation executed before auth validation (R6) |
| P5 | BOLA — read (resource) | MEDIUM | Resource ID reaches read datasink without auth binding |
| P6 | Mass assignment | MEDIUM | Sensitive field writable from user input without filtering |
| P7 | Data leakage via output | MEDIUM | Untrusted query results returned to user |
| P8 | Information oracle | LOW | Boolean/enum return allows enumeration |
| P9 | Filter/scope param risk | LOW | Filter param without auth may expose cross-user aggregation |
| P10 | Needs manual review | INFO | Exceeded depth limit or circular call |

## Step 4 — Generate Final Report

### report.md (Human-Readable)

```markdown
# AuthScan Report — {project_name}

**Scan Date:** {date}
**Endpoints Analyzed:** {count}
**Findings:** {risk_count} risks across {endpoint_count} endpoints

## Risk Summary

| Severity | Count | Types |
|----------|-------|-------|
| CRITICAL | {n} | Unauthorized access, Identity impersonation |
| HIGH | {n} | Vertical PE, Horizontal PE (write), Post-auth write |
| MEDIUM | {n} | Horizontal PE (read), Mass assignment, Data leakage |
| LOW | {n} | Information oracle, Filter/scope param risk |

## Detailed Findings (Per Endpoint)

**For EACH endpoint with risks, generate the following complete analysis. Do NOT skip parameters — every at-risk parameter must be individually explained AND combined into attack scenarios.**

### Endpoint: {endpoint} ({method})
**Handler:** `{ClassName.method}` @ `{file}:{line_start}-{line_end}`
**Trust Anchors:** {anchor_name} from `{source}` @ `{file}:{line}`

#### All Affected Parameters

**For EACH at-risk parameter, provide a complete risk card:**

##### Parameter: `{param_name}` — {severity}
- **Source:** {where the param comes from — RequestBody field / PathVariable / QueryParam}
- **Semantic Role:** {identity / resource / filter / data}
- **Trust Status:** {at_risk / risk_pending / identity_impersonation}
- **Applied Rule:** {R8 / R9 / R10 / etc.}
- **Risk Propagation Chain (full code trace):**
  ```
  User Input: request.{param} (user-controlled)
    ↓ used at: {file}:{line} — {code snippet}
    ↓ flows to: {next_function}() @ {file}:{line}
    ↓ reaches datasink: {operation} @ {file}:{line}
    ✗ NO trust anchor association found in this path
  ```
- **Vulnerability:** {what an attacker can do with this specific parameter}
- **Code Location:** `{file}:{line_start}-{line_end}` — {brief code context}

##### Parameter: `{param_name_2}` — {severity}
(same structure for each parameter)

#### Combined Attack Scenarios

**CRITICAL: When multiple parameters are at-risk, describe how they work TOGETHER to enable attacks. Do not just list individual parameter risks — show the combined exploitation.**

**Attack Scenario 1: {scenario_title}**
| Step | Attacker Action | Exploited Parameter(s) | System Behavior | Code Location |
|------|----------------|----------------------|-----------------|---------------|
| 1 | {action} | `{param}` | {what system does} | `{file}:{line}` |
| 2 | {action} | `{param1}` + `{param2}` | {what system does} | `{file}:{line}` |
| 3 | ... | ... | ... | ... |
| **Result** | **{attack outcome — what the attacker achieves}** | | | |

**Attack Scenario 2: {scenario_title}** (if applicable)
(same table format)

**Multi-Parameter Interaction Analysis:**
- How do the at-risk parameters relate to each other? (e.g., `orderNo` locates the record, `enterpriseId` is used in the write — together they enable querying any record AND writing arbitrary enterprise identity)
- Which combination creates the most severe impact?
- Are some parameter risks dependent on others? (e.g., `param2` is only exploitable if `param1` is also controllable)

#### Trust Chain Visualization

```
Trust Anchor: {anchor_name} @ {file}:{line}
  │
  ├─→ [TRUSTED] {param1} → {operation} @ {file}:{line} (R1: direct association)
  │     └─→ [TRUSTED] {derived_result} (R2: derived trust)
  │
  ├─✗ [AT RISK] {param3} → {datasink} @ {file}:{line} (R8: no association)
  │     └─✗ [AT RISK] {query_result} → returned to user @ {file}:{line}
  │
  └─✗ [CRITICAL] {param4} (identity) → {write_datasink} @ {file}:{line} (R9: stored identity not verified)
        └─ Stored identity: {stored_field} @ {file}:{line} — NOT compared with anchor
```

#### Remediation (Endpoint-Specific)

**For each at-risk parameter, provide the specific fix with code:**

```java
// Fix for {param1}: Add trust anchor to query constraint
// Before (vulnerable):
{vulnerable_code_line}

// After (fixed):
{fixed_code_line}
```

```java
// Fix for {param2}: Add identity comparison (R9)
// Before (vulnerable):
{vulnerable_code_line}

// After (fixed):
if (!currentUserId.equals(storedIdentity)) {
    throw new AccessDeniedException("Not authorized");
}
```

---

(Repeat the above structure for each endpoint with findings)

## Cross-Endpoint Issues

### Shared Vulnerable Functions
{list}

### Auth Coverage Gaps
{list}

## Remediation Recommendations

### For Unauthorized Access (P0)
Add authentication to the endpoint. Ensure global auth filter/interceptor covers the path.

### For Vertical Privilege Escalation (P1)
Add role/permission check matching the endpoint's privilege requirement.

### For Horizontal Privilege Escalation (P2-P3)
Add trust anchor (session user ID) to the data operation's constraint:
- Query: add `WHERE ... AND user_id = {session_uid}`
- Or: add ownership check before data access

### For Post-Auth Write (P4)
Move the authorization check BEFORE the write operation.

### For Mass Assignment (P5)
Use explicit field whitelists or dedicated DTOs that exclude sensitive fields.

## Appendix: All Analyzed Endpoints
| Endpoint | Risk Level | Findings |
|----------|-----------|----------|
| ... | ... | ... |
```

### report.json (Machine-Readable)

```json
{
  "project": "{project_name}",
  "scan_date": "{date}",
  "summary": {
    "total_endpoints": 0,
    "endpoints_with_risks": 0,
    "total_findings": 0,
    "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
  },
  "findings": [],
  "cross_endpoint_issues": {
    "shared_vulnerable_functions": [],
    "auth_coverage_gaps": [],
    "inconsistent_patterns": []
  },
  "endpoints": []
}
```

## Step 5 — Discovered Patterns Review (Present to User)

Review all analysis notes for auth patterns that were identified through autonomous exploration (not matched from references).

**Do NOT write directly to any reference file. Instead, present findings to the user.**

In the report, add a section:

```markdown
## Discovered Patterns & Insights (Pending User Review)

The following items were found during analysis but are not yet in the reference library.
Please review and confirm which ones should be added to the extended knowledge base.

### Pattern 1: {Pattern Name}
- **Type:** auth-pattern / datasink / trust-rule-extension / methodology-note
- **Framework/Language:** {info}
- **Search keywords:** `keyword1`, `keyword2`
- **Description:** {description}
- **Example:**
  ```{language}
  {code}
  ```
- **Source project:** {project_name}, {date}
- **Recommendation:** Add to extended knowledge / Skip / Needs further validation

### Pattern 2: ...
```

After the user reviews and approves specific entries, THEN append the approved ones to `extended-knowledge.md` (in the reference directory).

**Important:**
- Never modify existing reference files (auth-patterns-*.md, datasink-patterns.md, etc.)
- `extended-knowledge.md` is the append-only external knowledge extension
- Whether to eventually merge extended knowledge into main references is the developer's decision

## Completion Criteria

- [ ] All endpoint results aggregated
- [ ] Cross-endpoint correlation completed
- [ ] Findings sorted by priority
- [ ] report.md generated (human-readable)
- [ ] report.json generated (machine-readable)
- [ ] Discovered patterns listed in report for user review (NOT auto-written to files)
