# Python Authentication & Authorization Patterns Reference

Patterns ordered by priority. Match earlier patterns first.

---

## Priority 1: Framework-Level Global Auth

### 1.1 Django Middleware

**Search:** `MIDDLEWARE`, `AuthenticationMiddleware`, `process_request`, `process_view`, `__call__`, `settings.py`

```python
# settings.py — check MIDDLEWARE order
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # sets request.user
    'myapp.middleware.CustomAuthMiddleware',                     # custom
    'myapp.middleware.RoleCheckMiddleware',                      # custom role check
]

# Custom middleware (function-based)
def auth_middleware(get_response):
    def middleware(request):
        if not request.user.is_authenticated and not is_public_path(request.path):
            return JsonResponse({"error": "unauthorized"}, status=401)
        return get_response(request)
    return middleware

# Custom middleware (class-based)
class TenantAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = request.headers.get('X-Tenant-Id')
        request.tenant = validate_tenant(tenant_id)
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Called before view — can block access here."""
        if hasattr(view_func, 'require_admin') and not request.user.is_staff:
            return HttpResponseForbidden()
        return None
```

**Trust anchor:** `request.user`, `request.user.id`, `request.user.pk`

### 1.2 FastAPI Dependencies (Global / Router / Endpoint)

**Search:** `Depends`, `Security`, `OAuth2PasswordBearer`, `HTTPBearer`, `get_current_user`, `APIRouter`, `app = FastAPI`

```python
# Global dependency (all endpoints)
app = FastAPI(dependencies=[Depends(verify_token)])

# Router-level dependency
router = APIRouter(
    prefix="/api/admin",
    dependencies=[Depends(require_admin)]    # all routes in this router need admin
)

# Endpoint-level dependency
@app.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return user_service.get_profile(user.id)  # user.id is trust anchor

# Dependency chain
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = await user_repo.get(payload["sub"])
    if not user:
        raise HTTPException(status_code=401)
    return user

async def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403)
    return user
```

### 1.3 Flask before_request / before_app_request

**Search:** `before_request`, `before_app_request`, `@app.before_request`, `@blueprint.before_request`

```python
@app.before_request
def check_auth():
    # Whitelist
    if request.endpoint in ('login', 'register', 'health'):
        return None
    # Check auth
    token = request.headers.get('Authorization')
    user = validate_token(token)
    if not user:
        abort(401)
    g.user = user  # trust anchor set here

@admin_bp.before_request
def check_admin():
    if not g.user.is_admin:
        abort(403)
```

**Trust anchor:** `g.user`, `g.user.id`

### 1.4 Flask-Login LoginManager

**Search:** `flask_login`, `LoginManager`, `login_required`, `current_user`, `user_loader`

```python
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# current_user is automatically set for all requests
# current_user.id is trust anchor
```

### 1.5 ASGI Middleware (Starlette / FastAPI)

**Search:** `BaseHTTPMiddleware`, `ASGIMiddleware`, `@app.middleware`, `Middleware`, `starlette.middleware`

```python
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = request.headers.get("Authorization")
        if not token and request.url.path not in PUBLIC_PATHS:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        request.state.user = await validate_token(token)
        return await call_next(request)
```

### 1.6 Tornado RequestHandler prepare()

**Search:** `tornado.web.RequestHandler`, `prepare`, `get_current_user`

```python
class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        token = self.request.headers.get("Authorization")
        self.current_user = validate_token(token)
        if not self.current_user:
            raise tornado.web.HTTPError(401)
    # self.current_user is trust anchor in all handlers
```

---

## Priority 2: Decorator-Level Auth

### 2.1 Django @login_required / @permission_required / @user_passes_test

**Search:** `@login_required`, `@permission_required`, `@user_passes_test`, `django.contrib.auth.decorators`

```python
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test

@login_required                                        # must be logged in
def view_profile(request): ...

@permission_required('app.can_delete_order')           # specific permission
def delete_order(request, order_id): ...

@permission_required('app.can_delete_order', raise_exception=True)  # 403 instead of redirect
def delete_order(request, order_id): ...

@user_passes_test(lambda u: u.is_staff)                # custom test function
def admin_view(request): ...

@user_passes_test(lambda u: u.groups.filter(name='editors').exists())
def editor_view(request): ...
```

### 2.2 Django Class-Based View Mixins

**Search:** `LoginRequiredMixin`, `PermissionRequiredMixin`, `UserPassesTestMixin`, `AccessMixin`, `django.contrib.auth.mixins`

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    login_url = '/login/'

class AdminDashboard(PermissionRequiredMixin, TemplateView):
    permission_required = 'app.view_dashboard'

class OwnerOnlyView(UserPassesTestMixin, DetailView):
    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user  # ownership check
```

### 2.3 Django REST Framework Permission Classes

**Search:** `IsAuthenticated`, `IsAdminUser`, `AllowAny`, `DjangoModelPermissions`, `DjangoObjectPermissions`, `BasePermission`, `permission_classes`, `DEFAULT_PERMISSION_CLASSES`

```python
from rest_framework.permissions import IsAuthenticated, BasePermission

