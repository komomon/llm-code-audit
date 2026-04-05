# DataSink Patterns Reference

DataSinks are operations where user-controlled parameters cause real impact. When these operations lack authorization, actual damage occurs — data leaks, unauthorized modifications, or unintended side effects.

**Every datasink reached by a user-controlled parameter needs a trust chain to an authentication anchor.**

---

## Category 1: Database Operations (Highest Priority)

### 1.1 Read Operations (SELECT / Query / Find)
**Risk type:** Unauthorized data access (BOLA read)
**Post-auth allowed:** Yes (R5 — read results can be filtered before return)

| Language | Framework | Patterns |
|----------|-----------|----------|
| Java | JDBC | `executeQuery`, `PreparedStatement.execute` |
| Java | JPA/Hibernate | `EntityManager.find`, `createQuery`, `createNativeQuery`, `CriteriaQuery` |
| Java | Spring Data | `Repository.findById`, `findBy*`, `findAll`, `@Query` |
| Java | MyBatis | `<select>`, `@Select`, `selectOne`, `selectList` |
| Java | JdbcTemplate | `queryForObject`, `queryForList`, `query` |
| Python | Django ORM | `objects.get`, `.filter`, `.all`, `.exclude`, `.values`, `.raw` |
| Python | SQLAlchemy | `session.query().filter`, `select()`, `.get`, `.first`, `.all` |
| Python | Tortoise | `.filter`, `.get`, `.all`, `.first` |
| Python | pymongo | `find_one`, `find`, `aggregate` |
| Python | Raw SQL | `cursor.execute("SELECT ...")` |

### 1.2 Write Operations (INSERT / UPDATE / DELETE)
**Risk type:** Unauthorized data modification (BOLA write) — **higher severity**
**Post-auth NOT sufficient:** R6 applies — write is irreversible

| Language | Framework | Patterns |
|----------|-----------|----------|
| Java | JDBC | `executeUpdate`, `executeBatch` |
| Java | JPA | `persist`, `merge`, `remove`, `flush` |
| Java | Spring Data | `save`, `saveAll`, `delete`, `deleteById`, `deleteAll` |
| Java | MyBatis | `<insert>`, `<update>`, `<delete>`, `@Insert`, `@Update`, `@Delete` |
| Java | JdbcTemplate | `update`, `batchUpdate` |
| Python | Django ORM | `.save()`, `.delete()`, `.update()`, `.create()`, `bulk_create`, `bulk_update` |
| Python | SQLAlchemy | `session.add`, `session.delete`, `session.commit`, `.update()` |
| Python | pymongo | `insert_one`, `update_one`, `delete_one`, `replace_one`, `bulk_write` |
| Python | Raw SQL | `cursor.execute("INSERT/UPDATE/DELETE ...")` |

---

## Category 2: File System Operations

### 2.1 File Read / Download
**Risk type:** Unauthorized file access, sensitive data exposure
**Post-auth allowed:** Yes (R5)

| Language | Patterns |
|----------|----------|
| Java | `FileInputStream`, `Files.readAllBytes`, `Files.readString`, `BufferedReader`, `FileReader`, `Path.of`, `ResourceLoader.getResource` |
| Java | `StreamingResponseBody`, `InputStreamResource` (file download endpoints) |
| Python | `open(path, 'r')`, `Path.read_text()`, `pathlib`, `os.path`, `shutil.copy` |
| Python | `FileResponse`, `StreamingResponse`, `send_file`, `send_from_directory` |

### 2.2 File Write / Upload / Delete
**Risk type:** Unauthorized file creation/modification/deletion
**Post-auth NOT sufficient:** R6 applies

| Language | Patterns |
|----------|----------|
| Java | `FileOutputStream`, `Files.write`, `Files.copy`, `Files.move`, `Files.delete`, `File.createNewFile` |
| Java | `MultipartFile.transferTo`, `Part.write` (file upload) |
| Python | `open(path, 'w')`, `Path.write_text()`, `shutil.move`, `shutil.rmtree`, `os.remove`, `os.unlink` |
| Python | `UploadFile.read()` + save (FastAPI), `request.FILES` (Django) |

---

## Category 3: Network / External Service Calls

### 3.1 Outbound HTTP Requests
**Risk type:** SSRF, unauthorized actions on external services
**Write/side-effect calls → R6 applies**

| Language | Patterns |
|----------|----------|
| Java | `RestTemplate.getForObject/postForEntity/exchange`, `WebClient.get/post`, `HttpClient.send`, `HttpURLConnection`, `OkHttpClient` |
| Java | `FeignClient` interface methods (annotated with `@GetMapping`, `@PostMapping`) |
| Python | `requests.get/post/put/delete`, `httpx.get/post`, `aiohttp.ClientSession`, `urllib.request.urlopen` |

