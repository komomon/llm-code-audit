# Access Control Checklist

Use this file when reviewing source code for authorization flaws.

Treat each checklist item as a review prompt, not as an automatic finding.

## 1. Ownership checks

Inspect for:

- login check without resource ownership check
- object fetched by attacker-controlled ID
- update or delete by ID with no owner comparison
- read paths protected differently from write paths
- ownership enforced in one layer but bypassed in another

Evidence to seek:

- `resource.owner_id == current_user.id` or equivalent checks
- repository queries scoped by owner
- service methods receiving user-controlled resource IDs

## 2. Role-based checks

Inspect for:

- admin-only actions missing server-side role validation
- role checks in controllers but not in services
- role checks performed only in UI or client code
- inconsistent role checks across similar endpoints
- fallback logic that treats unknown roles permissively

Evidence to seek:

- explicit role comparisons
- central authorization guards
- missing or bypassable role decorators

## 3. Tenant isolation

Inspect for:

- queries missing tenant filters
- tenant_id trusted from request input
- tenant checks in reads but not writes
- list, export, or search endpoints without tenant scoping
- shared background jobs or caches without tenant partitioning

Evidence to seek:

- repository filters by tenant
- server-side derivation of tenant context
- service methods scoping by tenant before data access

## 4. IDOR patterns

Inspect for:

- predictable object identifiers
- object reads, updates, or deletes by raw ID
- file download or media endpoints using unscoped IDs
- batch endpoints taking arrays of resource IDs
- route parameters passed to repositories without scope checks

Evidence to seek:

- direct object lookup by request ID
- no owner or tenant guard before use

## 5. Vertical privilege escalation

Inspect for:

- low-privilege users reaching admin-only services
- internal helper methods reused by public endpoints
- feature flags or request parameters influencing privilege
- approval functions callable without elevated authority

Evidence to seek:

- mismatched role guard placement
- admin services exposed through non-admin routes
- privileged writes reachable from ordinary handlers

## 6. Approval and workflow authority

Inspect for:

- approve, refund, export, or publish operations missing authority checks
- approval enforced in UI but not server-side
- state transitions allowed without actor validation
- approval token or workflow state trusted from request or session input

Evidence to seek:

- server-side checks tied to actor authority
- workflow transitions validated before mutation

## 7. Batch and async paths

Inspect for:

- bulk updates skipping per-item authorization
- background jobs reusing unsafe service methods
- imports or webhooks mutating resources without actor scope checks

Evidence to seek:

- loops over unvalidated resource IDs
- job handlers lacking ownership or tenant checks

## 8. Common anti-patterns

Inspect for:

- `if current_user:` with no later authorization logic
- object fetch before authz with sensitive data already exposed
- hidden assumptions that middleware always ran
- authorization only in comments or documentation

## 9. Checklist output pattern

When using this checklist, ask the reviewing agent to report:

- which checklist categories were inspected
- which categories had direct evidence
- which categories remain unresolved
- which candidate findings were rejected and why
