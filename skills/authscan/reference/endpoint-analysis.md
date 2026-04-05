# Phase 2: Per-Endpoint Deep Analysis

**Goal:** For a single endpoint, analyze every parameter's trust relationship with authentication anchors. Produce a structured risk assessment.

**Prerequisites:** Load `recon_context.md` into context before starting.

**MUST READ:** Load `trust-propagation-rules.md` (in this same reference directory) — the 10 trust rules (R1-R10) are the foundation of all judgments in this phase.

**Also load:** `extended-knowledge.md` for any user-confirmed patterns from previous analyses.

## CRITICAL: Per-Endpoint Independence Principle

**Analyze this endpoint as if the attacker calls it directly and independently with arbitrary parameters.**

- Do NOT assume database data is "safe" because another endpoint wrote it with auth
- Do NOT trust data from DB/cache/external just because it "originally came from a trusted endpoint"
- Each input parameter must establish its OWN trust chain to an auth anchor WITHIN THIS endpoint
- A DB query result is only trusted if the query's WHERE clause includes an auth anchor — the data's origin is irrelevant

**Example — the trap to avoid:**
```java
// Endpoint A (has auth): POST /orders → INSERT (id, userId=sessionId, data)
// Endpoint B (we're analyzing): GET /orders/{orderId} → SELECT * WHERE id=orderId
//
// WRONG: "orderId references auth-protected data, so it's safe"
// RIGHT: "orderId has NO trust chain to auth anchor in THIS endpoint → AT RISK"
```

This principle ensures the analysis catches real BOLA vulnerabilities where the auth gap exists precisely between endpoints.

## Layer 0 — Endpoint-Level Auth Check

**Goal:** Before analyzing parameters, determine if the endpoint itself has adequate access control.

**Steps:**

1. **Check global auth coverage:**
   - Is this endpoint covered by the global auth mechanism identified in recon?
   - Is it in a whitelist/exclusion list? (e.g., Spring Security `permitAll()`, Django `@csrf_exempt` without auth)
   - If NOT covered → **CRITICAL: Unauthorized Access Risk**

2. **Check endpoint-level auth declarations:**
   - Does the endpoint have role/permission annotations? (`@PreAuthorize`, `@RequiresRole`, `@permission_required`, etc.)
   - If the endpoint has them, record the required role/permission level.

3. **Assess auth sufficiency:**
   - Endpoint's functionality vs its auth level:
     - Admin/management operation with only login check → **HIGH: Vertical Privilege Escalation Risk**
     - Data modification operation with only read-level permission → **HIGH: Vertical Privilege Escalation Risk**
     - Appropriate role check matching functionality → Pass
   - Use LLM semantic understanding to judge: does the function name, comments, or behavior suggest elevated privileges are needed?

**Output:** `endpoint_level_risks` array in result JSON.

## Layer 0.5 — Trust Anchor Credibility Analysis

**Goal:** Before relying on trust anchors for the entire analysis, verify that the anchors themselves are genuinely uncontrollable by the user. If an anchor is compromised, ALL trust conclusions based on it are invalid (Rule R10).

**Steps:**

1. **Identify how each trust anchor is obtained:**
   - Read the anchor's getter/acquisition code (e.g., `SecurityContext.getCurrentUserId()` implementation)
   - Trace: where does the value ACTUALLY come from at runtime?

2. **Check for credibility-reducing patterns:**

   | Pattern | Risk | Search Keywords |
   |---------|------|-----------------|
   | No-login annotation | Anchor may not exist | `noLoginExchangeUid`, `permitAll`, `@Anonymous`, `@PermitAll` |
   | Token fallback to user input | Anchor becomes user-controlled | `defaultIfEmpty`, `orElse(request.get`, `if (uid == null) uid = request.` |
   | Gray toggle controlling auth strictness | Toggle off → weaker auth path | `grayToggle`, `featureFlag`, `isHit`, `isEnabled` + auth-related toggle names |
   | Multiple auth sources with fallback chain | Weakest source determines credibility | Chained `if/else` blocks for uid resolution |

3. **Assess each anchor source:**

   | Source Type | Credibility |
   |-------------|-------------|
   | Server-side session attribute | ✅ Trusted |
   | JWT/Token claim (signature verified) | ✅ Trusted |
   | Framework auth injection (`@AuthenticationPrincipal`) | ✅ Trusted |
   | RPC framework context (with login state) | ✅ Trusted |
   | Internal gateway header (gateway strips client headers) | ✅ Trusted |
   | Token verification FAILED + fallback to request param | ❌ **Not trusted** |
   | Gray toggle OFF + weaker auth path | ⚠️ **Conditionally not trusted** |
   | Request header/param directly (no validation) | ❌ **Not trusted** |

4. **If any anchor is potentially user-controlled:**
   - Mark as **CRITICAL: Trust Anchor Compromised (R10)**
   - Note: all subsequent R1-R4 conclusions using this anchor are invalidated
   - The endpoint effectively has no reliable auth even if it "looks" like it does

**Output:** Add to `endpoint_level_risks` if compromised anchors found.

## Layer 1 — Input Parameter Forward Trust Chain (Core)

This is the primary analysis. Trace every user-controlled input parameter through the entire function to determine its trust status.

### Step 1: Parameter Expansion & Semantic Classification

1. Read the entry function signature
2. Extract all parameters
3. Classify each parameter by **source**:

| Source Classification | Description | Action |
|----------------------|-------------|--------|
| **User-controlled** | From HTTP request body/query/path/header that user can modify | Needs trust chain analysis |
| **Framework-injected auth** | `@AuthenticationPrincipal`, `HttpSession`, `request.user` | Mark as **trust anchor** immediately |
| **Framework-injected non-auth** | `HttpServletRequest`, `HttpServletResponse` | Ignore unless used to extract auth info |

4. For complex types (DTO/VO/POJO/dict), expand to primitive fields:
   - Read the class/type definition
   - List all fields with their types
   - Each field is a separate analysis target

5. **For each user-controlled parameter, also classify by semantic role:**

| Semantic Role | Indicators (field name / type / usage) | Risk Elevation |
|--------------|----------------------------------------|----------------|
| **Identity parameter** | `userId`, `accountId`, `tenantId`, `ownerId`, `operatorId`, `createdBy`, `memberId` — any param that represents WHO is performing the action or WHO owns the data | **CRITICAL if at_risk** — identity impersonation enables access to ALL of target user's resources |
| **Resource parameter** | `orderId`, `fileId`, `recordId`, `documentId` — any param that identifies WHICH specific resource to access | **HIGH if at_risk** — classic BOLA, scoped to one resource |
| **Filter/scope parameter** | `status`, `type`, `category`, `page`, `limit` — params that filter or scope results | **LOW if at_risk** — typically limited impact |
| **Data parameter** | `name`, `email`, `content`, `description` — params that carry data to be stored | **Check via Layer 3** (mass assignment) |

**Why this matters:** A user-controlled `userId` that reaches a datasink without auth binding is NOT just "horizontal privilege escalation" — it's **identity impersonation**. The attacker can act as ANY user. This is categorically more severe than accessing one record via `orderId`.

