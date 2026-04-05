# Phase 3: Aggregation, Report & Self-Learning

**Goal:** Aggregate all per-endpoint results, perform cross-endpoint correlation, generate final report, and capture newly discovered auth patterns.

## Step 1 — Aggregate Results

1. Load all `analysis.json` files from `{output_dir}/*/analysis.json` (the output directory established in SKILL.md step 1)
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

> **DISABLED — not currently generated.** Template moved to `reference/report-template.md`. To re-enable, add `Write {output_dir}/report.md` to SKILL.md step 4.5 and read the template file.

### report-summary.md

See `reference/report-summary-template.md` for the full template and writing principles.

### report.json (Machine-Readable)

Generate using this schema:

```json
{
  "project": "{project_name}",
  "scan_date": "{date}",
  "summary": {
    "total_endpoints": 0,
    "endpoints_with_risks": 0,
    "total_findings": 0,
    "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
    "by_type": {
      "unauthorized_access": 0,
      "identity_impersonation": 0,
      "vertical_privilege_escalation": 0,
      "bola_write": 0,
      "bola_read": 0,
      "mass_assignment": 0,
      "data_leakage": 0,
      "parameter_leakage": 0,
      "info_oracle": 0
    }
  },
  "endpoints": [
    {
      "endpoint": "/api/account/confirm",
      "method": "POST",
      "handler": {
        "function": "AccountServiceImpl.confirmAccount",
        "file": "src/main/java/com/example/service/AccountServiceImpl.java",
        "line_start": 170,
        "line_end": 214,
        "business_function": "企业账户开通确认（二阶段），完成企业开户流程"
      },
      "overall_severity": "CRITICAL",
      "trust_anchors": [
        {
          "name": "currentUserId",
          "source": "SecurityContext.getCurrentUserId()",
          "file": "src/main/java/com/example/service/AccountServiceImpl.java",
          "line": 171,
          "credibility": "compromised",
          "credibility_reason": "noLoginExchangeUid=true, may fallback to user input (R10)"
        }
      ],
      "parameter_risks": [
        {
          "param": "applyNo",
          "semantic_role": "resource",
          "trust_status": "at_risk",
          "trust_rule": "R8",
          "severity": "HIGH",
          "exploitation": "Attacker can load any enterprise's validation record by supplying an arbitrary applyNo",
          "reason": "applyNo flows to repository.load() without trust anchor binding",
          "flow_path": [
            "request.getApplyNo() @ AccountServiceImpl.java:176",
            "accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223",
            "SELECT WHERE enterprise_id=? AND apply_no=? (no anchor) @ AccountRepositoryImpl.java:226"
          ],
          "datasink": {
            "function": "AccountRepositoryImpl.load",
            "file": "src/main/java/com/example/repo/AccountRepositoryImpl.java",
            "line_start": 223,
            "line_end": 227,
            "op_type": "read"
          }
        },
        {
          "param": "enterpriseId",
          "semantic_role": "identity",
          "trust_status": "at_risk",
          "trust_rule": "R8+R9",
          "severity": "CRITICAL",
          "exploitation": "Attacker can substitute any enterpriseId to hijack account opening for another enterprise",
          "reason": "Identity param used in query without anchor (R8). Stored value exists but code uses user input instead (R9 Check 2).",
          "flow_path": [
            "request.getEnterpriseId() @ AccountServiceImpl.java:175",
            "accountRepository.load(enterpriseId, applyNo) @ AccountRepositoryImpl.java:223",
            "account.setEnterpriseId(request.getEnterpriseId()) @ AccountServiceImpl.java:204",
            "INSERT INTO accounts (..., enterprise_id, ...) @ AccountRepositoryImpl.java:231"
          ],
          "datasink": {
            "function": "AccountRepositoryImpl.openAccount",
            "file": "src/main/java/com/example/repo/AccountRepositoryImpl.java",
            "line_start": 230,
            "line_end": 234,
            "op_type": "write"
          }
        }
      ],
      "r9_analysis": {
        "triggered": true,
        "stored_identity_fields": ["operatorUserId", "enterpriseId"],
        "check1_identity_comparison": {
          "passed": false,
          "detail": "No code compares currentUserId with accountParam.getOperatorUserId()"
        },
        "check2_stored_value_usage": {
          "passed": false,
          "detail": "account.setEnterpriseId(request.getEnterpriseId()) uses input, not accountParam.getEnterpriseId()"
        }
      },
      "combination_risks": [
        {
          "params": ["applyNo", "enterpriseId"],
          "combined_severity": "CRITICAL",
          "description": "Both params combine in repository.load() to locate any enterprise's record without trust anchor",
          "trust_anchor_present": false
        }
      ],
      "attack_scenarios": [
        {
          "title": "Cross-Enterprise Account Hijacking",
          "severity": "CRITICAL",
          "involved_params": ["applyNo", "enterpriseId", "verifyId"],
          "impact": "Attacker opens account for any enterprise using victim's application record",
          "root_cause": "No identity binding between current caller and Phase 1 initiator (R9 Check 1 + R8)"
        }
      ],
      "output_risks": [],
      "mass_assignment_risks": [],
      "remediation_summary": "Add currentUserId ownership check (R9 Check 1), use stored values for business fields (R9 Check 2), add trust anchor to repository.load() query"
    }
  ],
  "cross_endpoint_issues": {
    "shared_vulnerable_functions": [],
    "auth_coverage_gaps": [],
    "inconsistent_patterns": []
  },
  "discovered_patterns": []
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
- [ ] `{output_dir}/report-summary.md` written to disk — comprehensive 9-module report
- [ ] `{output_dir}/report.json` written to disk — machine-readable structured data
- [ ] Discovered patterns listed in report-summary.md for user review (NOT auto-written to files)
