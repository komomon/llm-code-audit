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
- [ ] `output_risk_list` populated in analysis.json
