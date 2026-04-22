# Vulnerability Checklists

Use this file when selecting what a vulnerability-oriented agent should inspect.

The team template is generic. The checklist should change with the vulnerability
class.

## 1. How to use this file

- Pick the relevant vulnerability class.
- Give the checklist to the vulnerability-hypothesis agent and sometimes the code-reader agent.
- Treat checklist items as review prompts, not automatic findings.
- A checklist item is not a confirmed issue without evidence.

## 2. Broken access control / authorization

Inspect for:

- login checks without resource ownership checks
- role checks without resource-scope checks
- controller-level checks missing in service or data layers
- direct object access by attacker-controlled IDs
- admin-only actions protected only in the frontend
- optional flags such as `is_admin`, `role`, `tenant_id` influenced by request data
- bulk operations that skip per-object authorization
- separate read and write paths where only one side checks authorization
- authorization performed too late, after sensitive state is already read or changed

Common evidence patterns:

- `if current_user:` without a later ownership comparison
- route parameters used directly in database queries
- missing `user_id == resource.owner_id` or equivalent checks
- tenant filters absent from queries

## 3. IDOR / object-level authorization

Inspect for:

- object IDs coming from URL, JSON, form, or query params
- direct fetch/update/delete by ID
- no proof that the resource belongs to the current user or tenant
- predictable or enumerable IDs
- file or media download endpoints returning arbitrary object references

Questions to ask:

- where is the object-owner relationship enforced
- whether the repository query is scoped by user or tenant
- whether reads and writes are both protected

## 4. Authentication bypass

Inspect for:

- endpoints reachable without middleware
- debug or internal routes exposed in production
- trust in headers or cookies without signature verification
- authentication checks present in some code paths but skipped in others
- fallback code that treats missing auth context as trusted

Common evidence patterns:

- direct route registration without auth middleware
- `if not user: continue` or permissive fallback behavior
- user identity sourced from untrusted headers

## 5. Multi-tenant isolation failures

Inspect for:

- tenant_id provided by the client and trusted directly
- queries missing tenant scoping
- admin helpers reused in non-admin flows
- cache keys or background jobs lacking tenant partitioning
- cross-tenant search or export functionality

Common evidence patterns:

- queries filtered only by object ID
- service methods accepting tenant identifiers from request data
- cross-tenant listing endpoints without server-side restriction

## 6. Injection flaws

Inspect for:

- string concatenation into SQL, shell, template, or query languages
- user input entering interpreters or command execution
- insufficient parameterization
- dangerous dynamic evaluation features

Subclasses to consider:

- SQL injection
- command injection
- template injection
- NoSQL injection
- LDAP injection

Evidence to seek:

- query strings built with f-strings or concatenation
- shell commands with unsanitized user parameters
- eval-like behavior

## 7. SSRF

Inspect for:

- user-controlled URLs fetched by the server
- redirect-following behavior
- metadata service or internal network access
- insufficient allowlists or protocol restrictions
- webhook, import, crawler, or preview features

Evidence to seek:

- HTTP client calls with request-sourced URLs
- no host validation, protocol validation, or DNS/IP restrictions

## 8. File handling and path traversal

Inspect for:

- filesystem paths built from user input
- download or export endpoints taking arbitrary file names
- archive extraction without path normalization
- upload processing that trusts file names or extensions

Evidence to seek:

- direct joins with user input
- no canonicalization or traversal guard

## 9. Deserialization and unsafe execution

Inspect for:

- deserialization of untrusted data
- dynamic plugin loading from user-controlled input
- unsafe YAML, pickle, or object decoding
- reflection or code loading based on request values

Evidence to seek:

- use of unsafe loaders
- object rehydration from external input

## 10. Business logic flaws

Inspect for:

- approval steps enforced only in the UI
- sequence-dependent operations with no server-side guard
- limit bypass through repeated or reordered requests
- coupon, refund, balance, quota, or workflow abuse
- trust in client-side computed values

Evidence to seek:

- critical transitions without invariant checks
- missing state validation before high-impact actions

## 11. Checklist output pattern

When using a checklist, ask the agent to return:

- which checklist items were inspected
- which items had direct supporting evidence
- which items remain unresolved
- which candidate findings were rejected

That makes the review process easier to audit later.
