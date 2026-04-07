# AuthScan Design Specification

> Universal authorization vulnerability audit system powered by LLM + Skills

## 1. Project Overview

### 1.1 Problem Statement

Authorization vulnerabilities (BOLA, BFLA, unauthorized access, mass assignment) are fundamentally different from injection vulnerabilities. Their essence: **user-controlled parameters reach data operations without establishing a trust relationship with user-uncontrollable parameters** (session ID, auth tokens, trusted internal sources).

Traditional SAST tools rely on AST/CPG and predefined rules, making them brittle across different languages, frameworks, and custom auth patterns. LLMs can understand code semantics and reason about authorization logic regardless of technology stack.

### 1.2 Core Thesis

The fundamental question for each parameter is: **does it establish a direct or indirect association with a user-uncontrollable parameter (trust anchor) at any point in its data flow lifecycle?**

This association can happen:
- **Before** a data operation (pre-auth: `WHERE id=a1 AND userId=sessionId`)
- **After** a data operation (post-auth: query results later filtered by session)
- **Through** intermediate trusted results (transitive trust)

### 1.3 Scope

| Vulnerability Type | Description | Analysis Layer |
|---|---|---|
| Unauthorized Access | Endpoint has no authentication at all | Layer 0 (Endpoint) |
| Vertical Privilege Escalation (BFLA) | Insufficient role/permission checks | Layer 0 (Endpoint) |
| Horizontal Privilege Escalation (BOLA) | Parameters not bound to user identity | Layer 1 (Input Params) |
| Data Leakage via Output | Response contains unauthorized data | Layer 2 (Output Params) |
| Mass Assignment | Sensitive fields writable by user | Layer 3 (Field-level) |

### 1.4 Design Constraints

- **Pure LLM + native tools**: grep, read, glob, bash only. No AST/CPG tools.
- **Language priority**: Java, Python first; methodology must be language-agnostic.
- **Step-by-step logic**: Each analysis step has a single, clear objective.
- **Self-learning**: Automatically document newly discovered auth patterns.
- **Reference-first**: Match known patterns by priority before autonomous exploration.

## 2. Architecture

### 2.1 Three-Phase Pipeline

```
Phase 1: Project Reconnaissance
  → Understand tech stack, identify auth mechanisms, enumerate endpoints
  → Output: recon_context.md (reused by all endpoint analyses)

Phase 2: Per-Endpoint Deep Analysis (× N endpoints)
  → Layer 0: Endpoint-level auth check
  → Layer 1: Input parameter forward trust chain
  → Layer 2: Output parameter backward trust chain
  → Layer 3: Mass assignment check (write operations)
  → Output: per-endpoint analysis.json

Phase 3: Aggregation & Self-Learning
  → Cross-endpoint correlation, self-learning, final report
  → Output: report.md + report.json
```

### 2.2 Technology

- **Execution**: Claude Code SDK (Python) for agent orchestration
- **Methodology**: Skills (Markdown files following superpowers conventions)
- **Knowledge**: References (prioritized auth pattern examples)
- **Self-learning**: extended-knowledge.md (user-confirmed discoveries, append-only, in reference/)

### 2.3 Usage Patterns

```bash
# Via Claude Code skill invocation:
/authscan "/api/users/getInfo"                     # Analyze specific endpoint
/authscan "com.example.controller.UserController"  # Analyze by class index
/authscan --recon                                  # Reconnaissance only
/authscan --all                                    # Full project scan
```

## 3. Core Concepts & Definitions

### 3.1 Parameter Classification

| Category | Definition | Example |
|---|---|---|
| **Trust Anchor** | User-uncontrollable parameter from auth source | `session.getUserId()`, `@AuthenticationPrincipal` |
| **Trusted Parameter** | Has direct/indirect association with a trust anchor | `a1` in `WHERE a1=x AND userId=sessionId` |
| **Risk-Free Parameter** | Not used, or directly echoed back without affecting data access | `a4` that appears nowhere in data operations |
| **At-Risk Parameter** | Neither trusted nor risk-free; reaches datasink without anchor association | `a3` in `WHERE id=a3` (no session binding) |

### 3.2 Key Components

| Component | Definition |
|---|---|
| **Entry Function** | The first function where user-controlled parameters enter (HTTP handler, RPC handler) |
| **AuthCheck** | Any logic that validates authorization: annotations, interceptors, in-function checks, conditional guards |
| **DataSink** | Operations requiring authorization: DB queries, file I/O, network calls, data modifications |
| **Trust Chain** | The path through which a parameter establishes association with a trust anchor |

