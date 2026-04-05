# Phase 1: Project Reconnaissance

**Goal:** Build a project-level authentication context document (`recon_context.md`) that will be loaded as background for every endpoint analysis.

**Strategy:** Reference-first, then autonomous exploration. Match known patterns before exploring.

## Step 1 — Tech Stack & Project Structure

**Actions:**
1. Search project root for build/config files to identify language and framework:
   - Java: `pom.xml`, `build.gradle`, `build.gradle.kts`
   - Python: `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`
   - Node.js: `package.json`
   - Go: `go.mod`
   - Other: scan for dominant file extensions
2. Identify the web framework from dependencies (Spring Boot, Django, Flask, FastAPI, Express, Gin, etc.)
3. Map project directory layout — identify layers:
   - Entry points: controller / handler / router / view / endpoint directories
   - Business logic: service / usecase / domain directories
   - Data access: dao / repository / mapper / model directories
   - Configuration: config / settings files
4. Locate security/auth configuration files

**Output:** Tech stack section of `recon_context.md`

## Step 2 — Auth Pattern Identification (Core)

**Execution order:**

```
Load auth-patterns-{language}.md (in this same reference directory)
  ↓
For each pattern (by priority order):
  grep/glob for characteristic keywords
  ↓
  Match found → Record: mechanism type, file location, scope, strength
  No match → Continue to next pattern
  ↓
All known patterns checked, still gaps?
  → Load auth-patterns-common.md, repeat
  → Autonomous exploration: search for auth-related keywords
```

**Autonomous exploration keywords** (when known patterns don't match):
```
session, auth, permission, role, token, login, security, principal,
credential, access, privilege, authorize, authenticate, identity,
current_user, get_user, user_id, account, acl, rbac, abac, policy,
middleware, interceptor, filter, guard, decorator, annotation
```

**Identify at each layer:**

| Layer | What to Find | Why It Matters |
|-------|-------------|----------------|
| **Global auth** | Interceptors, middleware, filter chains, AOP aspects | Determines baseline: which endpoints are protected by default |
| **Endpoint-level auth** | Auth annotations, decorators, route-level permission declarations | Determines per-endpoint access control requirements |
| **In-function auth** | Explicit session/permission checks in handler code | Backup auth when global/endpoint-level is absent |
| **Role/permission model** | RBAC tables, role enums, permission structures, policy definitions | Needed for vertical privilege escalation analysis |
| **Trust anchor sources** | Functions/injections that return user-uncontrollable values | Foundation for trust chain analysis |

**For each mechanism found, record:**
- Type (global / endpoint-level / in-function)
- File path and line range
- Scope (which endpoints/paths it covers)
- Strength (login-only / role-check / permission-check / custom)
- How trust anchors are obtained (what function/injection provides the session/user identity)

## Step 3 — Entry Point Enumeration

**Mode A — Full project scan:**

Search for framework-specific endpoint definitions:
- Java Spring: `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@RestController`
- Java JAX-RS: `@Path`, `@GET`, `@POST`
- Python Django: `urlpatterns`, `path()`, `re_path()`, `ViewSet`
- Python Flask: `@app.route`, `@blueprint.route`
- Python FastAPI: `@app.get`, `@app.post`, `@router.get`
- Go Gin: `r.GET`, `r.POST`, `router.Handle`
- Node Express: `app.get`, `app.post`, `router.get`

**Mode B — User-specified endpoints:**
Use the endpoint names/class indices provided by the user.

**For each endpoint, record:**
```json
{
  "endpoint": "/api/users/getInfo",
  "method": "GET",
  "handler": {
    "function": "UserController.getUserInfo",
    "file": "src/main/java/com/example/controller/UserController.java",
    "line_start": 35,
    "line_end": 52
  },
  "global_auth_covered": true,
  "endpoint_auth_declarations": ["@PreAuthorize(\"hasRole('USER')\")"],
  "notes": ""
}
```

## Step 4 — Generate recon_context.md

Assemble all findings into a structured document:

```markdown
# Project Auth Context — {project_name}

## Tech Stack
- Language: {language} {version}
- Framework: {framework} {version}
- Build: {build_tool}

## Project Structure
- Entry points: {path}
- Services: {path}
- Data access: {path}
- Auth config: {path}

## Authentication Mechanisms

### Global Auth
- {mechanism}: covers {scope}, strength: {level}
  - File: {file}:{line_start}-{line_end}
  - Whitelist/exclusions: {paths}

### Endpoint-Level Auth
- {annotation/decorator}: {description}
  - Usage pattern: {example}

### In-Function Auth Patterns
- {pattern}: {description}
  - Example: {code_snippet}

## Trust Anchor Sources
- {source_function}: returns {what}, obtained via {how}
  - File: {file}:{line}
  - Type: session / token / internal_sdk / injection

## Role/Permission Model
- Roles: {list}
- Permission structure: {description}
- Storage: {table/config}

## Entry Points
| Endpoint | Method | Handler | Global Auth | Endpoint Auth |
|----------|--------|---------|-------------|---------------|
| ... | ... | ... | ... | ... |
```

## Step 5 — Record Newly Discovered Patterns (For Later User Review)

If any auth pattern was found through autonomous exploration (not matching any reference pattern):
1. Record the pattern details in `recon_context.md` under a "Discovered Patterns" section
2. **Do NOT write to `learned_patterns/` or any reference file** — these will be presented to the user for review during the Report phase (Phase 3)
3. Include enough detail for the user to evaluate: pattern name, mechanism, search keywords, code example

## Completion Criteria

Reconnaissance is complete when:
- [ ] Tech stack identified
- [ ] All auth layers analyzed (global → endpoint → in-function)
- [ ] Trust anchor sources identified with their obtaining methods
- [ ] Entry points enumerated (all or user-specified)
- [ ] `recon_context.md` written to results directory
- [ ] Newly discovered patterns (if any) recorded in recon_context.md for later user review
