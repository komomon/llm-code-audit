# Node.js / TypeScript Authentication & Authorization Patterns Reference

Patterns ordered by priority. Match earlier patterns first.

---

## Priority 1: Framework-Level Global Middleware

### 1.1 Express Global Middleware

**Search:** `app.use`, `express()`, `middleware`, `next()`, `req.user`, `express-session`

**Mechanism:** Middleware functions execute in order for every request. Auth middleware validates credentials and attaches user to `req.user`.

**Trust anchor source:** `req.user` (set by auth middleware), `req.session.userId`

```javascript
// Global auth middleware — applies to all routes after this point
const authMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    req.user = decoded;  // trust anchor set here
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

app.use(authMiddleware);  // all routes below this are protected

// Whitelist pattern — unprotected routes BEFORE the middleware
app.get('/health', (req, res) => res.json({ status: 'ok' }));  // no auth
app.use(authMiddleware);
app.get('/api/orders', orderController.list);  // auth required
```

**Record:** Which routes are mounted BEFORE vs AFTER the auth middleware. Routes before are unprotected.

### 1.2 Express Router-Level Middleware

**Search:** `express.Router()`, `router.use`, `router.get`, `router.post`

```javascript
const adminRouter = express.Router();
adminRouter.use(authMiddleware);          // all routes in this router need auth
adminRouter.use(requireRole('admin'));    // all routes need admin role
adminRouter.get('/users', listUsers);
adminRouter.delete('/users/:id', deleteUser);

app.use('/api/admin', adminRouter);       // mounted under /api/admin
app.use('/api/public', publicRouter);     // separate router, possibly no auth
```

### 1.3 Koa Middleware

**Search:** `Koa`, `koa`, `ctx.state.user`, `ctx.request`, `koa-jwt`, `koa-passport`, `koa-session`

**Trust anchor source:** `ctx.state.user`

```javascript
const Koa = require('koa');
const jwt = require('koa-jwt');

const app = new Koa();

// Error handling for unauthorized
app.use(async (ctx, next) => {
  try { await next(); }
  catch (err) { if (err.status === 401) ctx.status = 401; }
});

// Public routes BEFORE jwt middleware
const publicRouter = new Router();
publicRouter.get('/health', ctx => { ctx.body = 'ok'; });
app.use(publicRouter.routes());

// JWT middleware — protects everything after this
app.use(jwt({ secret: SECRET_KEY }));
// ctx.state.user is trust anchor after this point

const protectedRouter = new Router();
protectedRouter.get('/api/orders', async ctx => {
  const userId = ctx.state.user.id;  // trust anchor
  ctx.body = await Order.find({ userId });
});
app.use(protectedRouter.routes());
```

### 1.4 Fastify Hooks & Plugins

**Search:** `fastify`, `onRequest`, `preHandler`, `decorate`, `fastify-jwt`, `@fastify/auth`, `fastify.register`

**Trust anchor source:** `request.user` (set by auth hook/plugin)

```javascript
// Plugin-based auth
fastify.register(require('@fastify/jwt'), { secret: SECRET_KEY });

// Global preHandler hook
fastify.addHook('onRequest', async (request, reply) => {
  try {
    await request.jwtVerify();
    // request.user is now set — trust anchor
  } catch (err) {
    reply.code(401).send({ error: 'Unauthorized' });
  }
});

// Route-level hook (skip auth for specific routes)
fastify.get('/health', { onRequest: [] }, async () => ({ status: 'ok' }));

// Fastify route with schema validation
fastify.get('/api/orders/:id', {
  preHandler: [requireRole('user')],  // route-level auth
  handler: async (request, reply) => {
    const userId = request.user.id;  // trust anchor
    const order = await Order.findOne({ id: request.params.id, userId });
    return order;
  }
});
```

### 1.5 NestJS Guards (Global)

**Search:** `@UseGuards`, `CanActivate`, `ExecutionContext`, `APP_GUARD`, `AuthGuard`, `@nestjs/passport`, `@nestjs/jwt`

