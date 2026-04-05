# Cross-Language Authentication Patterns

Patterns that appear across frameworks and languages. Use when language-specific references don't match.

## JWT (JSON Web Token) Authentication

**Search keywords:** `jwt`, `JWT`, `Bearer`, `Authorization`, `token`, `decode`, `verify`, `claims`, `payload`

**Mechanism:** Client sends JWT in `Authorization: Bearer <token>` header. Server validates signature and extracts claims.

**Trust anchor:** Claims from validated token (typically `sub`/`userId`, `roles`, `permissions`).

**Check points:**
- Where is the token validated? (middleware/filter/per-request)
- What claims are extracted and used?
- Is the signature properly verified (not just decoded)?

## OAuth2 / OpenID Connect

**Search keywords:** `oauth`, `OAuth2`, `OIDC`, `access_token`, `refresh_token`, `scope`, `client_id`, `authorization_code`, `resource_server`

**Trust anchor:** Token introspection result or JWT claims from the identity provider.

## API Key Authentication

**Search keywords:** `api_key`, `apiKey`, `X-API-Key`, `apikey`

**Mechanism:** Static key identifies the caller. Usually for service-to-service auth.

**Note:** API keys identify the APPLICATION, not the USER. For user-level auth, need additional user context.

## Session-Based Authentication

**Search keywords:** `session`, `sessionId`, `JSESSIONID`, `cookie`, `Set-Cookie`, `session_id`

**Mechanism:** Server stores session state. Client sends session ID via cookie.

**Trust anchor:** Server-side session attributes (userId, roles) — not the session ID itself.

## RBAC (Role-Based Access Control)

**Search keywords:** `role`, `ROLE_`, `hasRole`, `isAdmin`, `is_staff`, `is_superuser`, `permission`, `authority`

**Common structures:**
- Role enum/table: `USER, ADMIN, SUPER_ADMIN`
- User-role mapping: `user_roles` table
- Role-permission mapping: `role_permissions` table

**Auth check patterns:**
- Annotation/decorator: `@RequiresRole("ADMIN")`
- Programmatic: `if (user.hasRole("ADMIN"))`
- Query: `SELECT * FROM user_roles WHERE user_id = ? AND role = ?`

## ABAC (Attribute-Based Access Control)

**Search keywords:** `policy`, `attribute`, `abac`, `casbin`, `OPA`, `open_policy_agent`

**Mechanism:** Access decisions based on attributes of user, resource, action, and environment.

## Microservice Internal Auth

**Search keywords:** `X-Internal`, `X-Forwarded-User`, `X-Request-ID`, `service-to-service`, `internal`, `mTLS`

**Patterns:**
- Gateway sets trusted headers after validating external auth
- Internal services trust gateway-set headers
- mTLS for service identity

**Trust anchors from internal headers:**
```
X-Forwarded-UserId: 12345         → user identity from gateway
X-Internal-Service: order-service  → calling service identity
X-User-Roles: ADMIN,USER          → roles from gateway
```

## Common Trust Anchor Acquisition Patterns

| Pattern | Language-Agnostic Description | Trust Level |
|---------|------------------------------|-------------|
| Session attribute | Server-side session stores user info after login | HIGH |
| JWT claim | Cryptographically signed token claim | HIGH (if signature verified) |
| Framework injection | Framework injects authenticated user object | HIGH |
| Request header (from gateway) | Gateway-set header after auth | HIGH (if gateway is trusted) |
| Request header (from client) | Client-set header | NONE (user-controllable!) |
| Cookie value | Client-sent cookie | LOW (unless server-side session) |
| API key | Static key in header/param | MEDIUM (identifies app, not user) |
| ThreadLocal / Context | Current thread/request stores user after auth | HIGH (if set by auth layer) |