### 3.2 Internal RPC / Microservice Calls
**Risk type:** Unauthorized cross-service operations

| Language | Patterns |
|----------|----------|
| Java | Dubbo `@Reference` service calls, gRPC `stub.method()`, Spring Cloud OpenFeign |
| Python | gRPC `stub.Method()`, `httpx` calls to internal services, Nameko RPC |

### 3.3 Email / SMS / Notification Sending
**Risk type:** Unauthorized communication, spam, information leakage via notifications
**R6 applies:** Sent messages cannot be recalled

| Language | Patterns |
|----------|----------|
| Java | `JavaMailSender.send`, `SimpleMailMessage`, `MimeMessageHelper`, SMS SDK calls |
| Python | `send_mail` (Django), `smtplib`, `boto3.client('ses')`, Twilio SDK, notification service calls |

---

## Category 4: Cache Operations

### 4.1 Cache Read
**Risk type:** Reading other users' cached data

| Language | Patterns |
|----------|----------|
| Java | `RedisTemplate.opsForValue().get`, `@Cacheable`, `CacheManager.getCache`, `Jedis.get` |
| Python | `cache.get` (Django), `redis.get`, `aioredis`, `cachetools` |

**Auth concern:** If cache key is `"order:{orderId}"` and orderId is user-controlled without auth, any user can read other users' cached order data.

### 4.2 Cache Write / Delete
**Risk type:** Cache poisoning, evicting other users' cache

| Language | Patterns |
|----------|----------|
| Java | `RedisTemplate.opsForValue().set`, `@CachePut`, `@CacheEvict`, `Jedis.set/del` |
| Python | `cache.set`, `cache.delete` (Django), `redis.set`, `redis.delete` |

---

## Category 5: Search Engine / NoSQL Operations

### 5.1 Elasticsearch
**Risk type:** Unauthorized search/data access

| Language | Patterns |
|----------|----------|
| Java | `RestHighLevelClient.search`, `ElasticsearchOperations.search`, `ElasticsearchRepository` |
| Python | `elasticsearch.search`, `elasticsearch_dsl`, `AsyncElasticsearch` |

### 5.2 MongoDB (beyond basic CRUD)
**Risk type:** Unauthorized aggregation/analysis

| Language | Patterns |
|----------|----------|
| Java | `MongoTemplate.find/aggregate`, `MongoRepository` |
| Python | `collection.aggregate`, `mongoengine` queries |

---

## Category 6: Message Queue / Event Publishing

**Risk type:** Unauthorized event trigger, data injection into processing pipelines
**R6 applies:** Published messages trigger downstream processing

| Language | Patterns |
|----------|----------|
| Java | `KafkaTemplate.send`, `RabbitTemplate.convertAndSend`, `JmsTemplate.send`, `StreamBridge.send` |
| Python | `celery.send_task`, `channel_layer.send` (Django Channels), `pika.basic_publish`, `aiokafka.send` |

---

## Category 7: Session / Auth State Manipulation

**Risk type:** Session hijacking, privilege escalation via state manipulation
**R6 applies:** State changes are immediate

| Language | Patterns |
|----------|----------|
| Java | `session.setAttribute`, `SecurityContextHolder.setContext`, `Authentication.setAuthorities` |
| Python | `request.session[key] = value`, `login(request, user)`, `session.modified = True` |

**Auth concern:** If user-controlled input can influence session attributes or auth state, that's a critical vulnerability.

---

## Category 8: Template Rendering / Response Assembly

### 8.1 Server-Side Template Rendering
**Risk type:** Unauthorized data exposure through rendered pages

| Language | Patterns |
|----------|----------|
| Java | `ModelAndView`, `model.addAttribute`, Thymeleaf `th:text`, JSP `${var}`, Freemarker |
| Python | `render(request, template, context)`, Jinja2 `render_template`, Mako |

**Auth concern:** If the template context includes data fetched without auth, the rendered page leaks unauthorized data.

### 8.2 Export / Report Generation
**Risk type:** Bulk data export without auth filtering

| Language | Patterns |
|----------|----------|
| Java | `POI` (Excel), `iText`/`OpenPDF` (PDF), `CSVWriter`, `StreamingResponseBody` for large exports |
| Python | `openpyxl`, `xlsxwriter`, `reportlab`, `csv.writer`, `pandas.to_excel/to_csv` |

---

## Category 9: Redirect / URL Construction

**Risk type:** Open redirect, parameter tampering in redirect URLs

| Language | Patterns |
|----------|----------|
| Java | `response.sendRedirect(url)`, `RedirectView`, `redirect:` prefix in Spring MVC |
| Python | `redirect(url)`, `HttpResponseRedirect(url)`, `RedirectResponse(url)` |