**Mechanism:** Guards implement `CanActivate` interface. Can be applied globally, at controller level, or at route level.

**Trust anchor source:** `request.user` (set by Passport strategy or JWT guard)

```typescript
// Global guard registration
@Module({
  providers: [{ provide: APP_GUARD, useClass: JwtAuthGuard }],
})
export class AppModule {}

// Guard implementation
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  canActivate(context: ExecutionContext) {
    return super.canActivate(context);
    // After this, request.user is set by Passport JWT strategy
  }
}

// Skip auth for specific routes
@Public()  // custom decorator that sets metadata
@Get('health')
healthCheck() { return { status: 'ok' }; }
```

### 1.6 NestJS Middleware

**Search:** `NestMiddleware`, `configure`, `forRoutes`, `exclude`, `MiddlewareConsumer`

```typescript
@Module({})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(AuthMiddleware)
      .exclude({ path: 'health', method: RequestMethod.GET })  // whitelist
      .forRoutes('*');  // all other routes protected
  }
}
```

---

## Priority 2: Route-Level / Decorator-Level Auth

### 2.1 NestJS @UseGuards + Role Decorators

**Search:** `@UseGuards`, `@Roles`, `@SetMetadata`, `RolesGuard`, `Reflector`

```typescript
// Role-based guard
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}
  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.get<string[]>('roles', context.getHandler());
    if (!requiredRoles) return true;
    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some(role => user.roles?.includes(role));
  }
}

// Usage on controller/route
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
export class AdminController {
  @Roles('admin')
  @Delete('users/:id')
  deleteUser(@Param('id') id: string) { ... }
}
```

### 2.2 Express Route-Level Middleware

**Search:** `router.get('/path', middleware, handler)`, middleware functions between path and handler

```javascript
// Auth middleware applied per-route
router.get('/api/orders', authenticate, listOrders);
router.get('/api/admin/users', authenticate, requireAdmin, listUsers);
router.get('/api/public/products', listProducts);  // no middleware = no auth!

// Common pattern: middleware chain
const adminOnly = [authenticate, requireRole('admin')];
router.delete('/api/users/:id', ...adminOnly, deleteUser);
```

### 2.3 Fastify Route-Level preHandler

**Search:** `preHandler`, `onRequest` in route options

```javascript
// Route-specific auth hooks
fastify.get('/admin/users', {
  preHandler: [fastify.authenticate, fastify.requireAdmin],
  handler: adminController.listUsers
});

// No preHandler = no route-level auth (relies on global hook or none)
fastify.get('/public/info', {
  handler: publicController.getInfo  // check if global hook covers this
});
```

### 2.4 Passport.js Strategy Authentication

**Search:** `passport`, `passport.authenticate`, `passport-jwt`, `passport-local`, `passport-oauth2`, `serializeUser`, `deserializeUser`

**Trust anchor source:** `req.user` (set by Passport strategy after successful authentication)

```javascript
// JWT Strategy
passport.use(new JwtStrategy({
  jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
  secretOrKey: SECRET_KEY
}, (payload, done) => {
  User.findById(payload.sub)
    .then(user => done(null, user || false))
    .catch(err => done(err, false));
}));

// Route usage
router.get('/profile',
  passport.authenticate('jwt', { session: false }),
  (req, res) => {
    // req.user is trust anchor (set by Passport)
    res.json(req.user);
  }
);
```

### 2.5 CASL / AccessControl Permission Libraries

**Search:** `@casl/ability`, `accesscontrol`, `defineAbility`, `can`, `cannot`, `ForbiddenError`, `AccessControl`

```typescript
// CASL ability definition
const ability = defineAbility((can, cannot) => {
  can('read', 'Order', { userId: user.id });   // can only read own orders
  can('manage', 'all', { condition: { role: 'admin' } });
});

// Check in handler
if (ability.cannot('read', order)) {
  throw new ForbiddenError('Not allowed');
}
```

