# AWS Cognito Integration — Setup & Code Reference

This document covers every step taken to integrate AWS Cognito into the Smart Q&A application: the AWS Console setup, Lambda triggers, backend changes, and frontend changes. It also lists the common errors encountered and how they were fixed.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [AWS Console Setup](#2-aws-console-setup)
3. [Lambda Trigger Functions](#3-lambda-trigger-functions)
4. [Backend Code Changes](#4-backend-code-changes)
5. [Frontend Code Changes](#5-frontend-code-changes)
6. [Environment Variables](#6-environment-variables)
7. [Common Issues & Fixes](#7-common-issues--fixes)
8. [Reference Links](#8-reference-links)

---

## 1. Architecture Overview

The app uses Cognito **User Pools** for authentication and **User Pool Groups** for role-based access control (STUDENT, TA, ADMIN). The backend never handles passwords — Cognito does. The backend only validates JWTs.

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│                                                             │
│  Register/Login  ──►  amazon-cognito-identity-js SDK        │
│                              │                              │
│              ┌───────────────┴───────────────┐              │
│              ▼                               ▼              │
│       Access Token                       ID Token           │
│    (sent to backend)              (decoded in frontend       │
│                                    for email/name)          │
└──────────────────────────────────────────────────────────────┘
         │ Authorization: Bearer <AccessToken>
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  1. Fetch JWKS from Cognito public endpoint                 │
│  2. Validate RS256 signature                                │
│  3. Verify token_use == "access" and client_id              │
│  4. Read cognito:groups for role-based access               │
│  5. Resolve/create User record in PostgreSQL by sub         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────┐      ┌───────────────────────────────┐
│    PostgreSQL DB   │      │       AWS Cognito              │
│                    │      │                                │
│  users table:      │      │  User Pool Groups:             │
│  - user_id (PK)    │      │   - STUDENT                   │
│  - cognito_sub     │      │   - TA                        │
│  - email           │      │   - ADMIN                     │
│  - display_name    │      │                                │
└────────────────────┘      └───────────────────────────────┘
```

### Auth flow — step by step

```
User fills Register form (name, email, password, role)
  │
  ├─► signUp() → Cognito (stores email, name, custom:desired_role)
  │       │
  │       └─► Pre Sign-up Lambda: auto-confirms user + verifies email
  │               │
  │               └─► Post-Confirmation Lambda: adds user to group
  │                       (STUDENT / TA / ADMIN) based on custom:desired_role
  │
  ├─► signIn() → Cognito returns { AccessToken, IdToken, RefreshToken }
  │
  ├─► AuthContext.login(session):
  │     ├─ Decode AccessToken → extract cognito:groups → set role state
  │     ├─ Decode IdToken → extract email, name
  │     ├─ PATCH /auth/me → backend saves email + display_name to DB
  │     └─ GET /auth/me → fetch updated user object, set user state
  │
  └─► All subsequent API calls attach AccessToken in Authorization header
        Backend validates token → resolves User record by cognito_sub
```

---

## 2. AWS Console Setup

### 2.1 Create the User Pool

1. Go to **AWS Console → Cognito → User Pools → Create user pool**
2. **Sign-in options**: check **Email**
3. **Password policy**: set your preferred requirements (min 8 chars recommended)
4. **MFA**: select **No MFA** (for development)
5. **Required attributes**: add `email` (required) and `name` (optional but recommended)
6. **Custom attributes**: add `custom:desired_role` (String, mutable)
7. **Email delivery**: use Cognito's default email service for development
8. **User pool name**: e.g. `smart-qna-pool`
9. **App client name**: e.g. `smart-qna-client`
   - **App type**: Public client
   - **Authentication flows**: enable `ALLOW_USER_SRP_AUTH` and `ALLOW_REFRESH_TOKEN_AUTH`
   - **No client secret** (required for the JavaScript SDK)
10. Create the pool and note down:
    - **User Pool ID** (e.g. `us-east-1_FYVTuevQ9`)
    - **App Client ID** (e.g. `7r4nc65f89pg5adl442fufrig8`)

### 2.2 Create User Pool Groups

In the User Pool → **Groups** tab, create three groups:

| Group Name | Description              |
|------------|--------------------------|
| `STUDENT`  | Regular course students  |
| `TA`       | Teaching Assistants      |
| `ADMIN`    | Course administrators    |

No IAM role attachment needed for these groups (they're only used for RBAC inside the app).

### 2.3 Attach Lambda Triggers

Two Lambda functions are used. Create each in the Lambda console (runtime: Python 3.12), then attach them in the User Pool → **Triggers** tab.

| Trigger              | Lambda Function              |
|----------------------|------------------------------|
| Pre sign-up          | `cognito-pre-signup`         |
| Post confirmation    | `cognito-post-confirmation`  |

The Lambda execution role needs the `cognito-idp:AdminAddUserToGroup` permission. Attach the following inline policy to the Lambda role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "cognito-idp:AdminAddUserToGroup",
      "Resource": "arn:aws:cognito-idp:us-east-1:*:userpool/*"
    }
  ]
}
```

---

## 3. Lambda Trigger Functions

### 3.1 Pre Sign-up — Auto-confirm users

**Purpose:** Skips email verification during development so users can register and log in immediately.

**File:** `lambda/cognito_pre_signup/handler.py`

```python
def lambda_handler(event, context):
    event["response"]["autoConfirmUser"] = True
    event["response"]["autoVerifyEmail"] = True
    return event
```

> **Note:** Remove or disable this trigger in production so that Cognito enforces real email verification.

### 3.2 Post-Confirmation — Assign user to a group

**Purpose:** After a user is confirmed, reads the `custom:desired_role` attribute they submitted at registration and adds them to the matching Cognito group.

**File:** `lambda/cognito_post_confirmation/handler.py`

```python
import boto3

def lambda_handler(event, context):
    client = boto3.client("cognito-idp")
    pool_id = event["userPoolId"]
    username = event["userName"]

    # userAttributes is a plain dict, not a list
    attrs = event["request"]["userAttributes"]
    role = attrs.get("custom:desired_role", "STUDENT")

    # Sanitize — only allow known roles
    if role not in ("STUDENT", "TA", "ADMIN"):
        role = "STUDENT"

    client.admin_add_user_to_group(
        UserPoolId=pool_id,
        Username=username,
        GroupName=role,
    )
    return event
```

> **Key lesson:** `event["request"]["userAttributes"]` is a **dict** (not a list of `{Name, Value}` pairs). Accessing it like a list causes `TypeError: string indices must be integers`.

---

## 4. Backend Code Changes

### 4.1 `backend/.env` / `docker-compose.yml` — Cognito environment variables

Added three Cognito variables to the backend service environment:

```yaml
# docker-compose.yml (backend service)
environment:
  DATABASE_URL: postgresql+asyncpg://smartqna:localdev123@postgres:5432/smartqna
  COGNITO_REGION: us-east-1
  COGNITO_USER_POOL_ID: us-east-1_FYVTuevQ9
  COGNITO_APP_CLIENT_ID: 7r4nc65f89pg5adl442fufrig8
```

### 4.2 `backend/app/config.py` — Settings model

Replaced local JWT settings (`SECRET_KEY`, token expiry) with Cognito settings. A computed property builds the JWKS URL used for token validation.

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    COGNITO_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""

    @property
    def cognito_jwks_url(self) -> str:
        return (
            f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com"
            f"/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )
```

### 4.3 `backend/requirements.txt` — Dependencies

| Removed                        | Added                   |
|-------------------------------|-------------------------|
| `python-jose[cryptography]`   | `PyJWT[crypto]==2.9.0`  |
| `passlib`, `bcrypt`           | `boto3==1.35.0`         |

- **PyJWT** validates Cognito's RS256-signed JWTs using the JWKS public keys.
- **boto3** is used by the Admin API to manage Cognito groups.

### 4.4 `backend/app/core/security.py` — Token validation

Cognito signs tokens with RS256 using rotating key pairs published at a public JWKS endpoint. This file fetches those keys (cached with `lru_cache`) and validates incoming Access Tokens.

```python
import jwt, httpx
from functools import lru_cache
from app.config import settings

@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    response = httpx.get(settings.cognito_jwks_url)
    response.raise_for_status()
    return response.json()

def decode_cognito_token(token: str) -> dict:
    jwks = _get_jwks()
    header = jwt.get_unverified_header(token)
    key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
    if not key:
        raise ValueError("Public key not found for token")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Access tokens don't have an 'aud' claim — skip audience validation
    claims = jwt.decode(
        token, public_key, algorithms=["RS256"],
        options={"verify_aud": False},
    )

    # Manually verify this is an access token for our specific app client
    if claims.get("token_use") != "access":
        raise ValueError("Expected an access token")
    if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
        raise ValueError("Token client_id mismatch")

    return claims
```

> **Key lesson:** Cognito Access Tokens do **not** include an `aud` (audience) claim — only ID Tokens do. Using `verify_aud=True` (the PyJWT default) causes every request to fail with `InvalidAudienceError`. The workaround is to disable audience verification and instead manually verify `token_use` and `client_id`.

### 4.5 `backend/app/core/dependencies.py` — User resolution & RBAC

**`_resolve_user`** looks up a user in PostgreSQL by their Cognito `sub` (a stable UUID Cognito assigns every user). If the user doesn't exist yet (first login), it creates a stub record. Real email/name are synced separately via `PATCH /auth/me`.

**`require_role`** reads `cognito:groups` from the Access Token claims to enforce role-based access — no database query needed for authorization.

```python
async def _resolve_user(claims: dict, db: AsyncSession) -> User:
    sub = claims.get("sub")
    result = await db.execute(select(User).where(User.cognito_sub == sub))
    user = result.scalar_one_or_none()
    if not user:
        user = User(cognito_sub=sub, email=sub, display_name="User")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

def require_role(*roles: str):
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        claims = decode_cognito_token(credentials.credentials)
        user_groups = claims.get("cognito:groups", [])
        if not any(r in user_groups for r in roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return await _resolve_user(claims, db)
    return role_checker
```

### 4.6 `backend/app/api/auth.py` — Profile sync endpoint

The backend no longer owns registration or login — Cognito handles those. The auth router now only provides:

- `GET /auth/me` — returns the current user's profile
- `PATCH /auth/me` — called by the frontend after every login to write the real `email` and `display_name` (extracted from the Cognito ID Token) into the database

```python
class ProfileSync(BaseModel):
    email: str
    display_name: str

@router.patch("/me", response_model=UserResponse)
async def sync_profile(
    data: ProfileSync,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.email and "@" in data.email:
        current_user.email = data.email
    if data.display_name and data.display_name != "User":
        current_user.display_name = data.display_name
    await db.commit()
    await db.refresh(current_user)
    return current_user
```

> **Why is this needed?** Cognito Access Tokens (which the backend receives) do **not** contain `email` or `name` claims. Only ID Tokens do. Rather than forwarding the ID Token to the backend (a security anti-pattern), the frontend decodes it locally and pushes the data via this endpoint.

### 4.7 `backend/app/api/admin.py` — Admin user management

Admin-only endpoints that use `boto3` to interact with Cognito directly.

- `GET /admin/users` — lists all users in each group (STUDENT, TA, ADMIN)
- `PATCH /admin/users/{username}/role` — moves a user between groups

Both endpoints are protected by `require_role("ADMIN")`.

### 4.8 `backend/app/models/user.py` — User model

| Removed columns     | Added column                             |
|---------------------|------------------------------------------|
| `hashed_password`   | `cognito_sub` (String, unique, not null) |
| `role`              | —                                        |

The `cognito_sub` is Cognito's stable identifier for a user — it never changes even if the user's email changes.

### 4.9 `backend/alembic/versions/003_add_cognito_sub_drop_password_role.py` — Migration

```python
def upgrade() -> None:
    # Add nullable first so existing rows aren't rejected
    op.add_column('users', sa.Column('cognito_sub', sa.String(255), nullable=True))
    op.execute("UPDATE users SET cognito_sub = gen_random_uuid()::text WHERE cognito_sub IS NULL")
    op.alter_column('users', 'cognito_sub', nullable=False)
    op.create_unique_constraint('uq_users_cognito_sub', 'users', ['cognito_sub'])
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'role')
```

---

## 5. Frontend Code Changes

### 5.1 `frontend/.env` — Cognito environment variables

```ini
VITE_COGNITO_USER_POOL_ID=us-east-1_FYVTuevQ9
VITE_COGNITO_CLIENT_ID=7r4nc65f89pg5adl442fufrig8
VITE_COGNITO_REGION=us-east-1
```

Vite exposes variables prefixed with `VITE_` to the browser via `import.meta.env`.

### 5.2 `frontend/package.json` — New dependencies

```json
"dependencies": {
  "amazon-cognito-identity-js": "^6.3.12",
  "jwt-decode": "^4.0.0"
}
```

### 5.3 `frontend/vite.config.js` — Global polyfill

`amazon-cognito-identity-js` was written for Node.js and references the `global` object, which doesn't exist in browsers. This one-line fix maps it to the browser's `globalThis`.

```js
export default defineConfig({
  plugins: [react()],
  define: {
    global: "globalThis",   // polyfill for amazon-cognito-identity-js
  },
});
```

> Without this, the browser throws `Uncaught ReferenceError: global is not defined` and shows a blank page.

### 5.4 `frontend/src/services/cognito.js` — Cognito SDK wrapper

Wraps `amazon-cognito-identity-js` in Promise-based functions so the rest of the app doesn't need to deal with the callback API.

| Function              | Purpose                                                   |
|-----------------------|-----------------------------------------------------------|
| `signUp()`            | Registers user; sends `email`, `name`, `custom:desired_role` as attributes |
| `confirmSignUp()`     | Confirms email via OTP code (not used — Pre Sign-up Lambda auto-confirms) |
| `signIn()`            | Authenticates user, returns a `CognitoUserSession`        |
| `signOut()`           | Clears the local Cognito session                          |
| `getCurrentSession()` | Restores session from local storage (used on page load)   |
| `getRole(session)`    | Decodes Access Token, returns first group from `cognito:groups` |
| `getUserInfo(session)`| Decodes ID Token, returns `{ email, display_name }`      |

```js
// getRole reads from the Access Token (always has cognito:groups)
export function getRole(session) {
  const payload = jwtDecode(session.getAccessToken().getJwtToken());
  return (payload["cognito:groups"] || [])[0] || "STUDENT";
}

// getUserInfo reads from the ID Token (has email and name attributes)
export function getUserInfo(session) {
  const payload = jwtDecode(session.getIdToken().getJwtToken());
  const email = payload.email || payload["cognito:username"] || "";
  return {
    email,
    display_name: payload.name || email.split("@")[0] || "User",
  };
}
```

> **Why two tokens?** Cognito Access Tokens contain authorization claims (`cognito:groups`, `scope`) but not user attributes. ID Tokens contain user attributes (`email`, `name`) but are not meant to be sent to APIs. Each is used for its intended purpose.

### 5.5 `frontend/src/context/AuthContext.jsx` — Auth state management

Manages the Cognito session, user object, and role across the app. On every login (and on page load if a session is still valid in local storage), it:

1. Extracts the role from the Access Token
2. Extracts `email` and `display_name` from the ID Token
3. Calls `PATCH /auth/me` to sync those values to the database
4. Calls `GET /auth/me` to fetch the fully synced user object

```jsx
useEffect(() => {
  getCurrentSession().then(async (sess) => {
    if (sess) {
      setSession(sess);
      setRole(getRole(sess));
      try {
        const userInfo = getUserInfo(sess);
        if (userInfo?.email) {
          await api.patch("/auth/me", userInfo).catch(() => {});
        }
        const res = await api.get("/auth/me");
        setUser(res.data);
      } catch {
        setUser(null);
      }
    }
    setLoading(false);
  });
}, []);
```

### 5.6 `frontend/src/services/api.js` — Axios interceptor

Automatically attaches the Cognito Access Token to every outgoing API request. Also prevents an infinite redirect loop on auth pages.

```js
api.interceptors.request.use(async (config) => {
  const session = await getCurrentSession();
  if (session) {
    config.headers.Authorization = `Bearer ${session.getAccessToken().getJwtToken()}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const onAuthPage = ["/login", "/register"].includes(window.location.pathname);
    if (error.response?.status === 401 && !onAuthPage) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

> **Why check `onAuthPage`?** Without this guard, a 401 on the login page itself (e.g. during the initial `GET /auth/me`) triggers a redirect to `/login`, which triggers another 401, creating an infinite loop.

### 5.7 `frontend/src/pages/Register.jsx` — Role selection

Added a role dropdown so users self-select their role during registration. The selected role is passed as the `custom:desired_role` Cognito attribute, which the Post-Confirmation Lambda then uses to assign the user to the correct group.

After a successful `signUp`, the user is immediately signed in (because the Pre Sign-up Lambda auto-confirms them — no email verification step needed).

### 5.8 `frontend/src/pages/Login.jsx` — Cognito sign-in

Replaced the old `POST /auth/login` API call with `signIn()` from `cognito.js`. The returned session is passed to `AuthContext.login()` which handles the profile sync.

### 5.9 `frontend/src/components/ProtectedRoute.jsx` — Role-based routing

Added a `requiredRole` prop. If the current user's role doesn't match, they are redirected to the home page.

```jsx
if (requiredRole && role !== requiredRole) {
  return <Navigate to="/" replace />;
}
```

Usage in `App.jsx`:
```jsx
<Route
  path="/admin/users"
  element={
    <ProtectedRoute requiredRole="ADMIN">
      <AdminUsers />
    </ProtectedRoute>
  }
/>
```

### 5.10 `frontend/src/components/RoleBadge.jsx` — Role indicator

A small pill component that renders the user's role with distinct colors (blue for STUDENT, purple for TA, red for ADMIN). Used in the profile header and the Admin Users page.

### 5.11 `frontend/src/pages/AdminUsers.jsx` — Admin panel

An ADMIN-only page that:
- Calls `GET /admin/users` to list all Cognito users grouped by role
- Lets admins change any user's role via a dropdown, which calls `PATCH /admin/users/{username}/role`

---

## 6. Environment Variables

### Backend (`backend/.env` or `docker-compose.yml`)

| Variable               | Description                          | Example                       |
|------------------------|--------------------------------------|-------------------------------|
| `COGNITO_REGION`       | AWS region of the User Pool          | `us-east-1`                   |
| `COGNITO_USER_POOL_ID` | User Pool ID from Cognito console    | `us-east-1_FYVTuevQ9`        |
| `COGNITO_APP_CLIENT_ID`| App Client ID from Cognito console   | `7r4nc65f89pg5adl442fufrig8` |

### Frontend (`frontend/.env`)

| Variable                    | Description                        | Example                       |
|-----------------------------|------------------------------------|-------------------------------|
| `VITE_COGNITO_USER_POOL_ID` | Same User Pool ID                  | `us-east-1_FYVTuevQ9`        |
| `VITE_COGNITO_CLIENT_ID`    | Same App Client ID                 | `7r4nc65f89pg5adl442fufrig8` |
| `VITE_COGNITO_REGION`       | AWS region                         | `us-east-1`                   |

> **Note:** `frontend/.env` is not volume-mounted into Docker — variables are baked in at Vite build time via `import.meta.env`. If you change them, rebuild the frontend container.

---

## 7. Common Issues & Fixes

### Issue 1: `Failed to resolve import "amazon-cognito-identity-js"`

**Cause:** The packages were added to `package.json` but the Docker image had already been built without them.

**Fix:** Rebuild the frontend container:
```bash
docker compose up --build -d frontend
```

---

### Issue 2: `Uncaught ReferenceError: global is not defined`

**Cause:** `amazon-cognito-identity-js` uses Node.js's `global` object, which doesn't exist in browsers.

**Fix:** Add to `vite.config.js`:
```js
define: { global: "globalThis" }
```
Then restart the frontend container.

---

### Issue 3: `PostConfirmation failed with error string indices must be integers`

**Cause:** Initial Lambda code tried to iterate `userAttributes` as a list of `{Name, Value}` objects. In the Post-Confirmation trigger, it is a **plain dict**.

**Fix:**
```python
# Wrong
attrs = {a["Name"]: a["Value"] for a in event["request"]["userAttributes"]}

# Correct
attrs = event["request"]["userAttributes"]
```

---

### Issue 4: Login page in an endless redirect loop

**Cause:** Three separate issues compounded:
1. `docker-compose.yml` was missing the Cognito env vars, so the backend rejected every token with 401.
2. The `api.js` response interceptor redirected to `/login` on any 401, even when already on `/login`.
3. The backend rejected tokens because `verify_aud=True` (PyJWT default) fails for Cognito Access Tokens.

**Fix:**
1. Add Cognito env vars to `docker-compose.yml` backend service.
2. Guard the redirect: `if (error.response?.status === 401 && !onAuthPage)`.
3. Set `options={"verify_aud": False}` in `jwt.decode()` and manually verify `token_use` and `client_id`.

---

### Issue 5: Profile shows a UUID instead of name/email

**Cause:** Cognito Access Tokens don't carry `email` or `name` claims — only ID Tokens do. The backend was storing `sub` (a UUID) as the user's email on first login.

**Fix:** The frontend decodes the ID Token via `getUserInfo(session)` after every login and calls `PATCH /auth/me` to push the real `email` and `display_name` to the backend, which saves them to the database.

---

### Issue 6: Code changes not reflecting in the browser (Docker + Windows)

**Cause:** Docker Desktop on Windows uses WSL2, and inotify file-change events don't always propagate from the Windows filesystem to the container. Vite's hot-module reload doesn't detect the changes.

**Fix:** Restart the frontend container to force Vite to reload from disk:
```bash
docker compose restart frontend
```

---

### Issue 7: Tags missing from "Ask Question" page after `docker compose down -v`

**Cause:** `docker compose down -v` deletes named volumes, including the PostgreSQL data volume. The tags table is empty on the fresh database.

**Fix:** Re-seed the database:
```bash
docker compose exec backend python -m app.utils.seed
```

---

## 8. Reference Links

### AWS Cognito
- [Cognito User Pools — Getting Started](https://docs.aws.amazon.com/cognito/latest/developerguide/getting-started-with-cognito-user-pools.html)
- [User Pool Groups](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-user-groups.html)
- [Lambda Trigger Event Reference](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-working-with-lambda-triggers.html)
- [Pre Sign-up Lambda trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html)
- [Post Confirmation Lambda trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-confirmation.html)
- [Cognito JWT Token structure (Access vs ID Token)](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html)
- [Verifying Cognito JWTs](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)
- [JWKS endpoint format](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html#amazon-cognito-user-pools-using-tokens-manually-inspect)

### boto3 (Python AWS SDK)
- [boto3 Cognito IDP client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp.html)
- [admin_add_user_to_group](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/admin_add_user_to_group.html)
- [list_users_in_group](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/list_users_in_group.html)

### Frontend SDK
- [amazon-cognito-identity-js (npm)](https://www.npmjs.com/package/amazon-cognito-identity-js)
- [amazon-cognito-identity-js (GitHub)](https://github.com/aws-amplify/amplify-js/tree/main/packages/amazon-cognito-identity-js)
- [jwt-decode (npm)](https://www.npmjs.com/package/jwt-decode)

### PyJWT (Python JWT library)
- [PyJWT documentation](https://pyjwt.readthedocs.io/en/stable/)
- [PyJWT — RSA algorithms](https://pyjwt.readthedocs.io/en/stable/algorithms.html)

### Supporting concepts
- [JSON Web Key Sets (JWKS) explained](https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-key-sets)
- [Access Token vs ID Token vs Refresh Token](https://auth0.com/blog/id-token-access-token-what-is-the-difference/)
- [FastAPI — HTTP Bearer security](https://fastapi.tiangolo.com/tutorial/security/http-basic-auth/)
- [Vite — define option (polyfills)](https://vitejs.dev/config/shared-options.html#define)
