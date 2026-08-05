# GitHub OAuth & Security Architecture

TestPilot AI is a **GitHub-native platform**. Authentication and repository access are managed securely through GitHub OAuth and JWT session management.

---

## Authentication Flow

```
 ┌──────────────┐         1. Redirect to GitHub OAuth         ┌──────────────────┐
 │   User App   │ ──────────────────────────────────────────> │   GitHub.com     │
 └──────┬───────┘                                             └────────┬─────────┘
        │                                                              │
        │ 3. Exchange Code for JWT                                     │ 2. Return Code
        ▼                                                              ▼
 ┌──────────────┐         4. Issue Access Token & Cookie       ┌──────────────────┐
 │ Backend API  │ <─────────────────────────────────────────── │ Auth Callback    │
 └──────────────┘                                              └──────────────────┘
```

### Key Security Implementations:
1. **GitHub Authorization**: Users authenticate directly on GitHub.com (`/login/oauth/authorize`).
2. **Zero Password Storage**: TestPilot AI does not store user passwords, eliminating credential vulnerability.
3. **Session Management**:
   - Access tokens issued as JWTs.
   - Refresh tokens stored in `HTTP-only`, `SameSite=Lax` secure cookies.
4. **React StrictMode Double-Exchange Guard**:
   - Auth callback includes a `useRef(false)` single-execution flag to prevent double-firing single-use OAuth authorization codes.