---

## Priority 3: In-Function Auth (Explicit Checks)

### 3.1 req.user / req.session

**Search:** `req.user`, `req.session`, `request.user`, `req.userId`, `req.auth`

```javascript
// Trust anchor from auth middleware
app.get('/api/orders', (req, res) => {
  const userId = req.user.id;        // trust anchor
  const role = req.user.role;
  const sessionUid = req.session?.userId;  // session-based anchor
});
```

### 3.2 JWT Verification (jsonwebtoken / jose)

**Search:** `jwt.verify`, `jwt.decode`, `jsonwebtoken`, `jose`, `jwtVerify`, `JWTPayload`

```javascript
const jwt = require('jsonwebtoken');

// TRUSTED: verify() validates signature
const decoded = jwt.verify(token, SECRET_KEY);
const userId = decoded.sub;  // trust anchor

// ❌ DANGEROUS: decode() does NOT validate signature!
const decoded = jwt.decode(token);  // anyone can forge this!
const userId = decoded.sub;  // NOT a trust anchor — R10 risk
```

**CRITICAL:** `jwt.decode()` vs `jwt.verify()` — decode does NOT check signature. If code uses `decode()` alone, the trust anchor is user-controllable (R10).

### 3.3 Express-Session

**Search:** `express-session`, `req.session`, `session.userId`, `connect-redis`, `session-file-store`

```javascript
const session = require('express-session');
app.use(session({ secret: 'secret', resave: false, saveUninitialized: false }));

// Login sets session
app.post('/login', (req, res) => {
  req.session.userId = authenticatedUser.id;  // server-side session
});

// Session as trust anchor
app.get('/api/profile', (req, res) => {
  const userId = req.session.userId;  // trust anchor (server-side)
  if (!userId) return res.status(401).send();
});
```

### 3.4 Custom Auth Utilities

**Search:** `getUser`, `getCurrentUser`, `AuthService`, `UserContext`, `cls-hooked`, `AsyncLocalStorage`

```typescript
// AsyncLocalStorage pattern (Node.js 16+)
const { AsyncLocalStorage } = require('async_hooks');
const userContext = new AsyncLocalStorage();

// Set in middleware
app.use((req, res, next) => {
  userContext.run({ userId: req.user.id }, next);
});

// Access anywhere in the call chain
function getService() {
  const { userId } = userContext.getStore();  // trust anchor
}
```

### 3.5 Explicit Ownership Checks

**Search:** `=== req.user`, `!== req.user`, `.userId ===`, `.ownerId ===`, `toString()` comparison

```javascript
// Guard pattern (R4)
const order = await Order.findById(orderId);
if (order.userId.toString() !== req.user.id.toString()) {
  return res.status(403).json({ error: 'Forbidden' });
}
// After guard: order is trusted

// CAUTION: MongoDB ObjectId comparison needs .toString()
if (order.userId !== req.user.id) {  // may fail — different types!
  // Always use .toString() or .equals() for ObjectId comparison
}
```

---

## Priority 4: Data Access Layer Auth Patterns

### 4.1 Mongoose (MongoDB) Scoped Queries

**Search:** `mongoose`, `Model.find`, `Model.findOne`, `Model.findById`, `.lean()`, `.populate()`

```javascript
// TRUSTED: scoped by user
const orders = await Order.find({ userId: req.user.id });
const order = await Order.findOne({ _id: orderId, userId: req.user.id });

// AT RISK: no user scope
const order = await Order.findById(orderId);  // any user's order
const orders = await Order.find({ status: 'active' });  // all users' orders
```

### 4.2 Sequelize Scoped Queries

**Search:** `sequelize`, `Model.findAll`, `Model.findOne`, `Model.findByPk`, `where`, `Op`

```javascript
// TRUSTED: scoped
const order = await Order.findOne({
  where: { id: orderId, userId: req.user.id }
});

// AT RISK: no user scope
const order = await Order.findByPk(orderId);  // any user's order
```