**Auth concern:** If redirect URL contains user-controlled parameters that reference resources, the target endpoint must also have auth.

---

## Category 10: Process / Command Execution

**Risk type:** Unauthorized system operations (overlaps with command injection, but auth dimension exists too)

| Language | Patterns |
|----------|----------|
| Java | `Runtime.exec`, `ProcessBuilder`, `Process` |
| Python | `subprocess.run/call/Popen`, `os.system`, `os.popen` |

**Auth concern:** If the command or its arguments are derived from user input, and the operation is privileged (e.g., system administration), lack of auth is critical.

---

## Category 11: Multi-Stage Operations (Cross-Phase Identity Risk)

**Risk type:** Cross-stage identity impersonation (R9)
**Severity:** CRITICAL

**Pattern:** A business flow split into multiple API calls where Phase 1 stores user identity and Phase 2 uses it.

**Recognition keywords:** `validate`, `confirm`, `complete`, `verify`, `approve`, `finalize`, `phase`, `stage`, `step1/step2`

| Scenario | Phase 1 | Phase 2 | Risk |
|----------|---------|---------|------|
| Identity verification | Initiate verification, store operatorUserId | Complete verification, use stored identity | Impersonate original operator |
| Order confirmation | Create order, store creator identity | Confirm order, use stored identity | Confirm another user's order |
| Approval workflow | Submit for approval, store submitter | Approve, use stored submitter | Approve as different user |
| Payment | Create payment record, store payer | Execute payment, use stored payer | Pay as another user |
| Two-factor auth | Start 2FA, store user context | Verify 2FA code, use stored context | Bypass with another user's context |

**Detection steps:**
1. Does this endpoint read stored/persistent data (from DB, cache, message)?
2. Does the stored data contain identity fields (operatorUserId, createdBy, ownerId)?
3. **Does the code verify `currentUserId == storedIdentity`?** (R9 check)
4. Does the code use stored values OR user input for business operations?
5. Can a user call this endpoint independently without calling Phase 1 first?

**Common stored identity field names:**
```
operatorUserId, operatorId, createdBy, createdUserId, initiatorId,
submitterId, requesterId, ownerId, applicantId, handlerId
```

---

## DataSink Summary: Trust Rule Mapping

| DataSink Category | Operation Type | Post-Auth Valid? (R5) | Post-Auth Risk? (R6) | Default Severity |
|-------------------|---------------|----------------------|---------------------|-----------------|
| DB SELECT | Read | Yes | — | MEDIUM |
| DB INSERT/UPDATE/DELETE | Write | — | Yes | HIGH |
| File Read / Download | Read | Yes | — | MEDIUM |
| File Write / Upload / Delete | Write | — | Yes | HIGH |
| HTTP GET (outbound) | Read | Yes | — | MEDIUM |
| HTTP POST/PUT/DELETE (outbound) | Write | — | Yes | HIGH |
| Email / SMS Send | Write (side effect) | — | Yes | HIGH |
| Cache Get | Read | Yes | — | LOW |
| Cache Set / Delete | Write | — | Yes | MEDIUM |
| Search Query | Read | Yes | — | MEDIUM |
| Message Publish | Write (side effect) | — | Yes | HIGH |
| Session Manipulation | Write (state) | — | Yes | CRITICAL |
| Template Render | Read (exposure) | Yes | — | MEDIUM |
| Export Generation | Read (bulk) | Yes | — | MEDIUM |
| Redirect | Read (navigation) | Yes | — | LOW |
| Process Execution | Write (system) | — | Yes | CRITICAL |

## Quick Search Keywords for Finding DataSinks

```
# Database
execute, query, find, select, insert, update, delete, save, persist,
merge, remove, create, destroy, filter, get, all, first, raw,
JdbcTemplate, EntityManager, Repository, @Query, @Select, objects.get

# File
File, Path, open, read, write, upload, download, transfer, stream,
FileInputStream, FileOutputStream, multipart, send_file, UploadFile

# Network
http, request, get, post, put, send, fetch, call, invoke, client,
RestTemplate, WebClient, HttpClient, requests, httpx, FeignClient

# Cache
cache, redis, memcached, get, set, put, evict, Cacheable, CachePut

# Message Queue
kafka, rabbit, jms, send, publish, dispatch, channel, celery, task

# Search
elasticsearch, search, index, aggregate, solr, lucene

# Session
session.set, session.put, setAttribute, SecurityContext, login

# Export
export, download, csv, excel, pdf, report, generate, POI, openpyxl

# Process
exec, system, Process, subprocess, Runtime, popen
```