**Identity impersonation detection rule:** If a user-controlled parameter with identity semantic role is used WHERE the trust anchor (session userId) SHOULD have been used, flag as **CRITICAL: Identity Impersonation Risk** — the endpoint accepts user identity from input instead of from authentication context.

**MANDATORY: Parameter Completeness Gate**

Before proceeding to Step 2, you MUST:
1. Output a complete parameter table listing EVERY user-controlled parameter
2. Verify: count of classified params == count of fields in the request DTO/function signature
3. If counts don't match → you missed parameters. Go back and re-read the DTO definition.

```
## Parameter Classification Table (MANDATORY — complete this before proceeding)

| # | Parameter | Source | Semantic Role | Risk Base | Classified? |
|---|-----------|--------|---------------|-----------|-------------|
| 1 | applyNo | RequestBody.applyNo | Resource | HIGH | [x] |
| 2 | enterpriseId | RequestBody.enterpriseId | Identity | CRITICAL | [x] |
| 3 | verifyId | RequestBody.verifyId | Resource | HIGH | [x] |

Parameter count check: DTO has 3 fields, table has 3 rows → ✅ Complete
```

**Common trap: analyzing only the "obvious" parameter (like enterpriseId) and skipping others (like applyNo, verifyId).** Every parameter in the request is a potential attack vector. The model MUST classify ALL of them, not just the ones that "look important."

### Step 2: Trust Anchor Identification

1. Load trust anchor sources from `recon_context.md`
2. **First apply Layer 0.5** — verify anchor credibility before proceeding (see above)
3. Search the function body for anchor usage:
   - Direct: `session.getUserId()`, `SecurityContextHolder.getContext()`, `request.user.id`
   - Injected: `@AuthenticationPrincipal User user` → `user.getId()`
   - SDK/Internal: custom auth utility calls identified in recon
4. Mark each anchor variable and its assignment location
5. If Layer 0.5 flagged any anchor as compromised → note that all trust conclusions using it are unreliable

**Record:**
```json
{
  "anchor": "currentUserId",
  "source": "session.getAttribute(\"userId\")",
  "file": "UserController.java",
  "line_start": 48,
  "line_end": 48,
  "type": "session"
}
```

### Step 3: Data Flow Tracking & Trust Determination

**For each user-controlled parameter, trace its complete data flow lifecycle.**

Read every line from the entry function to the return statement(s). At each usage point of the parameter (or its derivatives), apply the trust propagation rules:

```
For parameter P:
  At each usage point:
  │
  ├─ DATASINK (DB query / file op / network call / data modification):
  │   Examine the operation's constraints/conditions:
  │   ├─ Anchor in same constraint → Rule R1: Direct Association → TRUSTED
  │   ├─ P arrived via already-trusted intermediate → Rule R3: Transitive Trust → TRUSTED
  │   ├─ READ operation, result later associated with anchor → Rule R5: Post-Auth Read → TRUSTED
  │   ├─ WRITE operation, no prior anchor association → Rule R6: Post-Auth Write → RISK PENDING
  │   └─ No anchor association anywhere in flow → Rule R8: No Association → AT RISK
  │
  ├─ CONDITION / ASSERTION:
  │   ├─ Compares P (or derivative) with anchor, throws/returns on mismatch
  │   │   → Rule R4: Conditional Guard → TRUSTED (in passing branch only)
  │   ├─ Permission service call: permService.check(anchor, P)
  │   │   → Effective auth → TRUSTED (P is validated against anchor through permission model)
  │   └─ Business logic condition (status check, format validation)
  │       → NOT auth → no trust change
  │
  ├─ FUNCTION CALL (cross-function):
  │   ├─ Check trust conclusion cache for called function
  │   │   → Cache hit → apply cached conclusion
  │   ├─ Within depth limit → follow into called function, continue tracing
  │   └─ Beyond depth limit → mark "NEEDS MANUAL REVIEW"
  │
  └─ ASSIGNMENT / TRANSFORM:
      └─ Rule R7: trust status carries to new variable (transform doesn't create trust)
```

**Critical: Post-Auth Trust (the late-binding pattern)**

Trust association can happen AFTER a datasink. Example:
```java
// Step 1: a3 queries without auth (READ)
d_result = SELECT d1,d2 FROM table WHERE d3=a3;

// Step 2: d1 later associated with auth anchor
filtered = SELECT * FROM x WHERE key=d1 AND userId=sessionId;
return filtered;
```

Analysis: `d_result` is initially untrusted, but `d1` later forms trust association with `sessionId`. By Rule R5 (Post-Auth Read), trust propagates backward: `d1` trusted → `d_result` trusted → `a3`'s read usage is covered.

**BUT for WRITE operations (Rule R6):**
```java
DELETE FROM table WHERE id=a3;  // WRITE already executed
// ... later a3 gets validated against session
```
The DELETE cannot be undone. Mark as **Risk Pending** — the write happened before auth validation.

**Critical: Stored Identity Re-validation (Rule R9)**

When a DB/cache query returns data containing **identity fields** (operatorUserId, createdBy, ownerId), apply R9:

```java
ValidateMO mo = repo.findByOrderNo(orderNo);           // query (trusted or not)
OrderParam param = JSON.parse(mo.getSavedParam());

// R9 CHECK: does code compare stored identity with current user?
if (!currentUserId.equals(param.getOperatorUserId())) { // ← R9 satisfied ✅
    throw new AccessDeniedException();
}
// Without this check → R9 violated → CRITICAL: Identity Impersonation

// Also check: does the code use stored values or user input for business ops?
order.setEnterpriseId(param.getEnterpriseId());         // ✅ stored value
order.setEnterpriseId(request.getEnterpriseId());       // ❌ user input (R8 risk)
```

**R9 detection checklist for DB results (TWO mandatory checks):**
- [ ] **Check 1 (Identity):** Does the result contain identity fields (userId, operatorId, ownerId, createdBy)?
  - [ ] If yes: are those identity fields compared with the current user's trust anchor (`currentUserId == storedIdentity`)?
  - [ ] If no comparison → **CRITICAL: Identity Impersonation**
- [ ] **Check 2 (Stored vs Input):** For each field that exists BOTH in user input AND in stored data (same semantic meaning):
  - [ ] Does the business operation use the stored value or the user's input?
  - [ ] If user input is used when stored value exists → **HIGH: Parameter Substitution Risk**
  - [ ] Example: `order.setEnterpriseId(request.getEnterpriseId())` when `orderParam.getEnterpriseId()` is available
- [ ] **Redundant parameter flag:** Does the endpoint accept a parameter that duplicates a stored field? (design smell — flag for review)

### Step 4: Cross-Function Tracking

When a parameter is passed to another function:

1. **Check cache first:** If this function was analyzed before, reuse its conclusion:
   ```json
   {
     "function": "OrderService.getOrder",
     "param_trust": {"orderId": "at_risk", "userId": "anchor"},
     "return_trust": "depends_on_orderId"
   }
   ```

