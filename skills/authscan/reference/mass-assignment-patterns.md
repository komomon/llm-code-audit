# Mass Assignment Risk Patterns

Mass assignment occurs when user input is bound directly to a data model, allowing attackers to modify fields they shouldn't have access to.

## Sensitive Fields to Watch

| Category | Field Names | Risk |
|----------|------------|------|
| **Permission/Role** | `role`, `roles`, `permission`, `permissions`, `isAdmin`, `is_staff`, `is_superuser`, `level`, `authority`, `group`, `userType` | Privilege escalation |
| **Identity** | `userId`, `user_id`, `ownerId`, `owner_id`, `createdBy`, `created_by`, `tenantId`, `tenant_id`, `orgId` | Identity spoofing |
| **Status** | `status`, `state`, `approved`, `verified`, `enabled`, `disabled`, `deleted`, `is_active`, `locked`, `banned` | Business logic bypass |
| **Financial** | `price`, `amount`, `balance`, `credits`, `discount`, `total`, `fee`, `salary` | Financial manipulation |
| **Audit** | `createdAt`, `updatedAt`, `created_at`, `updated_at`, `version` | Audit trail tampering |
| **Internal** | `id`, `pk`, `internalId`, `systemField`, `secret`, `token`, `password`, `passwordHash` | Direct data corruption |

## Java Vulnerable Patterns

### Spring @ModelAttribute / @RequestBody Auto-Binding

```java
// VULNERABLE: All fields from JSON bound to entity
@PostMapping("/users")
public User createUser(@RequestBody User user) {
    return userRepo.save(user);  // user.role, user.isAdmin could be set by attacker
}

// VULNERABLE: Form binding to entity
@PostMapping("/update")
public void updateUser(@ModelAttribute User user) {
    userService.update(user);  // attacker can add role=ADMIN to form
}
```

**Safe alternatives:**
```java
// SAFE: Use a DTO with only allowed fields
public class CreateUserDTO {
    private String name;
    private String email;
    // No role, isAdmin, etc.
}

@PostMapping("/users")
public User createUser(@RequestBody CreateUserDTO dto) {
    User user = new User();
    user.setName(dto.getName());
    user.setEmail(dto.getEmail());
    user.setRole(Role.USER);  // Set explicitly, not from input
    return userRepo.save(user);
}
```

### Spring Data JPA save() with Entity

```java
// VULNERABLE: Entity from request saved directly
@PutMapping("/users/{id}")
public User updateUser(@PathVariable Long id, @RequestBody User user) {
    user.setId(id);
    return userRepo.save(user);  // All fields from request body saved
}
```

### MapStruct / BeanUtils.copyProperties

```java
// POTENTIALLY VULNERABLE: copies all matching properties
BeanUtils.copyProperties(requestDTO, entity);  // Check what fields match
```

## Python Vulnerable Patterns

### Django ModelForm without fields/exclude

```python
# VULNERABLE: All model fields exposed
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = '__all__'  # Includes role, is_staff, etc.

# SAFE: Explicit field whitelist
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email']  # Only safe fields
```

### Django REST Framework Serializer

```python
# VULNERABLE: All fields serializable
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

# SAFE: Explicit fields
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']
        read_only_fields = ['role', 'is_staff']  # Can't be set via API
```

### Direct dict unpacking

```python
# VULNERABLE: All request data passed to create
User.objects.create(**request.data)

# VULNERABLE: update with arbitrary fields
User.objects.filter(id=uid).update(**request.data)

# SAFE: Explicit fields
User.objects.create(
    name=request.data['name'],
    email=request.data['email'],
    role='user'  # Set explicitly
)
```

### FastAPI Pydantic Model

```python
# Check if the Pydantic model includes sensitive fields
class UserUpdate(BaseModel):
    name: str
    email: str
    role: str  # VULNERABLE: role should not be user-settable

# SAFE: Separate models for different operations
class UserUpdateRequest(BaseModel):
    name: str
    email: str
    # No role field — can't be set by user
```

## Detection Strategy

1. **Find write endpoints** (POST/PUT/PATCH handlers)
2. **Identify the input type** (DTO/Entity/dict/form)
3. **Trace which fields reach the datasink** (save/update/create)
4. **Check for field filtering:**
   - Explicit DTO with limited fields → Safe
   - Entity/Model with `fields = '__all__'` → Check for sensitive fields
   - `BeanUtils.copyProperties` / dict unpacking → Check source fields
   - `read_only_fields` / `exclude` declarations → Verify they cover sensitive fields
5. **Cross-reference with sensitive field list above**