### 4.3 TypeORM Scoped Queries

**Search:** `typeorm`, `Repository`, `getRepository`, `createQueryBuilder`, `EntityManager`, `@Entity`

```typescript
// TRUSTED: scoped
const order = await orderRepo.findOne({
  where: { id: orderId, userId: currentUser.id }
});

// createQueryBuilder with scope
const order = await orderRepo.createQueryBuilder('order')
  .where('order.id = :id', { id: orderId })
  .andWhere('order.userId = :userId', { userId: currentUser.id })
  .getOne();

// AT RISK: no user scope
const order = await orderRepo.findOne({ where: { id: orderId } });
```

### 4.4 Prisma Scoped Queries

**Search:** `prisma`, `PrismaClient`, `prisma.model.findUnique`, `prisma.model.findMany`, `prisma.$queryRaw`

```typescript
// TRUSTED: scoped
const order = await prisma.order.findFirst({
  where: { id: orderId, userId: currentUser.id }
});

// AT RISK: no user scope
const order = await prisma.order.findUnique({ where: { id: orderId } });

// Raw query — check for user scope manually
const orders = await prisma.$queryRaw`
  SELECT * FROM orders WHERE id = ${orderId} AND user_id = ${currentUser.id}
`;
```

### 4.5 Knex / Raw SQL

**Search:** `knex`, `knex.raw`, `knex.select`, `pg`, `mysql2`, `better-sqlite3`, `query(`

```javascript
// TRUSTED: scoped
const order = await knex('orders')
  .where({ id: orderId, user_id: req.user.id })
  .first();

// AT RISK: no user scope
const order = await knex('orders').where({ id: orderId }).first();

// Raw query
const [order] = await db.query(
  'SELECT * FROM orders WHERE id = $1 AND user_id = $2',
  [orderId, req.user.id]
);
```

---

## Priority 5: Special Auth Mechanisms

### 5.1 Socket.io / WebSocket Auth

**Search:** `socket.io`, `io.use`, `socket.handshake`, `socket.user`, `ws`, `WebSocket`, `socket.request`

```javascript
// Socket.io middleware auth
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    socket.user = decoded;  // trust anchor for this connection
    next();
  } catch (err) {
    next(new Error('Authentication error'));
  }
});

io.on('connection', (socket) => {
  const userId = socket.user.id;  // trust anchor
  socket.on('getOrder', async (orderId) => {
    // Must still scope by userId!
    const order = await Order.findOne({ _id: orderId, userId });
    socket.emit('order', order);
  });
});
```

### 5.2 GraphQL Resolvers (Apollo / Type-GraphQL)

**Search:** `ApolloServer`, `graphql`, `resolvers`, `context`, `@Resolver`, `@Authorized`, `type-graphql`

**Trust anchor source:** `context.user` (set in Apollo context function)

```typescript
// Apollo Server context setup
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => ({
    user: req.user,  // from Express auth middleware
  }),
});

// Resolver — must scope queries by user
const resolvers = {
  Query: {
    order: async (_, { id }, context) => {
      const userId = context.user.id;  // trust anchor
      return Order.findOne({ _id: id, userId });  // TRUSTED: scoped
    },
    // AT RISK: no user scope
    orderUnsafe: async (_, { id }) => Order.findById(id),
  },
};
```

### 5.3 API Gateway / Internal Headers

**Search:** `x-user-id`, `x-forwarded-user`, `x-internal`, `x-tenant-id`, gateway headers

```javascript
// Trust headers from API gateway (trusted IF gateway is properly configured)
app.use((req, res, next) => {
  if (req.headers['x-internal-token'] === INTERNAL_SECRET) {
    req.user = {
      id: req.headers['x-user-id'],        // trust anchor from gateway
      tenantId: req.headers['x-tenant-id'],
    };
    next();
  } else {
    // DANGER: client can set these headers directly if no gateway!
    return res.status(401).send();
  }
});
```