2. **Follow the call** (within depth limit, default 10):
   - Read the called function's source code
   - Continue the same trust analysis inside it
   - Record the conclusion in the cache

3. **Depth limit exceeded:** Mark as `"needs_manual_review"` with the call chain so far.

4. **Recursion detection:** If a function appears twice in the current call stack → stop, mark as `"circular_call"`.

5. **Priority:** Trace calls that lead to datasinks first. Skip utility functions (logging, formatting, toString) unless they have side effects.

### Step 5: Compile Parameter Risk List

After tracing all parameters, classify each and determine severity using both trust status AND semantic role:

| Status | Criteria | Base Severity |
|--------|----------|---------------|
| **trust_anchor** | Comes from auth source (session, token, injection) | None |
| **trusted** | Established association with anchor via R1-R5 | None |
| **risk_free** | Not used in any datasink, or only echoed back as-is | None |
| **at_risk** | Reaches datasink without anchor association (R8) | See severity table below |
| **risk_pending** | Write operation before auth association (R6) | See severity table below |
| **needs_review** | Exceeded depth limit or circular call | LOW |

**Severity elevation by semantic role** (for `at_risk` and `risk_pending` params):

| Semantic Role | Read Operation | Write Operation | Why |
|--------------|---------------|-----------------|-----|
| **Identity** (userId, accountId, tenantId) | **CRITICAL** | **CRITICAL** | Identity impersonation — attacker acts as ANY user, affects all their resources |
| **Resource** (orderId, fileId, recordId) | **MEDIUM** | **HIGH** | Classic BOLA — scoped to one resource per request |
| **Filter/Scope** (status, type, page) | **LOW** | **MEDIUM** | Usually limited impact, but write can corrupt filtered data sets |
| **Data** (name, content, description) | — | Check Layer 3 | Data params don't cause BOLA but may cause mass assignment |

**Identity impersonation special case:** If a parameter with `identity` semantic role is `at_risk`, AND a trust anchor (session userId) exists but is NOT used where this identity parameter is used, explicitly flag:
```json
{
  "risk_type": "identity_impersonation",
  "detail": "Endpoint accepts userId from input (dto.userId) but session userId (user.getId()) exists and is unused for this operation",
  "severity": "CRITICAL"
}
```

### Step 5.5: Multi-Parameter Combination Analysis

**Trigger:** When 2 or more user-controlled parameters are at_risk.

