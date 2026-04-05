# Java Authentication & Authorization Patterns Reference

Patterns ordered by priority. Match earlier patterns first for faster identification. Each pattern includes search keywords for grep/glob.

---

## Priority 1: Framework-Level Global Auth (Check First)

### 1.1 Spring Security FilterChain (Spring Boot 3.x / Spring Security 6.x)

**Search:** `SecurityFilterChain`, `HttpSecurity`, `authorizeHttpRequests`, `authorizeRequests`

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/api/public/**").permitAll()        // whitelist — NO auth
        .requestMatchers("/api/admin/**").hasRole("ADMIN")    // role required
        .requestMatchers("/api/**").authenticated()           // login required
        .anyRequest().denyAll()
    );
    return http.build();
}
```

**Record:** which paths are `permitAll` (these are unprotected), which require roles, what the default rule is.

**Trust anchor:** `SecurityContextHolder.getContext().getAuthentication()`

### 1.2 Spring Security (Legacy WebSecurityConfigurerAdapter, Spring Security 5.x)

**Search:** `WebSecurityConfigurerAdapter`, `configure(HttpSecurity`, `antMatchers`, `mvcMatchers`

```java
@Configuration
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()
            .antMatchers("/public/**").permitAll()
            .antMatchers("/admin/**").hasAuthority("ROLE_ADMIN")
            .anyRequest().authenticated();
    }
}
```

### 1.3 Spring Security WebSecurityCustomizer (Path Ignoring)

**Search:** `WebSecurityCustomizer`, `web.ignoring`, `ignoring().requestMatchers`

**WARNING:** Ignored paths completely bypass the security filter chain — no auth at all.

```java
@Bean
public WebSecurityCustomizer webSecurityCustomizer() {
    return web -> web.ignoring().requestMatchers("/static/**", "/health");
}
```

### 1.4 Spring HandlerInterceptor

**Search:** `HandlerInterceptor`, `preHandle`, `WebMvcConfigurer`, `addInterceptors`, `InterceptorRegistry`

```java
public class AuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String token = request.getHeader("Authorization");
        User user = tokenService.validate(token);
        if (user == null) { response.setStatus(401); return false; }
        request.setAttribute("currentUser", user);  // sets trust anchor
        return true;
    }
}

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new AuthInterceptor())
            .addPathPatterns("/api/**")
            .excludePathPatterns("/api/public/**", "/api/login");  // whitelist
    }
}
```

**Record:** `addPathPatterns` (covered) and `excludePathPatterns` (not covered).

### 1.5 Servlet Filter / OncePerRequestFilter

**Search:** `javax.servlet.Filter`, `jakarta.servlet.Filter`, `OncePerRequestFilter`, `doFilter`, `doFilterInternal`, `FilterRegistrationBean`, `@WebFilter`

```java
@Component
public class AuthFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                     FilterChain chain) throws ServletException, IOException {
        String token = request.getHeader("X-Auth-Token");
        if (!isValid(token)) { response.sendError(401); return; }
        chain.doFilter(request, response);
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return request.getRequestURI().startsWith("/public/");  // whitelist
    }
}
```

### 1.6 Spring Cloud Gateway GlobalFilter / GatewayFilter

**Search:** `GlobalFilter`, `GatewayFilter`, `GatewayFilterFactory`, `RouteLocator`

**Mechanism:** API Gateway level auth. Adds trusted headers after validation.

```java
@Component
public class AuthGlobalFilter implements GlobalFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String token = exchange.getRequest().getHeaders().getFirst("Authorization");
        // validate token → add X-User-Id header for downstream services
        return chain.filter(exchange.mutate()
            .request(r -> r.header("X-User-Id", userId))
            .build());
    }
}
```

### 1.7 Spring WebFlux Security (Reactive)

**Search:** `@EnableWebFluxSecurity`, `ServerHttpSecurity`, `SecurityWebFilterChain`, `ReactiveSecurityContextHolder`

```java
@Bean
public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
    return http.authorizeExchange(exchange -> exchange
        .pathMatchers("/public/**").permitAll()
        .anyExchange().authenticated()
    ).build();
}
```

**Trust anchor:** `ReactiveSecurityContextHolder.getContext()`

---

## Priority 2: Annotation-Level Auth

### 2.1 Spring @PreAuthorize / @PostAuthorize / @PreFilter / @PostFilter

**Search:** `@PreAuthorize`, `@PostAuthorize`, `@PreFilter`, `@PostFilter`, `@EnableMethodSecurity`, `@EnableGlobalMethodSecurity`

**Prerequisite:** `@EnableMethodSecurity` (Spring Security 6) or `@EnableGlobalMethodSecurity` (Spring Security 5) must be present for annotations to work.

```java
@PreAuthorize("hasRole('ADMIN')")                           // role check
public void deleteUser(Long userId) { ... }

@PreAuthorize("hasPermission(#orderId, 'Order', 'READ')")   // object-level permission
public Order getOrder(Long orderId) { ... }

@PreAuthorize("#userId == authentication.principal.id")       // ownership check via SpEL
public UserProfile getProfile(Long userId) { ... }

@PostAuthorize("returnObject.userId == authentication.principal.id")  // check AFTER execution
public Order getOrder(Long orderId) { ... }

@PreFilter("filterObject.ownerId == authentication.principal.id")   // filter input collection
public void batchDelete(List<Item> items) { ... }

@PostFilter("filterObject.userId == authentication.principal.id")   // filter output collection
public List<Order> getOrders() { ... }
```

### 2.2 JSR-250 Annotations (@RolesAllowed, @DenyAll, @PermitAll)

**Search:** `@RolesAllowed`, `@DenyAll`, `@PermitAll`, `javax.annotation.security`, `jakarta.annotation.security`

```java
@RolesAllowed({"ADMIN", "MANAGER"})
public void manageUsers() { ... }

@PermitAll
public String healthCheck() { ... }

@DenyAll
public void internalOnly() { ... }
```

### 2.3 Spring @Secured

**Search:** `@Secured`

```java
@Secured("ROLE_ADMIN")
public void adminOperation() { ... }

@Secured({"ROLE_USER", "ROLE_ADMIN"})
public List<Item> listItems() { ... }
```

### 2.4 Apache Shiro Annotations

**Search:** `@RequiresRoles`, `@RequiresPermissions`, `@RequiresAuthentication`, `@RequiresUser`, `@RequiresGuest`, `org.apache.shiro`

```java
@RequiresAuthentication                              // must be logged in
@RequiresRoles("admin")                              // role check
@RequiresPermissions("user:delete")                  // permission check
@RequiresPermissions(value={"order:read","order:write"}, logical=Logical.AND)  // combined
public void deleteUser(Long userId) { ... }
```

**Trust anchor:** `SecurityUtils.getSubject().getPrincipal()`, `SecurityUtils.getSubject().getSession()`

### 2.5 Custom Auth Annotations (Very Common in Enterprise Codebases)

**Search:** Look for custom annotations on controller methods: `@Auth`, `@LoginRequired`, `@Permission`, `@CheckRole`, `@Authorized`, `@AuthCheck`, `@RequireLogin`, `@NeedPermission`, `@AccessControl`

**Identification steps:**
1. Find the annotation definition (`@interface`)
2. Find the processor — could be:
   - **AOP Aspect** (`@Aspect` + `@Around`/`@Before` with `@annotation(xxx)` pointcut)
   - **HandlerInterceptor** that reads annotations via `HandlerMethod`
   - **ArgumentResolver** that resolves auth context
   - **Filter** that checks method annotations

**Pattern A: Custom Annotation + AOP @Around**
```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RequirePermission {
    String value();
}

@Aspect
@Component
public class PermissionAspect {
    @Around("@annotation(perm)")
    public Object checkPermission(ProceedingJoinPoint pjp, RequirePermission perm) throws Throwable {
        String userId = SecurityContext.getCurrentUserId();
        if (!permissionService.hasPermission(userId, perm.value())) {
            throw new AccessDeniedException("No permission: " + perm.value());
        }
        return pjp.proceed();
    }
}
```

**Pattern B: Custom Annotation + AOP @Before**
```java
@Aspect
@Component
public class AuthAspect {
    @Before("@annotation(auth)")
    public void checkAuth(JoinPoint jp, AuthCheck auth) {
        // validate before method execution
        if (!isAuthorized(auth.role())) {
            throw new UnauthorizedException();
        }
    }
}
```

**Pattern C: Custom Annotation + HandlerInterceptor**
```java
public class AuthAnnotationInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (handler instanceof HandlerMethod) {
            HandlerMethod method = (HandlerMethod) handler;
            RequireLogin annotation = method.getMethodAnnotation(RequireLogin.class);
            if (annotation != null) {
                // Check login status
                if (getCurrentUser(request) == null) {
                    response.setStatus(401);
                    return false;
                }
            }
            RequireRole roleAnnotation = method.getMethodAnnotation(RequireRole.class);
            if (roleAnnotation != null) {
                // Check role
            }
        }
        return true;
    }
}
```

**Pattern D: Custom Annotation + HandlerMethodArgumentResolver**
```java
@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
public @interface CurrentUser {}

public class CurrentUserResolver implements HandlerMethodArgumentResolver {
    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return parameter.hasParameterAnnotation(CurrentUser.class);
    }

    @Override
    public Object resolveArgument(MethodParameter parameter, ...) {
        return SecurityContext.getCurrentUser();  // returns trust anchor
    }
}

// Usage:
@GetMapping("/profile")
public Profile getProfile(@CurrentUser User user) {
    return profileService.get(user.getId());  // user.getId() is trust anchor
}
```

---

## Priority 3: In-Function Auth (Explicit Code Checks)

### 3.1 SecurityContextHolder (Spring Security)

**Search:** `SecurityContextHolder`, `getAuthentication`, `getPrincipal`, `UserDetails`, `SecurityContext`

```java
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
Long userId = ((UserDetailsImpl) auth.getPrincipal()).getId();
// userId is trust anchor

// Also check for:
String username = auth.getName();
Collection<? extends GrantedAuthority> authorities = auth.getAuthorities();
boolean isAdmin = auth.getAuthorities().stream()
    .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
```

### 3.2 @AuthenticationPrincipal / @CurrentUser Parameter Injection

**Search:** `@AuthenticationPrincipal`, `@CurrentUser`, `@LoginUser`, `@AuthUser`, `@CurrentAccount`

```java
@GetMapping("/orders")
public List<Order> getOrders(@AuthenticationPrincipal UserDetails user) {
    return orderRepo.findByUserId(user.getId());  // user.getId() is trust anchor
}
```

### 3.3 HttpSession

**Search:** `HttpSession`, `session.getAttribute`, `getSession`, `setAttribute`

```java
HttpSession session = request.getSession();
Long userId = (Long) session.getAttribute("userId");
String role = (String) session.getAttribute("userRole");
// userId, role are trust anchors
```

### 3.4 HttpServletRequest Attributes (Set by Interceptor/Filter)

**Search:** `request.getAttribute`, `setAttribute`, `RequestContextHolder`

```java
// Set by interceptor:  request.setAttribute("currentUser", user);
// Retrieved in handler:
User user = (User) request.getAttribute("currentUser");
Long userId = user.getId();  // trust anchor IF set by auth interceptor
```

### 3.5 ThreadLocal / RequestContext / UserContext Pattern

**Search:** `ThreadLocal`, `UserContext`, `RequestContext`, `SecurityContext`, `LoginContext`, `CurrentUserHolder`

```java
public class UserContext {
    private static final ThreadLocal<UserInfo> HOLDER = new ThreadLocal<>();
    public static UserInfo getCurrentUser() { return HOLDER.get(); }
    public static Long getCurrentUserId() { return HOLDER.get().getId(); }
}
// Set in filter/interceptor, used throughout request lifecycle
// UserContext.getCurrentUserId() is trust anchor
```

### 3.6 JWT Token Parsing

**Search:** `Jwts.parser`, `JWT`, `JwtUtil`, `TokenUtil`, `Claims`, `jjwt`, `jose4j`, `nimbus-jose`, `io.jsonwebtoken`

```java
Claims claims = Jwts.parserBuilder()
    .setSigningKey(secretKey)
    .build()
    .parseClaimsJws(token)
    .getBody();
Long userId = claims.get("userId", Long.class);
List<String> roles = claims.get("roles", List.class);
// userId, roles are trust anchors (from validated JWT)
```

### 3.7 Explicit Ownership / Permission Check in Code

**Search:** `equals`, `==` comparisons involving user ID/session and entity owner fields; `hasPermission`, `hasAccess`, `canAccess`, `checkAccess`, `isOwner`, `checkPermission`

```java
// Ownership check (R4 conditional guard):
Order order = orderRepo.findById(orderId).orElseThrow();
if (!order.getUserId().equals(currentUserId)) {
    throw new AccessDeniedException("Not your order");
}

// Permission service check:
if (!permissionService.hasAccess(currentUserId, resourceId, "READ")) {
    throw new ForbiddenException();
}

// Assert-style:
Assert.isTrue(item.getOwnerId().equals(sessionUserId), "Not authorized");
```

---

## Priority 4: Data Access Layer Auth Patterns

### 4.1 Spring Data JPA — Scoped Repository Methods

**Search:** `JpaRepository`, `CrudRepository`, `findBy`, `@Query`, `@Modifying`

```java
// Auth in query (method naming convention):
List<Order> findByUserIdAndStatus(Long userId, String status);
Optional<Order> findByIdAndUserId(Long id, Long userId);  // ownership-scoped

// Auth in @Query:
@Query("SELECT o FROM Order o WHERE o.id = :orderId AND o.user.id = :userId")
Optional<Order> findByIdForUser(@Param("orderId") Long orderId, @Param("userId") Long userId);

// DANGEROUS: no user scope
Optional<Order> findById(Long id);  // any user's data
```

### 4.2 MyBatis XML Mapper

**Search:** `*.xml` in mapper/resources directories, `<select>`, `<update>`, `<delete>`, `<insert>`, `#{`, `namespace`

```xml
<!-- Auth in SQL — look for userId/sessionId parameter -->
<select id="getOrder" resultType="Order">
    SELECT * FROM orders WHERE id = #{orderId} AND user_id = #{userId}
</select>

<!-- DANGEROUS: no user scope -->
<select id="getOrderById" resultType="Order">
    SELECT * FROM orders WHERE id = #{orderId}
</select>
```

**Important:** Trace which Java parameter maps to `#{userId}` in the mapper interface. If it comes from user input (not session), it's NOT a trust anchor.

### 4.3 MyBatis Annotations

**Search:** `@Select`, `@Insert`, `@Update`, `@Delete`, `@Mapper`

```java
@Select("SELECT * FROM orders WHERE id = #{orderId} AND user_id = #{userId}")
Order getOrder(@Param("orderId") Long orderId, @Param("userId") Long userId);
```

### 4.4 JPA EntityManager / Hibernate Session

**Search:** `EntityManager`, `em.find`, `em.createQuery`, `em.createNativeQuery`, `Session.get`, `Criteria`

```java
// Direct find (no auth scope):
Order order = em.find(Order.class, orderId);  // DANGEROUS

// JPQL with auth:
Order order = em.createQuery("SELECT o FROM Order o WHERE o.id = :id AND o.userId = :uid", Order.class)
    .setParameter("id", orderId)
    .setParameter("uid", currentUserId)
    .getSingleResult();
```

### 4.5 JDBC / JdbcTemplate

**Search:** `JdbcTemplate`, `NamedParameterJdbcTemplate`, `PreparedStatement`, `executeQuery`, `executeUpdate`, `DriverManager`, `DataSource`

```java
jdbcTemplate.queryForObject(
    "SELECT * FROM orders WHERE id = ? AND user_id = ?",
    new Object[]{orderId, currentUserId},  // currentUserId is anchor
    orderRowMapper
);
```

### 4.6 Spring Data JPA @EntityGraph / Fetch Join

**Search:** `@EntityGraph`, `JOIN FETCH`, `FetchType.EAGER`

Check if the entity graph includes relations that shouldn't be visible to the requesting user.

---

## Priority 5: Special Auth Mechanisms

### 5.1 Internal Service Call Headers (Microservices)

**Search:** `X-Internal`, `X-Service`, `X-Forwarded-User`, `X-User-Id`, `X-Tenant-Id`, custom internal headers

```java
String userId = request.getHeader("X-Forwarded-UserId");     // from API gateway
String tenantId = request.getHeader("X-Tenant-Id");           // multi-tenant
String internalToken = request.getHeader("X-Internal-Token"); // service-to-service
```

**WARNING:** These are trust anchors ONLY IF set by a trusted gateway/proxy, not if the client can set them directly. Check if the gateway strips/overwrites these headers.

### 5.2 Spring Security ACL (Access Control List)

**Search:** `AclService`, `MutableAcl`, `ObjectIdentity`, `hasPermission`, `@PostAuthorize("hasPermission")`

### 5.3 Apache Shiro Filter Chain

**Search:** `ShiroFilterFactoryBean`, `filterChainDefinitionMap`, `shiro.ini`, `[urls]`

```java
@Bean
public ShiroFilterFactoryBean shiroFilter(SecurityManager securityManager) {
    ShiroFilterFactoryBean bean = new ShiroFilterFactoryBean();
    Map<String, String> filterMap = new LinkedHashMap<>();
    filterMap.put("/login", "anon");           // no auth
    filterMap.put("/api/admin/**", "roles[admin]"); // role required
    filterMap.put("/api/**", "authc");          // auth required
    bean.setFilterChainDefinitionMap(filterMap);
    return bean;
}
```

### 5.4 gRPC Server Interceptor

**Search:** `ServerInterceptor`, `ServerCallHandler`, `Metadata`, `io.grpc`, `GrpcService`

```java
public class AuthInterceptor implements ServerInterceptor {
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers, ServerCallHandler<ReqT, RespT> next) {
        String token = headers.get(AUTH_HEADER_KEY);
        // validate token
        Context ctx = Context.current().withValue(USER_CONTEXT_KEY, userId);
        return Contexts.interceptCall(ctx, call, headers, next);
    }
}
```

### 5.5 Spring AOP Pointcut-Based Auth (Non-Annotation)

**Search:** `@Aspect`, `@Around("execution`, `@Before("execution`, `@Pointcut`, pointcut expressions targeting service/controller methods

```java
@Aspect
@Component
public class ServiceAuthAspect {
    // Intercepts ALL methods in service package
    @Before("execution(* com.example.service.*.*(..))")
    public void checkServiceAuth(JoinPoint jp) {
        // extract user from context, check authorization
    }

    // Intercepts methods matching naming pattern
    @Around("execution(* com.example..*.delete*(..))")
    public Object checkDeleteAuth(ProceedingJoinPoint pjp) throws Throwable {
        // require ADMIN role for any delete* method
    }
}
```

### 5.6 Spring Security OAuth2 Resource Server

**Search:** `@EnableResourceServer`, `OAuth2ResourceServerConfigurer`, `jwt()`, `opaqueToken()`, `BearerTokenAuthentication`, `JwtDecoder`

```java
http.oauth2ResourceServer(oauth2 -> oauth2
    .jwt(jwt -> jwt.decoder(jwtDecoder()))
);
// Trust anchor: JwtAuthenticationToken.getName(), .getAuthorities()
```

### 5.7 Spring @ControllerAdvice + ResponseBodyAdvice (Output Filtering)

**Search:** `@ControllerAdvice`, `ResponseBodyAdvice`, `beforeBodyWrite`

**Mechanism:** Modifies response body before sending — could be used for post-response auth filtering.

```java
@ControllerAdvice
public class DataFilterAdvice implements ResponseBodyAdvice<Object> {
    @Override
    public Object beforeBodyWrite(Object body, ...) {
        // filter response fields based on current user's role
        return filterByPermission(body, getCurrentUser());
    }
}
```

### 5.8 Dubbo / RPC Service Auth

**Search:** `@DubboService`, `@Service` (Dubbo), `RpcContext`, `Filter` (Dubbo), `@Activate`

```java
// Dubbo consumer filter
@Activate(group = "consumer")
public class AuthFilter implements Filter {
    @Override
    public Result invoke(Invoker<?> invoker, Invocation invocation) {
        RpcContext.getContext().setAttachment("userId", currentUserId);
        return invoker.invoke(invocation);
    }
}
```

### 5.9 Reflection / Dynamic Invocation Auth

**Search:** `Method.invoke`, `reflect`, `MethodHandle`, `DynamicProxy`, `InvocationHandler`

**Caution:** If controllers dispatch to service methods via reflection (e.g., generic API gateway pattern), the auth annotation on the target method may not be enforced by the framework. Check if custom invocation wrappers include auth checks.
