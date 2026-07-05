# Security & Privacy — ReputationOS AI

> Last updated: 2026-07-03 (post security-hardening pass)

## Authentication

### Password Policy
- Minimum 8 characters
- Requires uppercase, lowercase, digit, and special character
- Validated client-side (strength meter with 6 levels) and server-side (Pydantic validators)
- Passwords hashed with bcrypt via passlib

### Rate Limiting
- In-memory rate limiter on `/api/auth/login`: max 5 attempts per 300s per IP
- Returns HTTP 429 when exceeded

### Session Management
- Stateless JWT tokens (HS256)
- Token payload includes `exp`, `iat`, and `jti` claims
- Default expiry: 24 hours
- No refresh tokens; re-authentication required on expiry
- 401 responses clear local storage and redirect to login

### Password Reset / Account Recovery
- `POST /api/auth/forgot-password` — generates a cryptographically random token (48 bytes, URL-safe)
- Token stored as bcrypt hash in `password_reset_tokens` table with 1-hour expiry
- `POST /api/auth/reset-password` — verifies token and updates password
- Tokens are single-use; marked as `used` after successful reset

### Multi-Factor Authentication (MFA)
- TOTP-based (RFC 6238) via pyotp library
- Only admin roles (super_admin, agency_admin, client_admin) can enable
- QR code provisioning URI generated for authenticator apps
- Login flow: if MFA enabled, returns `mfa_required` flag + short-lived MFA token
- MFA token (5 min expiry) exchanged for full access token after TOTP verification
- Setup: call `/api/auth/mfa/setup` → user scans QR → call `/api/auth/mfa/verify`
- Disable: requires valid TOTP code via `/api/auth/mfa/disable`

## Authorization

### Role-Based Access Control
7 levels: super_admin (100), agency_admin (80), client_admin (60), marketing_manager (40), customer_support (30), branch_manager (20), read_only (10)

### Scope Enforcement
- `check_location_access()` — verifies user can access a Location by role hierarchy and tenant linkage
- `verify_client_access()` — analogous for Client-level access
- `check_review_access()` — resolves a Review through its Location to enforce the same chain
- All endpoints are scoped; super_admin bypasses all checks
- **July 2026 audit:** 13 cross-tenant access holes were found and fixed across by-ID endpoints
  (reviews, replies, brand voice, smart rules, competitors, alerts, SEO rankings, support tickets,
  scheduled reports, chat agent location context, location creation). Regression coverage lives in
  `tests/test_tenant_isolation.py`.

### OAuth Flow Security (Google Business Profile)
- `state` parameter is a signed JWT (10-minute expiry, nonce, purpose claim) — CSRF-protected;
  forged or raw-client-id states are rejected with 400
- Missing refresh token at connect time fails loudly; no sentinel values are stored
- Per-agency OAuth credentials: each agency uses its own Google Cloud project

## Data Protection

### Encryption at Rest
- Passwords: bcrypt hashing
- Google OAuth access/refresh tokens and agency OAuth client secrets: **Fernet-encrypted at the
  column level** (`app/core/crypto.py`, `EncryptedToken` type, `enc:v1:` prefix). Key comes from
  `ENCRYPTION_KEY`; legacy plaintext rows remain readable and re-encrypt on next save
- Key management: `ENCRYPTION_KEY` is required in production (startup guard); development derives
  a key from `JWT_SECRET`
- Other PII columns (emails, names, review text): stored unencrypted in PostgreSQL

### Production Startup Guards
The application refuses to start with `ENVIRONMENT=production` if any of:
- `JWT_SECRET` is missing or still the shipped default
- `ENCRYPTION_KEY` is not set
- `DEMO_MODE` is enabled (mock-data fallback must never run for real tenants)

### Encryption in Transit
- HSTS: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- CORS: restricted to configured origins
- HTTPS: recommended in production; no TLS termination in application layer

### Security Headers
| Header | Value |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |

## Audit Logging

- All `user.login` and `user.password_change` events logged to `audit_logs` table
- Captures: agency_id, user_id, action, resource_type, resource_id, details (JSON), ip_address
- Audit logs retrievable via `GET /api/audit` with filters (action, user_id, resource_type, limit, offset)
- Retention: logs older than 90 days (configurable via `AUDIT_LOG_RETENTION_DAYS`) are purged daily by scheduler

## GDPR / Data Privacy

### Data Export
- `GET /api/users/me/export` — returns JSON with:
  - Account details (email, name, role, created_at)
  - Reviews authored by the user
  - Review replies approved by the user
  - Chat sessions and messages
  - Audit log entries

### Account Deletion
- `DELETE /api/users/me` — anonymizes account:
  - Sets `is_active = False`
  - Replaces email with `deleted-{uuid}@anon.reputationos.ai`
  - Replaces name with `Deleted User`
- Associated records (reviews, replies, etc.) remain for platform integrity but are disassociated from the user identity
- Physical deletion of PII is a manual DBA operation; the application only anonymizes

### Retention Policy
- Scheduler runs `cleanup_old_audit_logs()` daily
- Deletes `AuditLog` rows where `created_at < now() - AUDIT_LOG_RETENTION_DAYS`
- Default retention: 90 days

## SOC 2 Readiness

### Current Controls
| Category | Status |
|---|---|
| Access Control | RBAC with 7 roles, scope enforcement (audited July 2026), active subscription gating |
| Authentication | Password policy, MFA (admin), rate limiting, OAuth CSRF protection |
| Audit Logging | User login and password changes logged |
| Encryption in Transit | HSTS, HTTPS recommended |
| Encryption at Rest | OAuth tokens and client secrets (Fernet); passwords (bcrypt) |
| Data Retention | Audit logs purged after 90 days |
| Deployment Safety | Production startup guards; advisory-locked scheduler; Alembic-only schema in prod |
| Incident Response | Application-level exception handling, structured logging |

### Gaps
- No automated backup and restore process (blocker before first paying customer — see roadmap Phase 6)
- No external penetration test or security review (SOC 2 posture is self-assessed)
- No formal security incident response plan
- No vendor security assessment
- No data classification policy
- No encryption at rest for general PII fields (emails, names, review text)
- No session revocation (token blacklist); stateless 24h JWTs
- JWTs stored in browser localStorage (XSS-exfiltratable; httpOnly cookies would be safer)