**Why this step exists:** Individual parameter analysis may show each param as HIGH risk. But when parameters COMBINE (e.g., both used as query conditions, or one locates a record and another controls what's written), the combined risk may be CRITICAL. Analyzing only one parameter and stopping is the #1 cause of missed vulnerabilities.

**Steps:**

1. **Identify combination usage points** — where are multiple at-risk params used together?
   ```java
   // Common pattern: two params combine in a query
   repository.load(enterpriseId, applyNo);  // both user-controlled → combined query
   ```

2. **Assess combined risk:**

   | Combination | Combined Risk | Why |
   |------------|---------------|-----|
   | Identity + Resource | CRITICAL | Locate any record + impersonate identity |
   | Identity + Identity | CRITICAL | Multi-dimensional identity impersonation |
   | Resource + Resource | HIGH | Multi-resource unauthorized access |

3. **Describe the combined attack** — how do the params interact to enable the attack? Each param plays a role:
   - Param A does what? (e.g., "locates the target record")
   - Param B does what? (e.g., "controls which enterprise the account is opened under")
   - Together: "attacker can locate any record AND substitute the enterprise identity"

4. **Check: does the combined query include a trust anchor?**
   - `load(enterpriseId, applyNo)` → no anchor → both params unconstrained → CRITICAL
   - `load(enterpriseId, applyNo, currentUserId)` → anchor present → combination is constrained → lower risk

**Output to analysis.json** as `attack_scenarios` array (see Result Output Format below for the full schema):

- Each scenario MUST include concrete `steps` with `attacker_action` using specific parameter names and realistic values
- `attacker_action` describes what the attacker literally sends or does — write the actual API call, parameter value substitution, or prerequisite action (NOT generic "attacker manipulates param X")
- For multi-phase flows: step 1 = what the legitimate user does that creates the prerequisite; subsequent steps = attacker's actual exploit actions
- `system_behavior` must reference the actual code path, SQL, or external call that executes at each step, with `code_location` pointing to the exact file:line
- Single-param vulnerabilities: generate 1 scenario with 1-2 steps
- Multi-param vulnerabilities: generate a SEPARATE scenario for EACH distinct exploitation path (e.g., "Cross-enterprise hijacking" and "Identity substitution" are different scenarios with different `involved_params`)
- **IMPORTANT:** Generate attack_scenarios during Phase 2 while source code is in context. Do NOT defer to Phase 3.

## Layer 2 — Output Parameter Backward Trust Chain

Read and follow `output-analysis.md` (in this same reference directory) for this layer.

## Layer 3 — Mass Assignment Check (Write Operations Only)

**Trigger:** Only run for endpoints that perform write operations (POST/PUT/PATCH/DELETE, or semantic judgment based on function behavior).

**Steps:**

1. **Identify write target:** What data does this endpoint modify?
   - DB INSERT/UPDATE: which table, which fields?
   - File write: what content?
   - API call to external service: what payload?

2. **Trace input fields to write operation:**
   - Which fields from the user's input DTO reach the write operation?
   - Are all input fields written, or only a subset (field whitelist)?

3. **Identify sensitive fields in the write target:**
   - Permission/role fields: `role`, `permission`, `isAdmin`, `level`, `authority`
   - Identity fields: `userId`, `ownerId`, `createdBy`, `tenantId`
   - Status fields: `status`, `approved`, `verified`, `enabled`, `deleted`
   - Business-critical fields: `price`, `balance`, `credits`, `amount`

4. **Assess risk:**
   - Sensitive field reachable from user input AND no whitelist/filtering → **Mass Assignment Risk**
   - Framework auto-binding (Spring `@ModelAttribute`, Django ModelForm) with no `fields`/`exclude` → **Mass Assignment Risk**
   - Explicit field mapping or DTO with only safe fields → Safe

**Output:** `mass_assignment_risks` array in result JSON.

## Result Output Format

**Design principle:** analysis.json captures **analysis conclusions** — what is at risk, why, where, and how parameters relate to each other. Presentation formatting (attack scenario narratives, remediation code) is generated in Phase 3 from these conclusions.

**Balance:** Include enough data that Phase 3 can generate a detailed report WITHOUT re-reading source code. Don't include presentation formatting (step-by-step tables, tree diagrams).

Each endpoint analysis produces `analysis.json`:

```json
{
  "endpoint": "/api/order/detail",
  "method": "GET",
  "handler": {
    "function": "OrderController.getDetail",
    "file": "src/main/java/com/example/controller/OrderController.java",
    "line_start": 45,
    "line_end": 78,
    "business_function": "Query order detail by orderId — returns full order record to caller"
  },
  "analysis_timestamp": "2026-04-05T10:30:00Z",
  "endpoint_level_risks": [],
  "trust_anchors": [
    {
      "name": "currentUserId",
      "source": "session.getAttribute(\"userId\")",
      "file": "src/main/java/com/example/controller/OrderController.java",
      "line_start": 48,
      "line_end": 48,
      "credibility": "trusted",
      "credibility_reason": null
    }
  ],
  "parameter_risk_list": [
    {
      "param": "orderId",
      "type": "user_controlled",
      "semantic_role": "resource",
      "expanded_from": "RequestParam orderId (Long)",
      "trust_status": "at_risk",
      "trust_rule": "R8",
      "severity": "HIGH",
      "reason": "orderId (user input) flows to OrderDAO.findById() → SELECT WHERE id=orderId. No trust anchor (currentUserId) in query constraint.",
      "exploitation": "Attacker can read any user's order by supplying an arbitrary orderId (e.g., orderId=1001 where 1001 belongs to another user)",
      "flow_path": [
        {
          "step": 1,
          "description": "User input: request.getParameter(\"orderId\") — user-controlled",
          "code": "Long orderId = Long.parseLong(request.getParameter(\"orderId\"))",
          "file": "src/main/java/com/example/controller/OrderController.java",
          "line": 47
        },
        {
          "step": 2,
          "description": "Passed to service without trust anchor",
          "code": "Order order = orderService.getOrder(orderId)",
          "file": "src/main/java/com/example/controller/OrderController.java",
          "line": 52
        },
        {
          "step": 3,
          "description": "Reaches DAO — no anchor in call",
          "code": "return orderDAO.findById(orderId)",
          "file": "src/main/java/com/example/service/OrderService.java",
          "line": 30
        },
        {
          "step": 4,
          "description": "DB query datasink — NO trust anchor in WHERE clause",
          "code": "SELECT * FROM orders WHERE id = ?",
          "file": "src/main/java/com/example/dao/OrderDAO.java",
          "line": 12,
          "is_datasink": true,
          "datasink_type": "read",
          "violation": "R8: No Association — currentUserId exists but absent from query"
        }
      ],
      "affected_datasinks": [
        {
          "operation": "SELECT * FROM orders WHERE id = ?",
          "function": "OrderDAO.findById",
          "file": "src/main/java/com/example/dao/OrderDAO.java",
          "line_start": 12,
          "line_end": 15,
          "op_type": "read"
        }
      ]
    }
  ],
  "output_risk_list": [],
  "mass_assignment_risks": [],
  "attack_scenarios": [
    {
      "title": "Horizontal privilege escalation via orderId enumeration",
      "severity": "HIGH",
      "involved_params": ["orderId"],
      "steps": [
        {
          "step": 1,
          "attacker_action": "Call GET /api/order/detail?orderId=1001 where 1001 belongs to another user",
          "exploited_params": ["orderId"],
          "system_behavior": "System executes SELECT * FROM orders WHERE id=1001, returns victim's order data without ownership check",
          "code_location": "OrderDAO.java:12"
        },
        {
          "step": 2,
          "attacker_action": "Enumerate orderId from 1 to N to harvest all orders in the system",
          "exploited_params": ["orderId"],
          "system_behavior": "Each request returns order data for that orderId regardless of who owns it",
          "code_location": "OrderController.java:52"
        }
      ],
      "impact": "Attacker can read ALL users' order data including sensitive business information",
      "root_cause": "orderId reaches datasink without trust anchor binding (R8)",
      "multi_param_interaction": "Single parameter vulnerability — orderId alone is sufficient for exploitation"
    }
  ],
  "trust_chain_summary": {
    "anchors": [
      {
        "name": "currentUserId",
        "source": "session.getAttribute(\"userId\")",
        "file": "src/main/java/com/example/controller/OrderController.java",
        "line": 48,
        "credibility": "trusted"
      }
    ],
    "trusted_params": [],
    "at_risk_params": ["orderId"],
    "risk_free_params": [],
    "propagation_tree": {
      "currentUserId": {
        "status": "anchor",
        "propagates_to": [],
        "note": "Exists but NOT used in orderId's data flow — this is the root cause"
      },
      "orderId": {
        "status": "at_risk",
        "rule": "R8",
        "chain": "user_input → OrderDAO.findById(orderId) → SELECT WHERE id=? (no anchor)",
        "reaches_datasinks": ["OrderDAO.findById @ src/main/java/com/example/dao/OrderDAO.java:12-15"]
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
  ],
  "cross_function_cache": {}
}
```

**What each field provides to Phase 3 (and user verification):**
- `handler.business_function`: One-sentence description of what the endpoint does in business terms — used in report 业务功能 field
- `analysis_timestamp`: ISO timestamp — used for cache invalidation in multi-endpoint scans
- `trust_anchors[].credibility` + `credibility_reason`: Whether the anchor is trustworthy; reason shown in report when compromised
- `reason`: Technical chain summary (input → flow → datasink → why at risk)
- `exploitation`: Attacker-facing one-liner describing what can be achieved — used in Risk Parameter Overview table "Risk Alone" column
- `flow_path`: **Structured object array** — each hop has `{step, description, code, file, line}`. The `code` field at each step enables Section Key Vulnerable Code to be rendered without re-reading source. `is_datasink` + `violation` flags mark the exact problem point.
- `trust_chain_summary.propagation_tree`: Per-parameter trust status with one-line chain — enables Trust Chain Visualization ASCII tree
- `affected_datasinks`: Exact datasink file:line locations for remediation code
- `functions_analyzed`: All code locations traversed — full call chain for report
- `cross_function_cache`: Cached conclusions for functions already analyzed — prevents re-analysis when the same function appears in multiple endpoints

## Worked Example

Consider this function:
```java
public Result getInfo(Long a1, Long a2, Long a3, Long a4) {
    Long sessionUid = getUserSessionId();                              // line 10: trust anchor
    CResult c = db.query("SELECT c1,c2,c3 FROM t1 WHERE c1=? AND c2=? AND c3=?", a1, a2, sessionUid);  // line 11
    DResult d = db.query("SELECT d1,d2 FROM t2 WHERE d3=?", a3);      // line 12
    EResult e = db.query("SELECT e1,e2 FROM t3 WHERE e3=?", c.getC3()); // line 13
    return new Result(c, d, e, a3);                                    // line 14
}
```

**Analysis walkthrough:**

1. **Anchors:** `sessionUid` from `getUserSessionId()` → trust anchor

2. **a1 (line 11):** Used in query alongside `sessionUid` → **R1: Direct Association → trusted**

3. **a2 (line 11):** Same query, same anchor constraint → **R1: Direct Association → trusted**

4. **c (line 11):** Result from anchor-constrained query → **R2: Derived Trust → all fields (c1,c2,c3) trusted**

5. **a3 (line 12):** Used in query WITHOUT any anchor → Check if result `d` is later anchor-associated...
   - `d` (d1,d2) returned directly at line 14 → no subsequent anchor association
   - **R8: No Association → at_risk**

6. **d (line 12):** Result from untrusted query → **at_risk** (d1, d2 returned to user without auth filtering)

7. **e (line 13):** Query uses `c.getC3()` which is trusted (from step 4) → **R3: Transitive Trust → trusted**

8. **a4:** Not used anywhere → **risk_free**

**Result:**
- Trust anchors: `sessionUid`
- Trusted: `a1`, `a2`, `c`(c1,c2,c3), `e`(e1,e2)
- At risk: `a3`, `d`(d1,d2) — **orderId-type BOLA vulnerability**
- Risk-free: `a4`
- Trust chain: `sessionUid → c(via R1 with a1,a2) → e(via R3 from c.c3)`

## Worked Example 2: Multi-Parameter Attack (Order Confirmation)

This example shows how to analyze and report when MULTIPLE parameters are at-risk and interact.

```java
public OrderConfirmResponse confirmOrder(OrderConfirmRequest request) {
    String currentUserId = SecurityContext.getCurrentUserId();          // line 159: anchor
    OrderValidateMO validateMO = orderRepository.load(
        request.getEnterpriseId(), request.getOrderNo());              // line 163: query
    OrderParam orderParam = JSON.parseObject(
        validateMO.getSavedParam(), OrderParam.class);                 // line 173: parse
    // Missing: currentUserId == orderParam.getOperatorUserId() check  // line 178
    VerifyResult verifyResult = verifyService.completeVerification(
        request.getVerifyId());                                        // line 182: external call
    Order order = new Order();
    order.setOrderNo(request.getOrderNo());                            // line 192
    order.setEnterpriseId(request.getEnterpriseId());                  // line 193: user input!
    order.setOperatorId(orderParam.getOperatorUserId());               // line 194: stored identity
    orderRepository.confirmOrder(order);                               // line 198: write datasink
    return new OrderConfirmResponse(order);                            // line 200
}
```

**Analysis walkthrough:**

1. **Anchor:** `currentUserId` from `SecurityContext.getCurrentUserId()` @ line 159 → trust anchor

2. **request.orderNo** (semantic_role: resource):
   - Used in `orderRepository.load(enterpriseId, orderNo)` @ line 163 → R8: no anchor in query → **at_risk**
   - Also used in `order.setOrderNo()` @ line 192 → flows to INSERT @ line 198 → **at_risk (write)**
   - Risk chain: `user_input → load(enterpriseId, orderNo) → no anchor → AT RISK`

3. **request.enterpriseId** (semantic_role: identity):
   - Used in `orderRepository.load(enterpriseId, orderNo)` @ line 163 → R8: no anchor → **at_risk**
   - Also used in `order.setEnterpriseId(request.getEnterpriseId())` @ line 193 → flows to INSERT → **at_risk (write)**
   - R9 Check 2 VIOLATED: stored value `orderParam.getEnterpriseId()` exists but code uses user input instead
   - Risk chain: `user_input → load() + order.setEnterpriseId() → INSERT → CRITICAL (identity + write + R9 violation)`

4. **request.verifyId** (semantic_role: resource):
   - Used in `verifyService.completeVerification(verifyId)` @ line 182 → external service call with side effect → R6/R8: no anchor → **risk_pending (HIGH)**
   - Risk chain: `user_input → completeVerification() → external side effect → no anchor → RISK PENDING`

5. **validateMO / orderParam** (from DB):
   - Query at line 163 uses only user-controlled params → R8 → result untrusted
   - `orderParam.getOperatorUserId()` is a stored identity field → R9 Check 1: is it compared with `currentUserId`? **NO** → **CRITICAL: Identity Impersonation**
   - Risk chain: `load(user_input, user_input) → untrusted result → operatorUserId NOT verified → used in INSERT`

**Combined Attack Scenarios:**

**Scenario 1: Cross-Enterprise Order Hijacking**
| Step | Attacker Action | Exploited Params | System Behavior | Code Location |
|------|----------------|-----------------|-----------------|---------------|
| 1 | Enterprise A user creates order normally in Phase 1 | — | Stores: orderNo_A, enterpriseId_A, operatorUserId_A | — |
| 2 | Attacker (Enterprise B) obtains orderNo_A | — | — | — |
| 3 | Attacker calls confirmOrder with `orderNo=orderNo_A, enterpriseId=enterpriseId_A` | `orderNo` + `enterpriseId` | Loads Enterprise A's order data (line 163) | OrderRepository.java:load |
| 4 | System writes order with attacker's verifyId, using stored operatorUserId_A | `verifyId` + stored `operatorUserId` | INSERT with wrong operator identity (line 198) | OrderRepository.java:confirmOrder |
| **Result** | **Attacker confirms Enterprise A's order using their own verification, with Enterprise A's operator identity** |

**Scenario 2: Enterprise Identity Substitution**
| Step | Attacker Action | Exploited Params | System Behavior | Code Location |
|------|----------------|-----------------|-----------------|---------------|
| 1 | Attacker creates own order in Phase 1 | — | Stores: orderNo_X, enterpriseId_B, operatorUserId_B | — |
| 2 | Attacker calls confirmOrder with `orderNo=orderNo_X, enterpriseId=enterpriseId_C` (different enterprise!) | `enterpriseId` | Loads own order but writes with enterpriseId_C (line 193) | OrderService.java:193 |
| **Result** | **Order confirmed under wrong enterprise (enterpriseId_C) — R9 Check 2 violation: user input replaces stored value** |

**Multi-Parameter Interaction:**
- `orderNo` + `enterpriseId` together control WHICH record is loaded (both needed for the query)
- `enterpriseId` is additionally used in the WRITE operation, allowing value substitution
- `verifyId` enables completing someone else's verification
- All three params combine to enable a full attack: locate victim's order + substitute enterprise + complete with own verification

**Trust Chain Visualization:**
```
Anchor: currentUserId @ line 159 [EXISTS BUT UNUSED IN DATA FLOW]
  │
  ├─✗ [AT RISK] request.orderNo → load(enterpriseId, orderNo) @ line 163 (R8)
  │     └─✗ validateMO (untrusted result)
  │           └─✗ [CRITICAL] orderParam.operatorUserId — NOT compared with currentUserId (R9 Check 1)
  │                 └─→ order.setOperatorId() → INSERT @ line 198
  │
  ├─✗ [CRITICAL] request.enterpriseId (identity) → load() @ line 163 (R8)
  │     └─✗ order.setEnterpriseId(request.enterpriseId) @ line 193 → INSERT @ line 198
  │           └─ R9 Check 2: stored value orderParam.enterpriseId EXISTS but NOT used
  │
  └─✗ [HIGH] request.verifyId → completeVerification() @ line 182 (R8, side effect)
```

**The two attack scenarios above MUST be written to `attack_scenarios` in analysis.json (generated during Phase 2 while code is in context):**

```json
"attack_scenarios": [
  {
    "title": "Cross-Enterprise Order Hijacking",
    "severity": "CRITICAL",
    "involved_params": ["orderNo", "enterpriseId", "verifyId"],
    "steps": [
      {
        "step": 1,
        "attacker_action": "Enterprise A user creates order normally (Phase 1), producing orderNo_A and enterpriseId_A stored in DB",
        "exploited_params": [],
        "system_behavior": "System stores orderNo_A, enterpriseId_A, operatorUserId_A in order_validate table",
        "code_location": "OrderService.java:128-143"
      },
      {
        "step": 2,
        "attacker_action": "Attacker obtains orderNo_A via interception, log leakage, or enumeration",
        "exploited_params": [],
        "system_behavior": "No system involvement — attacker acquires the prerequisite value",
        "code_location": "—"
      },
      {
        "step": 3,
        "attacker_action": "Attacker calls confirmOrder with orderNo=orderNo_A, enterpriseId=enterpriseId_A, verifyId=attacker_own_verifyId",
        "exploited_params": ["orderNo", "enterpriseId", "verifyId"],
        "system_behavior": "System loads Enterprise A's order record (line 163), completes verification using attacker's verifyId (line 182), writes order under Enterprise A's identity",
        "code_location": "OrderRepository.java:load (line 163), OrderRepository.java:confirmOrder (line 198)"
      }
    ],
    "impact": "Attacker confirms Enterprise A's order using their own verification credential — order is recorded as if Enterprise A's operator performed it",
    "root_cause": "orderNo + enterpriseId query has no trust anchor (R8); operatorUserId from stored record not compared with currentUserId (R9 Check 1)",
    "multi_param_interaction": "orderNo locates the target record; enterpriseId identifies the target enterprise; verifyId substitutes attacker's credential for the victim's — all three combine to complete the attack chain"
  },
  {
    "title": "Enterprise Identity Substitution via enterpriseId Override",
    "severity": "CRITICAL",
    "involved_params": ["enterpriseId"],
    "steps": [
      {
        "step": 1,
        "attacker_action": "Attacker creates their own order in Phase 1 (orderNo_X, enterpriseId_B stored)",
        "exploited_params": [],
        "system_behavior": "System stores attacker's own record normally",
        "code_location": "OrderService.java:128-143"
      },
      {
        "step": 2,
        "attacker_action": "Attacker calls confirmOrder with orderNo=orderNo_X (own order), enterpriseId=enterpriseId_C (different enterprise)",
        "exploited_params": ["enterpriseId"],
        "system_behavior": "System loads attacker's own order (orderNo_X), then writes final order with enterpriseId_C (from user input at line 193) instead of stored enterpriseId_B",
        "code_location": "OrderService.java:193 (account.setEnterpriseId(request.getEnterpriseId()))"
      }
    ],
    "impact": "Order confirmed under wrong enterprise (enterpriseId_C) — attacker can associate their order with any enterprise in the system",
    "root_cause": "R9 Check 2 violation: code uses request.getEnterpriseId() (user input) instead of orderParam.getEnterpriseId() (stored value)",
    "multi_param_interaction": "Single param exploitation path — only enterpriseId needs to be substituted; orderNo can be attacker's own"
  }
]
```

## Worked Example 3: Python Django DRF — BOLA + Data Leakage

This example shows how to analyze a Python endpoint using Django REST Framework.

```python
# views.py
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]                    # line 12: login required

    def get(self, request, order_id):                         # line 14: entry function
        user = request.user                                   # line 15: trust anchor

        # Fetch order
        order = Order.objects.get(id=order_id)                # line 18: DB query, NO user scope!

        # Fetch payment info for this order
        payment = Payment.objects.filter(order=order).first() # line 21: derived from untrusted order

        # Build response
        serializer = OrderSerializer(order)
        data = serializer.data
        data['payment_method'] = payment.method if payment else None    # line 26
        data['customer_email'] = order.user.email                       # line 27: leaks other user's email!
        return Response(data)                                           # line 28
```

```python
# models.py
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)   # owner
    product = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    method = models.CharField(max_length=50)   # e.g., "credit_card_ending_4242"
    paid_at = models.DateTimeField()
```

**Analysis walkthrough:**

1. **Layer 0:** `permission_classes = [IsAuthenticated]` → login required, but no role check. For a simple order detail view, login-only is adequate. Pass.

2. **Layer 0.5:** `request.user` from DRF `IsAuthenticated` → trust anchor is credible (DRF authentication pipeline).

3. **Parameter table:**

   | # | Parameter | Source | Semantic Role | Risk Base | Classified? |
   |---|-----------|--------|---------------|-----------|-------------|
   | 1 | order_id | URL path `/orders/{order_id}` | Resource | HIGH | [x] |

   Count: 1 URL param. ✅ Complete.

4. **order_id (Resource):**
   - Used in `Order.objects.get(id=order_id)` @ line 18
   - Query constraint: `WHERE id = order_id` — **NO `user` in filter!**
   - `request.user` exists (line 15) but is **NOT used** in the query
   - **R8: No Association → at_risk**
   - Severity: Resource + read = **MEDIUM**

5. **Derived data:**
   - `order` is untrusted (from R8 query) → all its fields are untrusted
   - `payment` at line 21: `Payment.objects.filter(order=order)` — derived from untrusted `order` → untrusted (NOT R3, because `order` itself is untrusted)
   - `order.user.email` at line 27 — accessing the order owner's email. Since `order` could be ANY user's order, this **leaks another user's email** → **Output risk: data leakage**

6. **R9 check:** No stored identity field pattern here (single-stage, not multi-phase). R9 not triggered.

7. **Output analysis (Layer 2):**

   | Return Field | Source | Trust Status |
   |-------------|--------|-------------|
   | `order.*` (serializer fields) | `Order.objects.get(id=order_id)` — untrusted | AT RISK |
   | `payment_method` | `Payment.filter(order=order)` — derived from untrusted | AT RISK |
   | `customer_email` | `order.user.email` — other user's PII from untrusted query | **AT RISK — PII leakage** |

**Trust Chain:**
```
Anchor: request.user @ views.py:15 [EXISTS BUT UNUSED IN QUERY]
  │
  └─✗ [MEDIUM] order_id (URL path) → Order.objects.get(id=order_id) @ views.py:18 (R8)
        └─✗ order (untrusted) → payment (derived untrusted) @ views.py:21
        └─✗ order.user.email → returned to attacker @ views.py:27 (PII leakage)
```

**Fix:**
```python
# Change line 18 from:
order = Order.objects.get(id=order_id)
# To:
order = get_object_or_404(Order, id=order_id, user=request.user)
# This adds trust anchor to the query → R1: Direct Association → trusted
```

---

## Worked Example 4: Vertical Privilege Escalation (Java Spring — BFLA + BOLA)

This example shows how to analyze **vertical privilege escalation** at Layer 0, and how it combines with horizontal BOLA at Layer 1.

```java
// UserAdminController.java
@RestController
@RequestMapping("/api/admin/users")
@PreAuthorize("isAuthenticated()")          // line 8: only login check — no role guard!
public class UserAdminController {

    @DeleteMapping("/{userId}")              // DELETE /api/admin/users/{userId}
    public Result deleteUser(
            @PathVariable Long userId,       // line 13: user-controlled
            HttpServletRequest request) {
        Long operatorId = SecurityUtils.getCurrentUserId(request);  // line 15: trust anchor
        userService.deleteUser(userId);      // line 16: no ownership check, no role check
        return Result.ok();
    }

    @PutMapping("/{userId}/role")            // PUT /api/admin/users/{userId}/role
    public Result updateUserRole(
            @PathVariable Long userId,       // line 21: user-controlled
            @RequestParam String newRole,    // line 22: user-controlled — can set ADMIN!
            HttpServletRequest request) {
        Long operatorId = SecurityUtils.getCurrentUserId(request);  // line 24: trust anchor
        userService.updateRole(userId, newRole);  // line 25: no permission boundary
        return Result.ok();
    }

    @GetMapping                              // GET /api/admin/users
    public Result listUsers(
            @RequestParam(required = false) String department,  // line 30
            @RequestParam(required = false) String role) {      // line 31
        return Result.ok(userService.findAll(department, role)); // line 32: returns all users
    }
}
```

**Analysis walkthrough:**

**Layer 0 — Endpoint-level auth check (KEY for this example):**

- Global auth: Spring Security filter covers all `/api/**` paths → login required ✅
- Endpoint-level annotation: `@PreAuthorize("isAuthenticated()")` @ line 8
- **Auth sufficiency check:**
  - Path: `/api/admin/users` — "admin" in path signals elevated privilege
  - Operations: `deleteUser` (destructive), `updateUserRole` (privilege assignment), `listUsers` (bulk PII access)
  - LLM semantic judgment: all three operations are admin-only by nature
  - `isAuthenticated()` = "is any logged-in user" — insufficient for admin operations
  - **→ HIGH: Vertical Privilege Escalation (BFLA) — any authenticated user can access admin functions**

**Layer 0.5 — Trust anchor credibility:**

- `SecurityUtils.getCurrentUserId(request)` → traces to session attribute set during login
- No noLogin annotation, no token fallback → **✅ Credibility: TRUSTED**

**Layer 1 — Parameter analysis:**

**Parameter table:**

| # | Parameter | Source | Semantic Role | Risk Base | Classified? |
|---|-----------|--------|---------------|-----------|-------------|
| 1 | `userId` (deleteUser) | URL path | Identity | HIGH | ✅ |
| 2 | `userId` (updateUserRole) | URL path | Identity | HIGH | ✅ |
| 3 | `newRole` | Query param | Data (privilege assignment) | HIGH | ✅ |
| 4 | `department` | Query param | Filter | LOW | ✅ |
| 5 | `role` (listUsers) | Query param | Filter | LOW | ✅ |

Count: 5 params. ✅ Complete.

**`userId` in deleteUser (semantic_role: identity):**
- Used in `userService.deleteUser(userId)` @ line 16 → write datasink
- `operatorId` (trust anchor) declared @ line 15 but **never used in the call**
- R8: No Association → **at_risk**
- Severity: Identity + write = **CRITICAL** (any user can delete any user)

**`userId` in updateUserRole (semantic_role: identity):**
- Used in `userService.updateRole(userId, newRole)` @ line 25 → write datasink
- `operatorId` declared @ line 24 but **never used**
- R8: No Association → **at_risk**
- Severity: Identity + write + role assignment = **CRITICAL**

**`newRole` (semantic_role: data — privilege value):**
- Reaches `userService.updateRole(userId, newRole)` @ line 25 → write datasink
- No whitelist / permission boundary check before setting the role
- **→ at_risk**: attacker can set `newRole=ADMIN` to escalate any user's privilege
- Severity: Privilege escalation = **CRITICAL**

**`department`, `role` (filter params):**
- Used in `userService.findAll(department, role)` @ line 32 → read datasink
- No anchor constraint → **at_risk (MEDIUM)**: can enumerate all users by any filter value

**Combined findings:**

There are **two independent vulnerability classes**:
1. **BFLA (Layer 0):** Any authenticated user can call all admin endpoints
2. **BOLA (Layer 1):** Even if BFLA were fixed (role guard added), `userId` in deleteUser/updateUserRole would still need an ownership or scope check

The Layer 0 finding does NOT stop Layer 1 analysis — both must be reported independently.

**Attack Scenarios:**

**Scenario 1: Privilege Escalation (BFLA + newRole)**
| Step | Attacker Action | Exploited Params | System Behavior | Code Location |
|------|----------------|-----------------|-----------------|---------------|
| 1 | Any logged-in user sends `PUT /api/admin/users/999/role?newRole=ADMIN` | `userId=999`, `newRole=ADMIN` | Calls `userService.updateRole(999, "ADMIN")` with no role boundary check | UserAdminController.java:25 |
| **Result** | **Attacker elevates any user (including themselves, userId=own id) to ADMIN** | | | |

**Scenario 2: Unauthorized User Deletion (BFLA + BOLA)**
| Step | Attacker Action | Exploited Params | System Behavior | Code Location |
|------|----------------|-----------------|-----------------|---------------|
| 1 | Any logged-in user sends `DELETE /api/admin/users/100` | `userId=100` | Calls `userService.deleteUser(100)` with no identity or role check | UserAdminController.java:16 |
| **Result** | **Attacker deletes any user's account — both BFLA (should require ADMIN role) and BOLA (no ownership) violated** | | | |

**Trust Chain Visualization:**
```
Layer 0: @PreAuthorize("isAuthenticated()") @ line 8
  ✗ INSUFFICIENT for admin operations — ANY authenticated user can call these endpoints
  → HIGH: Vertical Privilege Escalation (BFLA)

Trust Anchor: operatorId @ SecurityUtils.getCurrentUserId() [EXISTS BUT NEVER USED]
  │
  ├─✗ [CRITICAL] userId (deleteUser, identity)
  │     → userService.deleteUser(userId) @ line 16
  │     ✗ R8: No trust anchor binding — any userId can be deleted
  │
  ├─✗ [CRITICAL] userId (updateUserRole, identity) + newRole
  │     → userService.updateRole(userId, newRole) @ line 25
  │     ✗ R8: No trust anchor binding
  │     ✗ newRole unconstrained — attacker can set "ADMIN"
  │
  └─✗ [MEDIUM] department, role (filter)
        → userService.findAll(department, role) @ line 32
        ✗ R8: No anchor — returns all users matching any filter
```

**`attack_scenarios` for analysis.json:**
```json
"attack_scenarios": [
  {
    "title": "Privilege Escalation via Unauthenticated Admin Endpoint (BFLA)",
    "severity": "CRITICAL",
    "involved_params": ["userId", "newRole"],
    "steps": [
      {
        "step": 1,
        "attacker_action": "Any logged-in user sends PUT /api/admin/users/{own_userId}/role?newRole=ADMIN",
        "exploited_params": ["userId", "newRole"],
        "system_behavior": "userService.updateRole(userId, 'ADMIN') executes with no role boundary — attacker's account becomes ADMIN",
        "code_location": "UserAdminController.java:25"
      }
    ],
    "impact": "Any authenticated user can escalate themselves or others to ADMIN role",
    "root_cause": "Layer 0 BFLA: @PreAuthorize('isAuthenticated()') used on admin controller instead of role-based guard (e.g., hasRole('ADMIN')). Layer 1 BOLA: userId and newRole reach write datasink without trust anchor binding (R8).",
    "multi_param_interaction": "userId selects the target account; newRole specifies the privilege level — together they enable complete privilege assignment without any authorization check"
  }
]
```

**Fix:**
```java
// Fix 1 — Add role guard at class level (addresses BFLA):
@PreAuthorize("hasRole('ADMIN')")          // replaces isAuthenticated()
public class UserAdminController { ... }

// Fix 2 — Add trust anchor binding for destructive operations (addresses BOLA):
@DeleteMapping("/{userId}")
public Result deleteUser(@PathVariable Long userId, HttpServletRequest request) {
    Long operatorId = SecurityUtils.getCurrentUserId(request);
    // Verify operator has permission to delete this specific user
    // (e.g., can only delete users in own department, or require super-admin for cross-dept)
    userService.deleteUserWithAudit(userId, operatorId);
    return Result.ok();
}

// Fix 3 — Whitelist allowed role values (addresses newRole escalation):
private static final Set<String> ALLOWED_ROLES = Set.of("USER", "OPERATOR", "MANAGER");
// Before updateRole: validate newRole is in ALLOWED_ROLES (exclude "ADMIN" for self-service)
```

---

## Worked Example 5: Node.js Express + JWT — Simple BOLA

This example shows how to identify the trust anchor in a JWT-based Node.js/Express endpoint and trace a simple BOLA vulnerability with data leakage.

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

module.exports = function authMiddleware(req, res, next) {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'Unauthorized' });
    const decoded = jwt.verify(token, process.env.JWT_SECRET); // line 7: signature verified
    req.user = decoded;  // line 8: { id, email, role } — set by verified JWT
    next();
};
```

```javascript
// routes/orders.js
const router = require('express').Router();
const authMiddleware = require('../middleware/auth');
const Order = require('../models/Order');
const OrderItem = require('../models/OrderItem');

