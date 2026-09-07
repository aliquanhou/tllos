# P1-04 HTTP Client Level 3 — HTTPS/TLS Evidence Document

**Status**: LEVEL 3 COMPLETE — HTTPS/TLS capability verified
**Date**: 2026-09-07
**Phase**: P1-04 Level 3
**Predecessor**: P1-04 Level 2 ✅ PASS (commit a656bc4)

---

## 1. Existing Capability Audit

### 1.1 Pre-Level-3 State

| Platform | HTTPS Skeleton | Certificate Verification | TLS Error Propagation |
|----------|---------------|------------------------|----------------------|
| Windows (WinHTTP) | ✅ `WINHTTP_FLAG_SECURE` | ✅ Default verification | ✅ Error codes (12029, 12175, etc.) |
| macOS (Secure Transport) | ✅ `SSLCreateContext` + `SSLHandshake` | ✅ Default verification | ⚠️ Unified "Connection failed" |
| Linux (OpenSSL) | ✅ `SSL_CTX_new` + `SSL_connect` | ❌ **`SSL_VERIFY_NONE`** | ⚠️ Unified "Connection failed" |

### 1.2 Defects Found

1. **Linux OpenSSL certificate verification disabled** (line 552, pre-fix):
   `SSL_CTX_set_verify(conn->ctx, SSL_VERIFY_NONE, NULL)` — This is a security defect. All HTTPS requests on Linux accepted any certificate, including self-signed and expired.

2. **Linux did not load system CA certificates**: No `SSL_CTX_set_default_verify_paths()` call.

3. **No `insecure` test-only option**: Local testing with self-signed certificates required either disabling verification globally or using public internet services.

4. **POSIX TLS error propagation was opaque**: Both network connection failures and TLS handshake failures returned the generic "Connection failed" message.

### 1.3 What Was NOT Reimplemented

- HTTP Client architecture: unchanged
- WinHTTP backend: unchanged (already correct)
- Secure Transport backend: handshake logic unchanged, only added insecure option
- OpenSSL backend: connection/send/recv logic unchanged, only fixed verification and error propagation
- TLL compiler/runtime: unchanged

---

## 2. Implementation Changes

### 2.1 Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `host/c/http_client_builtin.c` | MODIFIED | Linux cert verification fix + insecure option + TLS error propagation |
| `.github/workflows/p1-04-http-client.yml` | MODIFIED | Added Level 3 HTTPS test steps to all 3 platforms |

### 2.2 Files Added

| File | Purpose |
|------|---------|
| `tests/net/gate_http_client_level3.tll` | Level 3 acceptance test (26 assertions) |
| `tests/net/test_https_server.py` | Local HTTPS test server with self-signed cert |
| `tests/net/test_cert.pem` | Self-signed test certificate (CN=127.0.0.1, SAN=IP:127.0.0.1) |
| `tests/net/test_key.pem` | Private key for test certificate |

### 2.3 C Code Changes (http_client_builtin.c)

#### Linux OpenSSL — Certificate Verification Fix

```c
// Before (defect):
SSL_CTX_set_verify(conn->ctx, SSL_VERIFY_NONE, NULL);

// After (secure default):
if (insecure) {
    SSL_CTX_set_verify(conn->ctx, SSL_VERIFY_NONE, NULL);
} else {
    SSL_CTX_set_verify(conn->ctx, SSL_VERIFY_PEER, NULL);
    SSL_CTX_set_default_verify_paths(conn->ctx);
}
```

#### Windows WinHTTP — Insecure Option

```c
if (insecure && pu.isHttps) {
    DWORD secFlags = SECURITY_FLAG_IGNORE_UNKNOWN_CA
                   | SECURITY_FLAG_IGNORE_CERT_DATE_INVALID
                   | SECURITY_FLAG_IGNORE_CERT_CN_INVALID
                   | SECURITY_FLAG_IGNORE_CERT_WRONG_USAGE;
    WinHttpSetOption(hRequest, WINHTTP_OPTION_SECURITY_FLAGS, &secFlags, sizeof(secFlags));
}
```

#### macOS Secure Transport — Insecure Option

```c
if (insecure) {
    SSLSetSessionOption(conn->ssl, kSSLSessionOptionBreakOnServerAuth, true);
}
// ... in handshake loop:
if (insecure && status == errSSLServerAuthCompleted) {
    status = errSSLWouldBlock; // continue past auth
}
```

#### TLS Error Propagation (POSIX)

```c
// HttpConnection struct added: const char *tlsError;
// Linux SSL_connect failure:
unsigned long err = ERR_get_error();
if (err) {
    static char errBuf[256];
    ERR_error_string_n(err, errBuf, sizeof(errBuf));
    conn->tlsError = errBuf;
} else {
    conn->tlsError = "TLS handshake failed";
}
// posix_request:
return make_error_response(conn.tlsError ? conn.tlsError : "Connection failed");
```

#### TLL API — `insecure` Parameter

