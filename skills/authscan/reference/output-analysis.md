# Layer 2: Output Parameter Backward Trust Chain

**Goal:** For each field in the endpoint's response, trace its data source backward to determine if the returned data is authorized for the requesting user.

**When to run:** After Layer 1 (input trust chain) is complete. Layer 1's trust conclusions feed directly into this analysis.

## Step 1 — Return Value Expansion

1. Identify all return statements in the handler function (and called functions if the return is assembled elsewhere)
2. Identify the response type/structure
3. Expand to primitive fields:
   - For DTO/VO/POJO: list all fields
   - For Map/dict: trace what keys are put in
   - For List/array: trace the element type's fields
   - For wrapper types (ResponseEntity, ApiResponse): unwrap to the actual data

**Record each return field:**
```json
{
  "field": "response.order.paymentInfo.cardLast4",
  "type": "String",
  "return_location": {
    "file": "OrderController.java",
    "line": 67
  }
}
```

## Step 2 — Reverse Source Tracing

For each return field, trace backward: **where did this value come from?**

Follow the assignment chain in reverse until you reach a terminal source:

| Terminal Source | Trust Status | Reasoning |
|----------------|-------------|-----------|
| Trusted query result (R1/R2/R3 from Layer 1) | **Safe** | Data constrained by anchor |
| Post-auth filtered result (R5 from Layer 1) | **Safe** | Data filtered by anchor before return |
| Static variable / constant / config value | **Safe** | Not user-specific, no auth concern |
| Trusted SDK / internal service call | **Safe** | Internal source, user can't influence |
| User input parameter (echoed back) | **Risk-free** | User gets back their own input, no data leak |
| Untrusted query result (R8 from Layer 1) | **At Risk** | Data retrieved without auth constraint |
| Risk-pending operation result (R6) | **Risk Pending** | Side effects already occurred |
| Unknown / can't trace | **Needs Review** | Exceeded analysis depth |

**Cross-reference with Layer 1:** If a return field comes from a query whose parameters were analyzed in Layer 1, directly reuse that trust conclusion. Don't re-analyze.

### Multi-Source Fields

If a return field is assembled from multiple sources:
```java
response.setSummary(order.getName() + " - " + externalData.getInfo());
```
Each source is judged independently. The field is only safe if ALL sources are safe. One untrusted source → the combined field is at risk.

## Step 3 — Information Oracle Risk Assessment

For endpoints that return boolean/enum/status-code responses:

```java
public boolean checkOrderExists(Long orderId) {
    return orderRepo.existsById(orderId);  // true/false based on user-controlled orderId
}
```

**Assessment criteria:**
- Can an attacker enumerate the parameter space to extract information?
  - `existsById(orderId)` with sequential IDs → **Low Risk** (oracle: can enumerate which orders exist)
  - `isValid(formatString)` → **No Risk** (no sensitive data exposed)
- Is the information meaningful?
  - Existence of a record → Low risk (information disclosure)
  - Status of a record → Low risk if status is sensitive
  - Count/statistics → Usually no risk unless segment-specific

**Severity:** Generally LOW — flag but don't alarm. Mark as `"info_oracle"` type.

## Step 3.5 — Parameter Leakage Risk Assessment (Layer 2.5)

**Trigger:** When the analyzed endpoint is part of a multi-stage flow (e.g., Phase 2 of a create → confirm pattern), OR when the endpoint accepts parameters that are typically returned by another endpoint (transNo, verifyId, applyNo, etc.).

**Why this matters:** Even if Phase 2 properly validates parameters, the PREVIOUS phase may have returned these values to the client in plaintext. If an attacker can obtain these values (network interception, log leakage, URL parameters, other API responses), they have the inputs needed to call Phase 2.

**Analysis steps:**

1. **Identify if this endpoint is a "later stage":**
   - Does it accept parameters like `transNo`, `applyNo`, `verifyId`, `confirmCode`, `token` that look like system-generated identifiers from a prior operation?
   - Does the code load stored data using these parameters (multi-stage pattern from datasink-patterns.md Category 11)?

2. **Trace where these parameters originated:**
   - Search for the corresponding "Phase 1" endpoint that generates/returns these values
   - Check: does Phase 1 return them in its HTTP response body? In URL parameters? In headers?
   - If yes → the parameters are exposed to the client and potentially to attackers

3. **Assess leakage + exploitation risk:**

   | Phase 1 Return Method | Leakage Risk | Combined with Phase 2 Auth Gap |
   |----------------------|-------------|-------------------------------|
   | Response body (JSON) | MEDIUM — client-side JS can read, network intercept | If Phase 2 has no ownership check → **HIGH** |
   | URL query parameter | HIGH — browser history, server logs, referrer header | If Phase 2 has no ownership check → **CRITICAL** |
   | URL path parameter | HIGH — same as above | If Phase 2 has no ownership check → **CRITICAL** |
   | HTTP header | LOW — harder to intercept | If Phase 2 has no ownership check → **MEDIUM** |
   | Not returned (server-side only) | NONE — attacker can't obtain | Phase 2 auth gap still matters if value is guessable |

4. **Check predictability of the parameter:**
   - Sequential IDs (auto-increment) → HIGH leakage risk (enumerable)
   - UUID v4 → LOW leakage risk (not guessable, but still interceptable)
   - Timestamp-based → MEDIUM (partially predictable)
   - Cryptographically signed token → LOW (tamper-resistant)

5. **Output assessment:**
   - If Phase 1 returns sensitive identifiers AND Phase 2 doesn't validate ownership → flag as **Parameter Leakage + Authorization Bypass** combined risk
   - Recommend: Phase 1 should minimize returned identifiers; Phase 2 must validate ownership regardless

**Record in output_risk_list:**
```json
{
  "field": "phase1_response.applyNo",
  "risk_type": "parameter_leakage",
  "leakage_source": "Phase 1 response body (JSON)",
  "consumed_by": "Phase 2 confirmAccount endpoint",
  "phase2_validates_ownership": false,
  "combined_severity": "HIGH",
  "recommendation": "Phase 1: sign or encrypt applyNo before returning. Phase 2: validate applyNo belongs to current user."
}
```

## Step 4 — Compile Output Risk List

```json
{
  "field": "response.order.paymentInfo",
  "trust_status": "at_risk",
  "source_chain": [
    {
      "step": "OrderController.java:67 → return orderDetail",
      "value": "orderDetail.paymentInfo"
    },
    {
      "step": "OrderService.java:34 → orderDetail = orderRepo.findById(orderId)",
      "value": "from untrusted query (orderId is at_risk per Layer 1)"
    }
  ],
  "trust_rule": "R8 (inherited from Layer 1 input analysis)",
  "reason": "paymentInfo comes from query constrained only by at_risk orderId",
  "severity": "HIGH"
}
```

## Completion Criteria

- [ ] All return fields expanded and traced to terminal sources
- [ ] Each field's trust status determined by cross-referencing Layer 1 or independent backward tracing
- [ ] Multi-source fields checked for ALL-safe condition
- [ ] Oracle risk assessed for boolean/enum returns
- [ ] Parameter leakage assessed for multi-stage flow endpoints (Layer 2.5)
- [ ] `output_risk_list` populated in analysis.json