### 5.4 Bull / BullMQ Background Jobs

**Search:** `Bull`, `BullMQ`, `Queue`, `Worker`, `process`, `add(`, `job.data`

**Caution:** Background jobs run outside request context. `req.user` is NOT available.

```javascript
// Adding job — must explicitly pass userId
await orderQueue.add('processOrder', {
  orderId,
  userId: req.user.id,  // pass trust anchor into job data
});

// Worker — userId comes from job data, NOT from request context
const worker = new Worker('orders', async (job) => {
  const { orderId, userId } = job.data;
  // Is userId trustworthy? Only if the producer (API endpoint) was authenticated.
  // If the queue accepts external messages, userId could be forged!
});
```

### 5.5 Next.js API Routes / Middleware

**Search:** `NextApiRequest`, `NextApiResponse`, `middleware.ts`, `getServerSession`, `getSession`, `NextAuth`

```typescript
// Next.js API route with NextAuth
import { getServerSession } from 'next-auth';
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const session = await getServerSession(req, res, authOptions);
  if (!session) return res.status(401).json({ error: 'Unauthorized' });
  const userId = session.user.id;  // trust anchor
}

// Next.js middleware (Edge Runtime)
export function middleware(request: NextRequest) {
  const token = request.cookies.get('session-token');
  if (!token) return NextResponse.redirect(new URL('/login', request.url));
}
```

---

## Priority 6: Trust Anchor Credibility Risks (CRITICAL)

### 6.1 jwt.decode() Without Verification

**Search:** `jwt.decode`, `decode(` without `verify(`, `jsonwebtoken`

**Risk:** `jwt.decode()` does NOT validate the signature. The token payload is user-controllable.

```javascript
// ❌ CRITICAL: decode() does not verify!
const decoded = jwt.decode(req.headers.authorization);
const userId = decoded.sub;  // ATTACKER CONTROLS THIS

// ✅ SAFE: verify() validates signature
const decoded = jwt.verify(req.headers.authorization, SECRET_KEY);
const userId = decoded.sub;  // trust anchor
```

### 6.2 Middleware Ordering Errors

**Search:** Review `app.use()` order, check if auth middleware is applied AFTER route definitions

**Risk:** Routes defined before auth middleware are unprotected.

```javascript
// ❌ DANGEROUS: route defined BEFORE auth middleware
app.get('/api/orders', orderController.list);  // NO AUTH!
app.use(authMiddleware);  // too late for /api/orders

// ✅ SAFE: auth middleware first
app.use(authMiddleware);
app.get('/api/orders', orderController.list);  // protected
```

### 6.3 Cookie-Based Auth Without Signature/Encryption

**Search:** `cookie-parser`, `req.cookies`, `res.cookie`, unsigned cookies, `signed: false`

**Risk:** Unsigned cookies can be modified by the client.

```javascript
// ❌ DANGEROUS: plain cookie as identity
app.get('/profile', (req, res) => {
  const userId = req.cookies.userId;  // CLIENT CAN SET THIS
});

// ✅ SAFE: signed cookie or session
app.use(cookieParser(COOKIE_SECRET));
app.get('/profile', (req, res) => {
  const userId = req.signedCookies.userId;  // server-signed
});
```

### 6.4 Missing Auth on Specific HTTP Methods

**Search:** `app.all`, `app.route`, check if PUT/DELETE have same auth as GET

**Risk:** Auth middleware applied only to GET but not to POST/PUT/DELETE on the same resource.

```javascript
// ❌ DANGEROUS: only GET is protected
router.get('/api/orders/:id', authenticate, getOrder);
router.put('/api/orders/:id', updateOrder);  // NO AUTH on update!
router.delete('/api/orders/:id', deleteOrder);  // NO AUTH on delete!

// ✅ SAFE: all methods protected
router.route('/api/orders/:id')
  .all(authenticate)
  .get(getOrder)
  .put(updateOrder)
  .delete(deleteOrder);
```