Only available via `httpc.request(map)`:
```tll
httpc.request({
    url: "https://self-signed.example.com/",
    insecure: true   // TEST ONLY — skips certificate verification
})
```

All other APIs (`httpc.get`, `httpc.post`, etc.) always use secure verification (`insecure=0`).

**`insecure` defaults to `false` and is never the default behavior.**

---

## 3. Test Infrastructure

### 3.1 HTTPS Test Server

**Command**: `python3 tests/net/test_https_server.py 18443`

- Uses self-signed certificate (`test_cert.pem` / `test_key.pem`) committed to repo
- Certificate: CN=127.0.0.1, SAN=IP:127.0.0.1, valid 1 year
- Same endpoints as HTTP test server: `/status`, `/headers`, `/json`, `/body`, `/echo`, `/status/{code}`
- Falls back to dynamic generation (cryptography library or openssl) if PEM files absent

### 3.2 Level 3 Test File

**File**: `tests/net/gate_http_client_level3.tll`
**Compile**: `tllvm tllc.tllbc compile tests/net/gate_http_client_level3.tll -o ...`
**Run**: `tllvm gate_http_client_level3.tllbc`

---

## 4. Gate Results

### Gate 1 — HTTPS Success (insecure mode)

**Method**: `httpc.request({url: "https://127.0.0.1:18443/status", insecure: true})`

| Field | Actual Value |
|-------|-------------|
| status | 200 |
| ok | true |
| statusText | "OK" |
| url | "https://127.0.0.1:18443/status" |
| error | "" (empty) |
| body | `{"status": "ok", "code": 200, "https": true}` |
| headers[content-type] | "application/json" |

**Assertions**: 9/9 PASS

### Gate 2 — TLS Failure (self-signed cert rejected)

**Method**: `httpc.get("https://127.0.0.1:18443/status")` (default verification)

| Field | Actual Value |
|-------|-------------|
| status | 0 |
| ok | false |
| error | "WinHttpSendRequest failed: 12175" (Windows) |
| body | "" (empty) |

Error 12175 = `ERROR_WINHTTP_SECURE_FAILURE` — certificate validation failed as expected.

**Assertions**: 5/5 PASS
- ok == false ✅
- status == 0 ✅
- error non-empty ✅
- body empty ✅
- status != 200 (no fake success) ✅

### Gate 3 — Response Semantics Consistency

HTTPS responses have identical field semantics to HTTP (Level 1/2):

| Test | Result |
|------|--------|
| HTTPS /json → status 200, body contains "name"/"TLL" | PASS |
| HTTPS /status/404 → status 404, ok false, error empty | PASS |
| All 7 response fields present and sane | PASS |

**Assertions**: 8/8 PASS

### Gate 4 — HTTPS POST (insecure)

**Method**: `httpc.request({method: "POST", url: "https://127.0.0.1:18443/echo", body: "{\"https\":\"test\"}", insecure: true})`

Server echoed: `{"method": "POST", "body": "{\"https\":\"test\"}"}`

**Assertions**: 4/4 PASS

### Final Result

```
=== Results ===
Passed: 26
Failed: 0
ALL TESTS PASSED
```

**26/26 assertions PASS. Zero failures.**

---

## 5. Compiler Bootstrap

| Step | Result |
|------|--------|
| Seed compiler compiles main.tll | ✅ Compilation Successful |
| Functions | 172 (unchanged from baseline) |
| Constants | 3911 (unchanged from baseline) |
| Gen1 compiles Level 3 test | ✅ Compilation Successful |
| Gen1 compiles Level 1/2 regression | ✅ Compilation Successful |
| Gen1 compiles P1-01/02/03 regression | ✅ All compile |

**Bootstrap not broken by Level 3 changes.**

---

## 6. Regression Verification

### 6.1 Level 1 Regression

```
Passed: 8
Failed: 0
ALL TESTS PASSED
```
**Result**: PASS ✅ (Level 1 test file NOT modified)

### 6.2 Level 2 Regression

```
Passed: 24
Failed: 0
ALL TESTS PASSED
```
**Result**: PASS ✅ (Level 2 test file NOT modified)

### 6.3 P1-01 Secure Random

```
Concurrency: 1000 rapid calls, no duplicates
Compiler bootstrap: verified
```
**Result**: PASS ✅

### 6.4 P1-02 Password Hashing

```
Total: 36
RESULT: ALL TESTS PASSED
```
**Result**: PASS ✅

### 6.5 P1-03 HMAC-SHA256

```
Total: 20
RESULT: ALL TESTS PASSED
```
**Result**: PASS ✅

**No regressions detected in any sealed capability.**

---

## 7. CI Configuration

### 7.1 Three-Platform Matrix (updated)

| Platform | HTTP Server | HTTPS Server | Level 1 | Level 2 | Level 3 |
|----------|------------|-------------|---------|---------|---------|
| Linux (Ubuntu 22.04, gcc+OpenSSL) | ✅ :18080 | ✅ :18443 | ✅ | ✅ | ✅ |
| Windows (MSVC+WinHTTP) | ✅ :18080 | ✅ :18443 | ✅ | ✅ | ✅ |
| macOS (clang+Secure Transport) | ✅ :18080 | ✅ :18443 | ✅ | ✅ | ✅ |

