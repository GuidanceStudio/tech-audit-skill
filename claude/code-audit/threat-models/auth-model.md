# Threat model — auth model

JWT, session, cookie, and bearer patterns. Most security bugs in B2B SaaS sit here.

## JWT — verification gotchas

Common pitfalls when verifying tokens:

### `alg=none` acceptance

Some JWT libraries default to accepting tokens with `alg: none`. An attacker presents an unsigned token; verification passes.

**Detect**:

```sh
# Search for permissive JWT decode
grep -rnE "jwt\.decode\(.*verify=False|jwt\.verify\(.*algorithms=\[\]|allow_unsafe" .
```

**Fix**: explicitly list allowed algorithms, NEVER `none`.

### Algorithm confusion (RS256 → HS256)

If the server is configured to "verify with the public key" but the JWT library uses the public key as an HMAC secret when `alg: HS256` is presented:

- Attacker takes the public key (which is, well, public).
- Mints a token signed with HMAC-SHA256 using the public key.
- Sets `alg: HS256`.
- Library happily verifies.

**Fix**: lock the verification algorithm explicitly (`algorithms=["RS256"]` only).

### kid confusion

`kid` (key ID) in the JWT header tells the verifier which key to use. If the verifier trusts the `kid` and the application uses `kid` as a file path or DB key:

```python
# WRONG
key = open(f"keys/{token.kid}.pem").read()
```

Attacker sets `kid: ../../etc/passwd` or `kid: <controllable URL>`. Path traversal or SSRF.

**Fix**: maintain a `kid → key` mapping in the verifier; reject unknown kids.

### Expired token still trusted

`exp` not enforced:

```python
jwt.decode(token, key, algorithms=["RS256"], options={"verify_exp": False})
```

The `verify_exp=False` is sometimes leftover from a test. → 🔴.

### Audience / issuer not checked

Multi-tenant or multi-service deployments need `aud` and `iss` claim checks. A token minted for service A should not be accepted by service B.

```python
jwt.decode(token, key,
    algorithms=["RS256"],
    audience="cerase-gateway",
    issuer="cerase-control-plane",
)
```

Missing `audience=` or `issuer=` parameter → 🟡.

## Session fixation

After login, the session ID MUST rotate:

```php
session()->regenerate();          // Laravel
session.rotate()                  // Python sessions library
request.session.cycle_key()       // Django
```

Missing on the login route → 🔴 (an attacker who pre-set the session cookie pre-login can ride the post-login session).

## CSRF / origin

State-changing endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) need either:

- CSRF middleware (cookie-based session auth), OR
- Origin / Referer check (modern alternative), OR
- Custom header that browsers can't auto-send (e.g. `X-Requested-With`) + CORS preflight, OR
- Token in body that's not stored in a cookie.

Routes without any of these → 🔴 for cookie-auth, 🟡 for token-auth.

## Trusted headers

Auth code MUST NOT trust headers without verification. Common offenders:

- `X-Forwarded-User` from the gateway: only trust if the gateway authoritatively SET it (and the network path ensures clients can't inject it).
- `X-Real-IP` for rate limiting: same logic.
- `X-Tenant-Id`: never trust without verification.

**Detect**:

```sh
grep -rnE 'request\.headers?\.get\([\'\"](X-[A-Z][a-zA-Z-]+)' .
```

Each match → "is this header trusted, and how is that trust established?"

## Password / credential handling

- `Hash::check()` / `bcrypt` / `argon2` — never compare with `===` or `strcmp`.
- Credential transmission only over HTTPS (force HSTS).
- Failed-login rate limiting per identifier (not per IP — abuse defeats per-IP).

## Token storage

Where does the client store tokens? Each storage has trade-offs:

- **localStorage**: vulnerable to XSS but immune to CSRF.
- **httpOnly cookie**: immune to XSS but vulnerable to CSRF; needs CSRF defense.
- **memory only**: best, but doesn't survive page refresh.

For a B2B admin SPA: httpOnly cookie + SameSite=Strict + CSRF token is the common choice.

## API key (long-lived bearer) handling

- Stored hashed at rest (you can't display the key after creation).
- Key prefix shown for UI identification (`sk_live_...`).
- Last-used timestamp tracked.
- Revocation propagation timing documented (cache TTL, etc.).

## Cross-references

- `dimensions/D04-security-posture.md`.
- `languages/<stack>.md` — framework-specific auth gotchas.