### 3.3 Trust Propagation Rules

| # | Rule | Description | Result |
|---|---|---|---|
| R1 | Direct Association | Param and anchor in same constraint | Trusted |
| R2 | Derived Trust | Result from anchor-constrained operation | All fields trusted |
| R3 | Transitive Trust | Operation based on already-trusted data | Trusted |
| R4 | Conditional Guard | Auth condition passes (throw/return on failure) | Trusted in passing branch |
| R5 | Post-Auth Read | Read result later associated with anchor | Trusted (retroactive) |
| R6 | Post-Auth Write | Write executed before anchor association | **Risk pending** (irreversible) |
| R7 | Transform Neutral | toString/split/format operations | Trust status unchanged |
| R8 | No Association | Entire data flow has no anchor association | **At-risk** |

#### Trust propagation through conditions — classification:

| Condition Type | Example | Constitutes Auth? |
|---|---|---|
| Auth condition | `if(userId != session.userId) throw 403` | Yes |
| Permission query | `if(!permService.hasAccess(session.uid, resId))` | Yes (also trusts resId) |
| Business logic | `if(status == "active")` | No |

## 4. Phase 1: Project Reconnaissance (Detail)

### 4.1 Step 1 — Tech Stack & Structure Identification

**Actions:**
- Scan build files: `pom.xml`, `build.gradle`, `requirements.txt`, `pyproject.toml`, `package.json`
- Identify framework: Spring Boot / Django / Flask / FastAPI / Express / etc.
- Map project directory structure: controller/service/dao/model layers
- Locate config files: `application.yml`, `settings.py`, etc.

### 4.2 Step 2 — Auth Pattern Identification

**Strategy: Reference-first, then autonomous exploration.**

1. Load `references/auth-patterns-{language}.md`
2. For each pattern (by priority), search for characteristic keywords via grep/glob
3. On match: record auth mechanism details (location, scope, strength)
4. On no match across all known patterns: autonomous search for auth-related keywords (`session`, `auth`, `permission`, `role`, `token`, `login`, `security`, `principal`, `credential`)
5. Identify all layers:
   - Global auth (interceptors, middleware, filter chains)
   - Endpoint-level auth (annotations, decorators, route-level declarations)
   - In-function auth (explicit session/permission checks)
   - Role/permission model (RBAC tables, role enums, permission structures)
   - Trust anchor sources (session getters, auth injection points, internal SDK calls)

### 4.3 Step 3 — Entry Point Enumeration

**Two modes:**
- **Full scan**: Search framework-specific endpoint definitions (`@RequestMapping`, `@app.route`, `@router.get`, etc.)
- **User-specified**: Use provided endpoint names/class indices

**For each endpoint, record:**
- Endpoint path and HTTP method
- Handler function location (file + line range)
- Whether covered by global auth
- Any endpoint-level auth declarations

### 4.4 Step 4 — Generate Recon Context

Output `recon_context.md` containing all above information in structured format. This document is loaded as context for every subsequent endpoint analysis.

### 4.5 Step 5 — Record Discovered Patterns

If any auth pattern was discovered through autonomous exploration (not in references), record it in `recon_context.md` under a "Discovered Patterns" section for later user review. Do NOT write to any reference file at this stage.

## 5. Phase 2: Per-Endpoint Deep Analysis (Detail)

Each endpoint analysis is independent and loads `recon_context.md` as background context.

**Per-Endpoint Independence Principle:** Every endpoint MUST be analyzed as if the user calls it directly and independently with arbitrary parameters. Do NOT assume database data is "safe" because another endpoint wrote it with auth. Each parameter must establish its OWN trust chain within THIS endpoint's execution scope.

### 5.1 Layer 0 — Endpoint-Level Auth Check

**Checks:**
1. Is this endpoint covered by global auth? (If no → **Unauthorized Access Risk**, severity: CRITICAL)
2. Does this endpoint have endpoint-level permission declarations? (e.g., `@PreAuthorize("hasRole('ADMIN')")`)
3. If endpoint functionality semantically requires elevated permissions but only has basic login check → **Vertical Privilege Escalation Risk**, severity: HIGH
4. Is this endpoint excluded from global auth via whitelist? (If yes, is it intentional?)

### 5.2 Layer 1 — Input Parameter Forward Trust Chain