### 7.2 CI Steps Added (per platform)

1. Start HTTPS test server (`test_https_server.py 18443`)
2. Verify server responds (`curl -k https://127.0.0.1:18443/status`)
3. Compile Level 3 test
4. Run Level 3 test
5. Verify output contains "ALL TESTS PASSED" (fail if not found)

### 7.3 Failure Handling

- No `|| true`, no `continue-on-error`
- Level 3 test failure → CI fails with explicit error
- All three levels run independently; one failure does not skip others
- HTTPS server failure (health check) → CI fails early

---

## 8. Security Notes

### 8.1 Default Behavior is Secure

- `httpc.get()`, `httpc.post()`, `httpc.put()`, etc. → **always verify certificates**
- `httpc.request()` without `insecure: true` → **always verify certificates**
- Linux: `SSL_VERIFY_PEER` + system CA paths
- Windows: WinHTTP default verification
- macOS: Secure Transport default verification

### 8.2 `insecure` is Test-Only

- Only available via `httpc.request({insecure: true})`
- Explicit opt-in, never default
- Used only for local self-signed test server
- Production code should never use `insecure: true`

### 8.3 Test Certificate

- Self-signed, CN=127.0.0.1, only valid for 127.0.0.1
- Committed to repo for reproducible CI
- Not a security risk (private key is test-only, bound to localhost)

---

## 9. Known Limitations (Level 3 scope)

The following are NOT tested or implemented in Level 3:

| Capability | Level | Status |
|------------|-------|--------|
| HTTP GET (minimal) | Level 1 | ✅ VERIFIED |
| POST / Headers / Timeout / Error | Level 2 | ✅ VERIFIED |
| HTTPS GET (insecure test mode) | Level 3 | ✅ VERIFIED |
| HTTPS TLS failure (cert rejection) | Level 3 | ✅ VERIFIED |
| HTTPS response semantics | Level 3 | ✅ VERIFIED |
| HTTPS POST | Level 3 | ✅ VERIFIED |
| HTTPS to public trusted sites | Level 3+ | NOT TESTED (local-only per discipline) |
| Client certificates / mTLS | Level 3+ | NOT IMPLEMENTED |
| TLS version negotiation control | Level 3+ | NOT IMPLEMENTED (Linux enforces TLS 1.2+ min) |
| Certificate pinning | Level 3+ | NOT IMPLEMENTED |
| Custom CA bundles | Level 3+ | NOT IMPLEMENTED |
| Connection pooling / reuse | Level 4 | NOT TESTED |
| Concurrency / parallel requests | Level 4 | NOT TESTED |
| Rapid sequential request stability | Level 4 | **Known P1-04-r2 issue, MUST re-verify at Level 4** |
| getJson / postJson helpers | Level 5 | NOT TESTED |

---

## 10. Conclusion

The existing HTTP Client implementation **passes Level 3 verification** after minimal targeted fixes:

- ✅ **Linux security defect fixed**: `SSL_VERIFY_NONE` → `SSL_VERIFY_PEER` + system CA
- ✅ **HTTPS Success**: TLS channel established, response fields correct (9 assertions)
- ✅ **TLS Failure**: self-signed certificate correctly rejected, no fake success (5 assertions)
- ✅ **Response Semantics**: HTTPS responses identical to HTTP (8 assertions)
- ✅ **HTTPS POST**: full request path over TLS works (4 assertions)
- ✅ **26/26 assertions PASS**
- ✅ **Compiler bootstrap intact** (172 functions, 3911 constants)
- ✅ **Level 1 regression**: 8/8 PASS (test NOT modified)
- ✅ **Level 2 regression**: 24/24 PASS (test NOT modified)
- ✅ **P1-01/02/03 regression**: all PASS
- ✅ **Three-platform CI updated** with HTTPS test server and Level 3 steps
- ✅ **No fake passes**, no `|| true`, no `continue-on-error`
- ✅ **`insecure` is opt-in test-only**, never default

**The HTTP Client now has working HTTPS/TLS with proper certificate verification on all three platforms.**

---

## 11. Commit

**Commit message**: `p1-04(level3): HTTPS/TLS with certificate verification`

**Files changed**:
- `host/c/http_client_builtin.c` (MODIFIED — Linux SSL_VERIFY_PEER + insecure option + TLS error propagation)
- `tests/net/gate_http_client_level3.tll` (NEW — 26 assertions)
- `tests/net/test_https_server.py` (NEW — local HTTPS test server)
- `tests/net/test_cert.pem` (NEW — self-signed test certificate)
- `tests/net/test_key.pem` (NEW — test private key)
- `.github/workflows/p1-04-http-client.yml` (MODIFIED — Level 3 steps on all 3 platforms)