// GET /api/orders/:orderId
router.get('/:orderId', authMiddleware, async (req, res) => {
    const orderId = req.params.orderId;               // line 9: user-controlled (URL path)
    const currentUserId = req.user.id;               // line 10: trust anchor from JWT

    const order = await Order.findOne({ _id: orderId });         // line 12: NO userId scope!
    if (!order) return res.status(404).json({ error: 'Not found' });

    const items = await OrderItem.find({ orderId: orderId });    // line 15: derived from untrusted

    return res.json({
        orderId: order._id,
        amount: order.amount,
        status: order.status,
        recipientName: order.recipientName,   // line 20: victim's PII
        recipientPhone: order.recipientPhone, // line 21: victim's PII
        items
    });
});
```

**Analysis walkthrough:**

**Layer 0:**
- `authMiddleware` applied to the route → login required ✅
- No role annotation — `GET /api/orders/:orderId` is a standard user operation, login-only is adequate
- Layer 0: **Pass**

**Layer 0.5 — Trust anchor credibility:**
- `req.user.id` set from `jwt.verify(token, JWT_SECRET)` @ middleware line 7
- `jwt.verify()` throws if signature invalid → token cannot be forged
- No fallback path (no `|| req.body.userId` style override)
- **✅ Credibility: TRUSTED**

**Layer 1 — Parameter analysis:**

**Parameter table:**

| # | Parameter | Source | Semantic Role | Risk Base | Classified? |
|---|-----------|--------|---------------|-----------|-------------|
| 1 | `orderId` | URL path `/:orderId` | Resource | MEDIUM | ✅ |

Count: 1 URL path param. ✅ Complete.

**`orderId` (semantic_role: resource):**
- Used in `Order.findOne({ _id: orderId })` @ line 12
- Query filter: `{ _id: orderId }` — **no `userId` field in filter**
- `currentUserId` declared @ line 10 but **absent from the query**
- R8: No Association → **at_risk**
- Severity: Resource + read = **MEDIUM**

**`items` (derived from untrusted `orderId`):**
- `OrderItem.find({ orderId: orderId })` @ line 15
- `orderId` is at_risk → this query is also untrusted (not R3 — source itself is untrusted)
- **at_risk**: attacker-controlled orderId fetches another user's order items

**Layer 2 — Output analysis:**

| Return Field | Source | Trust Status |
|-------------|--------|-------------|
| `orderId`, `amount`, `status` | `Order.findOne({ _id: orderId })` — untrusted | AT RISK |
| `recipientName`, `recipientPhone` | same untrusted order | **AT RISK — PII leakage** |
| `items` | `OrderItem.find({ orderId })` — derived from untrusted | AT RISK |

**`recipientName` / `recipientPhone`** — victim's personal contact information returned to attacker. This elevates the severity from MEDIUM to **HIGH** due to PII exposure.

**Trust Chain Visualization:**
```
Anchor: currentUserId = req.user.id @ routes/orders.js:10 [JWT-verified, TRUSTED]
  │
  └─✗ [MEDIUM→HIGH] orderId (URL path, resource)
        → Order.findOne({ _id: orderId }) @ routes/orders.js:12
        ✗ R8: No Association — currentUserId absent from MongoDB filter
        │
        ├─→ order.recipientName, order.recipientPhone [PII of order owner] → returned @ line 20-21
        │   ✗ Data leakage: victim's contact info exposed to attacker
        │
        └─→ OrderItem.find({ orderId }) @ line 15
            ✗ Derived from untrusted orderId — attacker sees victim's order items
