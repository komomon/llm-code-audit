# Example Flows

## Example 1. Order update review

User request:

Audit whether users can update other users' orders in this service.

Recommended flow:

- main agent defines order update endpoints and services as scope
- scope agent finds routes, handlers, service methods, and repositories
- authz mapper agent checks login, role, owner, and tenant gates
- code-path agent traces `order_id` from request to mutation
- access-control-hypothesis agent tests for IDOR and horizontal privilege escalation
- evidence agent groups support
- judge agent confirms or rejects
- reporter writes the final report

## Example 2. Admin export review

User request:

Check whether non-admin users can trigger admin export functionality.

Recommended focus:

- role-based checks
- service reuse by public endpoints
- background jobs
- export query scoping

Likely subtype:

- vertical privilege escalation

## Example 3. Multi-tenant billing review

User request:

Review whether one tenant can view or modify another tenant's invoices.

Recommended focus:

- tenant context derivation
- repository query scoping
- list, export, and update endpoints
- shared jobs or caches

Likely subtype:

- tenant-isolation failure

## Example 4. Approval workflow review

User request:

Audit whether refund approvals can be performed without proper authority.

Recommended focus:

- approval endpoints
- workflow transitions
- actor authority checks
- service methods that finalize refunds or approvals

Likely subtype:

- approval-authority-bypass