# Global default (settings.py)
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
}

# Per-view override
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerPermission]

# Custom object-level permission
class IsOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user  # ownership check

# Combined permissions
class AdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff
```

### 2.4 DRF Authentication Classes

**Search:** `authentication_classes`, `DEFAULT_AUTHENTICATION_CLASSES`, `BaseAuthentication`, `TokenAuthentication`, `JWTAuthentication`, `SessionAuthentication`

```python
# These IDENTIFY the user, not authorize
class ApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        key = request.headers.get('X-API-Key')
        user = ApiKey.objects.get(key=key).user
        return (user, None)  # returns (user, auth) tuple

class CustomView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAuthenticated]  # this does the authorization
```

### 2.5 Flask-Login @login_required

**Search:** `@login_required`, `flask_login.login_required`

```python
from flask_login import login_required, current_user

@app.route('/orders')
@login_required
def get_orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return jsonify([o.to_dict() for o in orders])
```

### 2.6 FastAPI Security Schemes

**Search:** `OAuth2PasswordBearer`, `HTTPBearer`, `HTTPBasic`, `APIKeyHeader`, `APIKeyCookie`, `APIKeyQuery`, `SecurityScopes`

```python
# OAuth2 with scopes
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"read": "Read access", "write": "Write access", "admin": "Admin access"}
)

async def get_current_user(security_scopes: SecurityScopes,
                            token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY)
    token_scopes = payload.get("scopes", [])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403, detail="Insufficient scope")
    return payload

@app.get("/admin", dependencies=[Security(get_current_user, scopes=["admin"])])
async def admin_endpoint(): ...
```

### 2.7 Custom Python Decorators

**Search:** `functools.wraps`, `@wraps`, custom decorator definitions that check auth

```python
def require_role(*roles):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.role in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(perm):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(perm):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

@require_role('admin', 'manager')
def manage_users(request): ...

@require_permission('order:delete')
def delete_order(request, order_id): ...
```

---

## Priority 3: In-Function Auth (Explicit Checks)

### 3.1 Django request.user

**Search:** `request.user`, `request.user.id`, `request.user.pk`, `request.user.is_staff`, `request.user.is_superuser`, `request.user.has_perm`

```python
# Trust anchors:
user_id = request.user.id           # current user ID
is_staff = request.user.is_staff    # admin flag
is_superuser = request.user.is_superuser

# Permission check:
if request.user.has_perm('app.change_order'):
    ...

# Group check:
if request.user.groups.filter(name='editors').exists():
    ...
```

### 3.2 Flask g.user / session

**Search:** `g.user`, `session['user_id']`, `flask.session`, `flask.g`, `current_user`

```python
# Flask-Login
from flask_login import current_user
user_id = current_user.id  # trust anchor

# Flask session
user_id = session.get('user_id')  # trust anchor

# Flask g (set by before_request)
user_id = g.user.id  # trust anchor
```

### 3.3 JWT Decoding (PyJWT / python-jose)

**Search:** `jwt.decode`, `jose.jwt`, `PyJWT`, `python-jose`, `authlib`, `itsdangerous`

```python
import jwt
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
user_id = payload['sub']     # trust anchor
roles = payload.get('roles', [])

# python-jose
from jose import jwt
payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

# itsdangerous (Flask session signing)
from itsdangerous import URLSafeTimedSerializer
s = URLSafeTimedSerializer(SECRET_KEY)
data = s.loads(token, max_age=3600)
user_id = data['user_id']  # trust anchor
```

### 3.4 Explicit Ownership Checks

**Search:** `== request.user`, `!= request.user`, `owner`, `user_id ==`, `.user ==`, `get_object_or_404` + ownership

```python
# Guard pattern (R4):
order = Order.objects.get(id=order_id)
if order.user != request.user:
    raise PermissionDenied("Not your order")
# After guard: order is trusted

# get_object_or_404 with ownership:
order = get_object_or_404(Order, id=order_id, user=request.user)
# Directly trusted (R1: anchor in query)
```

---

## Priority 4: ORM / Data Access Auth Patterns

### 4.1 Django ORM — Scoped Queries

**Search:** `objects.filter`, `objects.get`, `objects.all`, `objects.exclude`, `Q(`, `get_queryset`

```python
# TRUSTED (R1: anchor in query):
orders = Order.objects.filter(user=request.user, id=order_id)
order = Order.objects.get(id=order_id, user_id=request.user.id)

# AT RISK (no user scope):
order = Order.objects.get(id=order_id)
orders = Order.objects.all()

# Queryset scoping in DRF ViewSet:
class OrderViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)  # scoped — TRUSTED
```

### 4.2 Django Manager Custom Queryset

**Search:** `Manager`, `QuerySet`, `get_queryset`, `objects =`, custom manager

```python
class UserScopedManager(models.Manager):
    def for_user(self, user):
        return self.filter(user=user)

class Order(models.Model):
    objects = UserScopedManager()