```

**`attack_scenarios` for analysis.json:**
```json
"attack_scenarios": [
  {
    "title": "Order Data and PII Access via orderId Enumeration",
    "severity": "HIGH",
    "involved_params": ["orderId"],
    "steps": [
      {
        "step": 1,
        "attacker_action": "Attacker sends GET /api/orders/507f1f77bcf86cd799439011 where the ObjectId belongs to another user's order",
        "exploited_params": ["orderId"],
        "system_behavior": "Order.findOne({ _id: '507f1f77bcf86cd799439011' }) returns victim's order including recipientName and recipientPhone",
        "code_location": "routes/orders.js:12"
      },
      {
        "step": 2,
        "attacker_action": "Attacker iterates ObjectIds (or guesses from leaked values) to harvest multiple victims' order data",
        "exploited_params": ["orderId"],
        "system_behavior": "Each request returns full order details + PII of the order owner — no rate limiting or ownership check",
        "code_location": "routes/orders.js:12-21"
      }
    ],
    "impact": "Attacker can read any user's order details, order items, recipient name and phone number — PII exposure at scale",
    "root_cause": "orderId reaches MongoDB findOne() without userId binding (R8). currentUserId exists at line 10 but is not included in the query filter.",
    "multi_param_interaction": "Single parameter vulnerability — orderId alone is sufficient for exploitation"
  }
]
```

**Fix:**
```javascript
// Change line 12 from:
const order = await Order.findOne({ _id: orderId });

// To (bind query to trust anchor):
const order = await Order.findOne({ _id: orderId, userId: currentUserId });
// R1: Direct Association — orderId now constrained by trust anchor
// If order doesn't belong to currentUserId, findOne returns null → 404
```
