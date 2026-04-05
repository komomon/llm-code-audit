# Phase 2: Per-Endpoint Deep Analysis

**Goal:** For a single endpoint, analyze every parameter's trust relationship with authentication anchors. Produce a structured risk assessment.

**Prerequisites:** Load `recon_context.md` into context before starting.

**MUST READ:** Load `trust-propagation-rules.md` (in this same reference directory) — the 8 trust rules are the foundation of all judgments in this phase.

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

**Record:**
```json
{
  "param": "orderRequest.userId",
  "type": "user_controlled",
  "semantic_role": "identity",
  "expanded_from": "OrderRequest orderRequest → userId (Long)",
  "source": "RequestBody",
  "note": "Identity parameter from user input — should come from session"
}
```
```json
{
  "param": "orderRequest.orderId",
  "type": "user_controlled",
  "semantic_role": "resource",
  "expanded_from": "OrderRequest orderRequest → orderId (Long)",
  "source": "RequestBody"
}
```

### Step 2: Trust Anchor Identification

1. Load trust anchor sources from `recon_context.md`
2. Search the function body for anchor usage:
   - Direct: `session.getUserId()`, `SecurityContextHolder.getContext()`, `request.user.id`
   - Injected: `@AuthenticationPrincipal User user` → `user.getId()`
   - SDK/Internal: custom auth utility calls identified in recon
3. Mark each anchor variable and its assignment location

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

Each endpoint analysis produces `analysis.json`:

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
  "analysis_timestamp": "2026-04-05T10:30:00Z",
  "endpoint_level_risks": [],
  "trust_anchors": [
    {
      "name": "currentUserId",
      "source": "session.getAttribute(\"userId\")",
      "file": "OrderController.java",
      "line_start": 48,
      "line_end": 48
    }
  ],
  "parameter_risk_list": [
    {
      "param": "orderId",
      "type": "user_controlled",
      "expanded_from": "RequestParam orderId (Long)",
      "trust_status": "at_risk",
      "trust_rule": "R8",
      "reason": "orderId used in SELECT ... WHERE id=orderId without session binding",
      "affected_datasinks": [
        {
          "operation": "SELECT * FROM orders WHERE id = ?",
          "function": "OrderDAO.findById",
          "file": "src/main/java/com/example/dao/OrderDAO.java",
          "line_start": 12,
          "line_end": 15,
          "op_type": "read"
        }
      ],
      "severity": "HIGH"
    }
  ],
  "output_risk_list": [],
  "mass_assignment_risks": [],
  "trust_chain_summary": {
    "anchors": ["currentUserId @ OrderController.java:48"],
    "trusted_params": [],
    "at_risk_params": ["orderId"],
    "risk_free_params": [],
    "propagation_tree": {}
  },
  "functions_analyzed": [
    {
      "function": "OrderController.getDetail",
      "file": "src/main/java/com/example/controller/OrderController.java",
      "line_start": 45,
      "line_end": 78,
      "role": "entry_function"
    }
  ],
  "cross_function_cache": {}
}
```

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