**Step 1: Parameter Expansion**
- Extract all input parameters from handler function signature
- Expand complex types (DTO/VO/Map) to primitive fields
- Classify: user-controlled vs framework-injected (auth anchors marked immediately)

**Step 2: Trust Anchor Identification**
- Load trust anchor sources from `recon_context.md`
- Search function body for anchor usage (e.g., `session.getUserId()`, `user.getId()`)
- Mark all anchor variables and their assignment locations

**Step 3: Data Flow Tracking & Trust Determination**
- For each user-controlled parameter, trace its entire data flow lifecycle
- At each usage point (datasink, assignment, function call, condition, return), apply trust propagation rules R1-R8
- Key: trust association can happen ANYWHERE in the data flow, not just at the datasink

**Step 4: Cross-Function Tracking**
- Follow function calls up to configurable depth (default: 10)
- Maintain trust conclusion cache: `{function_name → {param: trust_status, return: trust_source}}`
- Priority: trace datasink-containing call chains first
- Detect recursion/cycles: stop and mark as "circular call"

### 5.3 Layer 2 — Output Parameter Backward Trust Chain

**Step 1: Return Value Expansion**
- Identify all return statements
- Expand return objects to primitive fields

**Step 2: Reverse Source Tracing**
- For each return field, recursively trace upstream data source:
  - From trusted query (anchor-constrained) → Safe
  - From static variable/constant → Safe
  - From trusted SDK/internal service → Safe
  - From input parameter echo (returning user's own input) → Risk-free
  - From untrusted query result → At-risk (cross-reference Layer 1 trust determination)
  - From multiple sources (concatenation) → Judge each source independently

**Step 3: Information Oracle Risk**
- Boolean/enum/status code returns → assess oracle attack possibility
- User-controlled parameter directly determines true/false → Low risk flag

### 5.4 Layer 3 — Mass Assignment Check (Write Operations Only)

**Trigger**: Only for write operations (POST/PUT/PATCH/DELETE or semantic judgment).

**Steps:**
1. Trace input object fields to their target datasinks (DB INSERT/UPDATE)
2. Identify sensitive fields that should not be user-modifiable:
   - Permission/role fields: `role`, `permission`, `isAdmin`, `level`
   - Identity fields: `userId`, `ownerId`, `createdBy`
   - Status fields: `status`, `approved`, `verified`
   - Business-sensitive fields: `price`, `balance`, `credits`
3. Check for field filtering mechanisms (whitelist/blacklist, explicit field mapping)
4. No filtering + sensitive field reaches datasink → **Mass Assignment Risk**

### 5.5 Result Output Format

```json
{
  "endpoint": "/api/order/detail",
  "method": "GET",
  "handler": {
    "function": "OrderController.getDetail",
    "file": "src/main/java/com/example/controller/OrderController.java",
    "line_start": 45,
    "line_end": 78
  },
  "endpoint_level_risks": [
    {
      "type": "vertical_privilege_escalation",
      "detail": "Only checks login status, no role/permission check",
      "severity": "HIGH",
      "location": {
        "file": "src/main/java/com/example/config/SecurityConfig.java",
        "line_start": 23,
        "line_end": 25
      }
    }
  ],
  "parameter_risk_list": [
    {
      "param": "orderId",
      "type": "user_controlled",
      "expanded_from": "RequestParam orderId (String)",
      "trust_status": "at_risk",
      "reason": "orderId used in SELECT ... WHERE id=orderId without session binding",
      "trust_chain": [],
      "affected_datasinks": [
        {
          "operation": "SELECT * FROM orders WHERE id = orderId",
          "function": "OrderDAO.findById",
          "file": "src/main/java/com/example/dao/OrderDAO.java",
          "line_start": 12,
          "line_end": 15,
          "type": "read",
          "trust_rule_applied": "R8 (No Association)"
        }
      ],
      "severity": "HIGH"
    },
    {
      "param": "userId (from session)",
      "type": "trust_anchor",
      "trust_status": "anchor",
      "reason": "From @AuthenticationPrincipal, user-uncontrollable",
      "source": {
        "function": "SecurityContextHolder.getContext().getAuthentication()",
        "file": "src/main/java/com/example/controller/OrderController.java",
        "line_start": 48,
        "line_end": 48
      }
    }
  ],
  "output_risk_list": [
    {
      "field": "order.paymentInfo",
      "trust_status": "at_risk",
      "source_chain": [
        {
          "step": "OrderDAO.findById(orderId)",
          "trust": "untrusted (orderId is at_risk)",
          "file": "src/main/java/com/example/dao/OrderDAO.java",
          "line_start": 12,
          "line_end": 15
        }
      ],
      "reason": "Data source query not constrained by trust anchor"
    }
  ],
  "mass_assignment_risks": [],
  "trust_chain_summary": {
    "anchors": ["session.getUserId() @ OrderController.java:48"],
    "trusted_params": [],
    "at_risk_params": ["orderId"],
    "risk_free_params": [],
    "propagation_tree": {
      "session.getUserId()": {
        "status": "anchor",
        "propagates_to": []
      },
      "orderId": {
        "status": "at_risk",
        "reaches_datasinks": ["OrderDAO.findById:12-15"],
        "anchor_association": "none"
      }
    }
  },
  "functions_analyzed": [
    {
      "function": "OrderController.getDetail",
      "file": "src/main/java/com/example/controller/OrderController.java",
      "line_start": 45,
      "line_end": 78,
      "role": "entry_function"
    },
    {
      "function": "OrderDAO.findById",
      "file": "src/main/java/com/example/dao/OrderDAO.java",
      "line_start": 10,
      "line_end": 20,
      "role": "datasink"
    }
  ]
}
```

## 6. Phase 3: Aggregation & Self-Learning (Detail)

### 6.1 Risk Aggregation
- Collect all per-endpoint analysis results
- Deduplicate: same unauthed service method called by multiple endpoints → merge
- Sort by severity: Unauthorized > Vertical > Horizontal(write) > Horizontal(read) > Mass Assignment > Info Oracle

### 6.2 Cross-Endpoint Correlation
- Service function called by multiple endpoints without auth → elevate risk
- Global auth config gaps (paths not covered) → batch flag
- Shared at-risk parameters across endpoints → pattern indicator

### 6.3 Self-Learning (User-Approved, Append-Only)
- If new auth patterns, datasink patterns, or analysis insights were discovered (not in references):
  - Present all discoveries to the user in the report for review
  - **Do NOT auto-write** to any file, and **never modify** existing reference files
  - After user approval, append confirmed entries to `reference/extended-knowledge.md`
  - `extended-knowledge.md` acts as an external knowledge extension — supplements but never replaces built-in references
  - Whether to merge extended knowledge into main references is the developer's decision
  - Approved entries are auto-loaded alongside built-in references in future analyses

### 6.4 Final Report
- `report.md`: Human-readable with risk overview, per-endpoint details, remediation suggestions
- `report.json`: Machine-readable with full structured data

## 7. Project Structure

```
authscan/
├── .claude-plugin/
│   └── plugin.json                    # Claude Code plugin registration
├── skills/
│   └── authscan/
│       ├── SKILL.md                   # Main entry skill (user-invocable)
│       └── reference/                 # All methodology + knowledge base files
│           ├── recon.md               # Phase 1 methodology
│           ├── endpoint-analysis.md   # Phase 2 methodology (Layer 0-3)
│           ├── output-analysis.md     # Layer 2 detailed methodology
│           ├── report.md              # Phase 3 methodology
│           ├── trust-propagation-rules.md  # 8 core trust rules with examples
│           ├── auth-patterns-java.md  # Java auth patterns (prioritized)
│           ├── auth-patterns-python.md # Python auth patterns (prioritized)
│           ├── auth-patterns-common.md # Cross-language auth patterns
│           ├── datasink-patterns.md   # Data operation patterns
│           ├── mass-assignment-patterns.md # Mass assignment risk patterns
│           └── extended-knowledge.md  # User-confirmed discoveries (append-only)
├── results/                           # Analysis outputs
│   └── {project_name}/
│       ├── recon_context.md
│       ├── endpoints.json
│       ├── {endpoint_name}/
│       │   └── analysis.json
│       ├── report.md
│       └── report.json
└── docs/
    └── 2026-04-05-authscan-design.md  # This document
```

## 8. Skill Design Principles

Each skill follows superpowers conventions:

1. **YAML frontmatter**: `name` + `description`
2. **Single objective per step**: Each analysis step has one clear goal
3. **Explicit input/output**: What to load, what to produce
4. **Rules over judgment**: Trust propagation rules are formal, not vague
5. **Examples are methodology**: Each rule includes concrete code examples
6. **Reference-first**: Always match known patterns before exploring
7. **Self-documenting**: Results include reasoning chains, not just conclusions
8. **Location tracking**: Every function/code reference includes file path + line range for re-verification
