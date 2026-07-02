# Security & Privacy — ReputationOS AI

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
- All endpoints are scoped; super_admin bypasses all checks

## Data Protection

### Encryption at Rest
- Database: PostgreSQL (no additional column-level encryption currently)
- Passwords: bcrypt hashing
- Secret fields (JWT_SECRET, Google OAuth tokens): stored in env vars / database; no application-level encryption

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
| Access Control | RBAC with 7 roles, scope enforcement, active subscription gating |
| Authentication | Password policy, MFA (admin), rate limiting |
| Audit Logging | User login and password changes logged |
| Encryption in Transit | HSTS, HTTPS recommended |
| Data Retention | Audit logs purged after 90 days |
| Incident Response | Application-level exception handling, structured logging |

### Gaps
- No automated backup verification
- No penetration testing schedule
- No formal security incident response plan
- No vendor security assessment
- No data classification policy
- No encryption at rest for PII fields
- No session revocation (token blacklist)