# Usage:
orders = Order.objects.for_user(request.user)  # TRUSTED
```

### 4.3 SQLAlchemy Scoped Queries

**Search:** `db.session.query`, `.filter`, `.filter_by`, `Session.query`, `select(`, `and_(`

```python
# TRUSTED:
order = db.session.query(Order).filter(
    Order.id == order_id,
    Order.user_id == current_user.id
).first()

# SQLAlchemy 2.0 style:
stmt = select(Order).where(and_(Order.id == order_id, Order.user_id == uid))
order = db.session.execute(stmt).scalar_one()

# AT RISK:
order = db.session.query(Order).get(order_id)
```

### 4.4 Raw SQL

**Search:** `cursor.execute`, `raw(`, `RawSQL`, `extra(`, `connection.cursor`

```python
# Django raw SQL:
orders = Order.objects.raw(
    'SELECT * FROM orders WHERE id = %s AND user_id = %s',
    [order_id, request.user.id]  # user_id is anchor
)

# Direct cursor:
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM orders WHERE id = %s AND user_id = %s",
        [order_id, request.user.id]
    )
```

### 4.5 Tortoise ORM (FastAPI)

**Search:** `tortoise`, `Tortoise`, `.filter`, `.get`, `.all`, `tortoise.models`

```python
order = await Order.filter(id=order_id, user_id=current_user.id).first()  # TRUSTED
order = await Order.get(id=order_id)  # AT RISK
```

### 4.6 MongoDB (pymongo / mongoengine / motor)

**Search:** `pymongo`, `mongoengine`, `motor`, `find_one`, `find`, `collection.`, `Document`

```python
# pymongo:
order = db.orders.find_one({"_id": order_id, "user_id": current_user_id})  # TRUSTED
order = db.orders.find_one({"_id": order_id})  # AT RISK

# mongoengine:
order = Order.objects(id=order_id, user_id=current_user.id).first()  # TRUSTED
```

---

## Priority 5: Special Auth Mechanisms

### 5.1 Django Admin

**Search:** `admin.site`, `ModelAdmin`, `has_change_permission`, `has_delete_permission`, `has_view_permission`

Django admin has built-in permission checks, but custom admin actions may bypass them.

### 5.2 Django Signals

**Search:** `post_save`, `pre_save`, `pre_delete`, `receiver`, `Signal`

Signals execute automatically — check if they have auth context. Usually they DON'T have `request.user` unless explicitly passed.

### 5.3 Celery / Background Tasks

**Search:** `@shared_task`, `@app.task`, `celery`, `delay(`, `apply_async`, `bind=True`

**WARNING:** Background tasks run outside request context. `request.user` is NOT available. Check how user identity is passed:
```python
@shared_task
def process_order(order_id, user_id):  # user_id must be explicitly passed
    # Is user_id from session (trusted) or from user input (untrusted)?
```

### 5.4 FastAPI BackgroundTasks

**Search:** `BackgroundTasks`, `background_tasks.add_task`

Same concern — background tasks don't have request context. User identity must be explicitly passed.

### 5.5 GraphQL (Graphene / Strawberry / Ariadne)

**Search:** `graphene`, `strawberry`, `ariadne`, `resolve_`, `info.context`, `Mutation`, `Query`

```python
# Graphene:
class Query(graphene.ObjectType):
    orders = graphene.List(OrderType)
    def resolve_orders(self, info):
        user = info.context.user  # trust anchor
        return Order.objects.filter(user=user)

# Strawberry:
@strawberry.type
class Query:
    @strawberry.field
    def orders(self, info: Info) -> list[Order]:
        user = info.context["request"].user  # trust anchor
        return Order.objects.filter(user=user)
```

### 5.6 Flask-Principal / Flask-Security

**Search:** `flask_principal`, `flask_security`, `RoleNeed`, `Permission`, `Identity`, `roles_required`, `roles_accepted`

```python
from flask_principal import Permission, RoleNeed

admin_permission = Permission(RoleNeed('admin'))

@app.route('/admin')
@admin_permission.require(http_exception=403)
def admin_panel(): ...
```

### 5.7 Django REST Framework Token / SimpleJWT

**Search:** `rest_framework.authtoken`, `rest_framework_simplejwt`, `TokenAuthentication`, `JWTAuthentication`, `TokenObtainPairView`

```python
# SimpleJWT — token contains user identity
from rest_framework_simplejwt.authentication import JWTAuthentication

# In views: request.user is set automatically by DRF's authentication
# request.user.id is trust anchor
```

### 5.8 Python gRPC Interceptor

**Search:** `grpc`, `ServerInterceptor`, `intercept_service`, `ServicerContext`, `metadata`

```python
class AuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get('authorization')
        # validate and set user context
```

### 5.9 WebSocket Auth (Django Channels / FastAPI WebSocket)

**Search:** `WebSocketConsumer`, `@channel_layer`, `websocket_connect`, `WebSocket`, `WebSocketEndpoint`

```python
# Django Channels:
class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]  # trust anchor from middleware
        if not self.user.is_authenticated:
            self.close()

# FastAPI:
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user: User = Depends(get_ws_user)):
    # user is trust anchor
```
