# IDOR Checklist

Use this file when auditing object-level authorization paths.

Treat each item as a review prompt, not as an automatic finding.

## 1. Input parameters

Inspect for:

- route-controlled object IDs
- query-controlled selectors
- JSON fields carrying object identifiers
- lists of resource IDs in batch APIs
- file or document IDs in download endpoints

## 2. Trusted identity context

Inspect for:

- authenticated user id
- account id
- tenant id
- role context
- session-derived ownership information

## 3. Input/auth relation

Inspect for:

- comparisons between object id and owner-scoped lookup
- repository filters that include actor or tenant scope
- service-layer checks that bind object selection to trusted identity
- joins or predicates that narrow the object set to the caller

## 4. Output/auth relation

Inspect for:

- objects returned directly after unscoped lookup
- serializers or response builders with no ownership guard
- mutations performed after unscoped fetch
- downloads or exports returned after id-only lookup

## 5. Common weak patterns

Inspect for:

- authentication without object-level authorization
- `find_one({"id": object_id})` with no owner or tenant filter
- direct serialization of fetched objects
- update or delete after unscoped retrieval

## 6. Confidence blockers

Watch for:

- hidden decorators or policies not provided
- repository wrappers not shown
- tenant semantics missing from the data model
- serializers or helpers missing from the artifacts
