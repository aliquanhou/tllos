# P1-04 HTTP Client Level 2 — Evidence Document

**Status**: LEVEL 2 COMPLETE — POST + Custom Headers + Timeout + Error Handling verified
**Date**: 2026-09-07
**Phase**: P1-04 Level 2
**Predecessor**: P1-04 Level 1 ✅ PASS (commit 0d1999e)

---

## 1. Objective

Verify that the existing HTTP Client implementation supports Level 2 capabilities:

```
POST with body → custom request headers → timeout parameter → error handling (404/500/connection refused)
```

**This phase does NOT modify C code.** The existing `http_client_builtin.c` is the object under verification.

**Level 3 (HTTPS/TLS), Level 4 (connection reuse/concurrency/stability), Level 5 (JSON helpers) are NOT addressed in Level 2.**

---

## 2. Implementation Status

### 2.1 Existing Implementation (NOT modified)

| Component | File | Status |
|-----------|------|--------|
| C native HTTP client | `host/c/http_client_builtin.c` | 35,768 bytes, unchanged |
| TLL codegen binding | `compiler/codegen.tll` L1772-1782 | httpc idx 200-208, unchanged |
| TLL API verified | `httpc.get(url, headers?)`, `httpc.post(url, body, headers?)`, `httpc.request(map)` | All working |

### 2.2 Changes Made in Level 2

| File | Change | Reason |
|------|--------|--------|
| `tests/net/gate_http_client_level2.tll` | NEW | Level 2 acceptance test (24 assertions) |
| `.github/workflows/p1-04-http-client.yml` | MODIFIED | Added Level 2 test steps to all 3 platforms |
| `docs/P1-04-HTTP-CLIENT-LEVEL2-EVIDENCE.md` | NEW | This evidence document |

**Zero C code modifications.** Level 1 test file (`gate_http_client_minimal.tll`) is NOT modified.

---

## 3. Test Commands

### 3.1 Server Command

```bash
python3 tests/net/test_server.py 18080
```

Endpoints used:
- `POST /echo` → echoes method, path, headers, body
- `GET /headers` → returns received request headers
- `GET /status/404` → returns HTTP 404
- `GET /status/500` → returns HTTP 500
- `http://127.0.0.1:19999/` → connection refused (no server)

### 3.2 Test Compile Command

```bash
./host/c/tllvm tools/TLLC/tllc_l2.tllbc compile tests/net/gate_http_client_level2.tll -o tests/net/gate_http_client_level2.tllbc
```

**Result**: Compilation Successful (8 type warnings, non-blocking)

### 3.3 Test Run Command

```bash
./host/c/tllvm tests/net/gate_http_client_level2.tllbc
```

---

## 4. Actual Results

### 4.1 Section 1: POST with body

```
status=200 ok=true
body={"method": "POST", "path": "/echo", "headers": {...}, "body": "{\"name\":\"TLL\",\"version\":\"1.0\"}"}
```

| Assertion | Result |
|-----------|--------|
| POST returns status 200 | PASS |
| POST ok is true | PASS |
| POST body contains TLL | PASS |
| POST body contains version | PASS |
| POST body contains method POST | PASS |

### 4.2 Section 2: POST with Content-Type header

| Assertion | Result |
|-----------|--------|
| POST with Content-Type status 200 | PASS |
| POST with headers body contains TLL | PASS |

### 4.3 Section 3: Custom request headers on GET

```
body={"headers": {"Connection": "Keep-Alive", "Accept": "application/json", "User-Agent": "TLL-HTTP-Client/1.0", "X-Test-Header": "TLL-Level2", "Host": "127.0.0.1:18080"}}
```

| Assertion | Result |
|-----------|--------|
| GET with custom headers status 200 | PASS |
| Server received X-Test-Header | PASS |
| Server received TLL-Level2 value | PASS |
| Server received Accept header | PASS |

### 4.4 Section 4: Error handling - HTTP 404

```
status=404 ok=false
```

| Assertion | Result |
|-----------|--------|
| 404 response status is 404 | PASS |
| 404 response ok is false | PASS |
| 404 body is non-empty | PASS |

### 4.5 Section 5: Error handling - HTTP 500

```
status=500 ok=false
```

| Assertion | Result |
|-----------|--------|
| 500 response status is 500 | PASS |
| 500 response ok is false | PASS |

### 4.6 Section 6: Error handling - connection refused

```
status=0 ok=false error=[WinHttpSendRequest failed: 12029]
```

| Assertion | Result |
|-----------|--------|
| Connection refused ok is false | PASS |
| Connection refused status is 0 | PASS |
| Connection refused error is non-empty | PASS |

**Note**: Error message is platform-specific (Windows: WinHttpSendRequest failed: 12029). Linux/macOS will show platform-appropriate error messages. The assertion only checks that error is non-empty, not the exact message.

### 4.7 Section 7: Timeout parameter via httpc.request

```
request: {method: "GET", url: "http://127.0.0.1:18080/status", timeout: 10000}
status=200 ok=true
```

| Assertion | Result |
|-----------|--------|
| request with timeout returns 200 | PASS |
| request with timeout ok is true | PASS |
| request with timeout body non-empty | PASS |

**Note**: Level 2 verifies that the timeout parameter is accepted and does not break normal requests. Actual timeout behavior (request that exceeds timeout) is deferred to a later level because it requires a slow server endpoint.

### 4.8 Section 8: httpc.request with POST

```
request: {method: "POST", url: ".../echo", body: "{\"test\":\"request-post\"}"}
status=200
```

| Assertion | Result |
|-----------|--------|
| request POST returns 200 | PASS |
| request POST body contains request-post | PASS |

### 4.9 Final Result

```
=== Results ===
Passed: 24
Failed: 0

ALL TESTS PASSED
```

**24/24 assertions PASS. Zero failures.**

---

## 5. Compiler Bootstrap

| Step | Result |
|------|--------|
| Seed compiler compiles main.tll | ✅ Compilation Successful |
| Functions | 172 |
| Constants | 3911 |
| Gen1 compiles Level 2 test | ✅ Compilation Successful |
| Gen1 compiles Level 1 test (regression) | ✅ Compilation Successful |
| Gen1 compiles P1-01/02/03 regression tests | ✅ All compile |

**Bootstrap not broken by Level 2 changes.**

---

## 6. Regression Verification

### 6.1 Level 1 Regression

```
=== Results ===
Passed: 8
Failed: 0
ALL TESTS PASSED
```
**Result**: PASS ✅ (Level 1 test file NOT modified)

### 6.2 P1-01 Secure Random

```
Concurrency: 1000 rapid calls, no duplicates
Compiler bootstrap: verified
```
**Result**: PASS ✅

### 6.3 P1-02 Password Hashing

```
PASS: 36
FAIL: 0
Total: 36
RESULT: ALL TESTS PASSED
```
**Result**: PASS ✅

### 6.4 P1-03 HMAC-SHA256

```
PASS: 20
FAIL: 0
Total: 20
RESULT: ALL TESTS PASSED
```
**Result**: PASS ✅

**No regressions detected in Level 1 or P1-01/02/03 sealed capabilities.**

---

## 7. CI Configuration

### 7.1 Updated Workflow

File: `.github/workflows/p1-04-http-client.yml`
Name: `P1-04 HTTP Client Level 1 Tests` (will be renamed in a future commit to reflect Level 1+2)

### 7.2 Three-Platform Matrix (updated)

| Platform | Level 1 Test | Level 2 Test |
|----------|--------------|--------------|
| Linux (Ubuntu 22.04, gcc+OpenSSL) | ✅ Added | ✅ Added |
| Windows (MSVC+WinHTTP) | ✅ Added | ✅ Added |
| macOS (clang+Secure Transport) | ✅ Added | ✅ Added |

### 7.3 CI Steps Added (per platform)

1. Compile Level 2 test
2. Run Level 2 test
3. Verify output contains "ALL TESTS PASSED" (fail if not found)

### 7.4 Trigger Paths Updated

Added: `tests/net/gate_http_client_level2.tll`

### 7.5 Failure Handling

- No `|| true`, no `continue-on-error`
- Level 2 test failure → CI fails with explicit error message
- Level 1 and Level 2 tests run independently; one failure does not skip the other

---

## 8. Known Limitations (Level 2 scope)

The following are NOT tested in Level 2 and remain for subsequent levels:

| Capability | Level | Status |
|------------|-------|--------|
| HTTP GET (minimal) | Level 1 | ✅ VERIFIED |
| POST with body | Level 2 | ✅ VERIFIED |
| Custom request headers | Level 2 | ✅ VERIFIED |
| Timeout parameter (accepted) | Level 2 | ✅ VERIFIED |
| Error handling (404/500/connection refused) | Level 2 | ✅ VERIFIED |
| httpc.request full control | Level 2 | ✅ VERIFIED |
| Actual timeout behavior (slow server) | Level 2+ | Not tested (requires slow endpoint) |
| PUT / DELETE / HEAD / PATCH | Level 2+ | Not tested (API exists but not verified) |
| HTTPS / TLS | Level 3 | Not tested |
| Connection pooling / reuse | Level 4 | Not tested |
| Concurrency / parallel requests | Level 4 | Not tested |
| Rapid sequential request stability | Level 4 | **Known issue from P1-04-r2, MUST be re-verified at Level 4** |
| getJson / postJson helpers | Level 5 | Not tested |

**Important**: The rapid sequential request stability issue (known from P1-04-r2, involving SO_LINGER and graceful delay fixes) is NOT addressed or re-verified in Level 2. It is explicitly deferred to Level 4 where connection reuse and concurrency will be tested. Level 2 tests run requests sequentially with natural delays between test sections, which does not stress the rapid-request path.

---

## 9. Conclusion

The existing 35KB `http_client_builtin.c` implementation **passes Level 2 verification** without any C code modifications:

- ✅ POST with body (body correctly sent and echoed)
- ✅ Custom request headers (X-Test-Header, Accept, Content-Type all received by server)
- ✅ Timeout parameter (accepted via httpc.request, does not break normal requests)
- ✅ Error handling (HTTP 404 → status=404/ok=false, HTTP 500 → status=500/ok=false, connection refused → status=0/ok=false/error non-empty)
- ✅ httpc.request full control (GET and POST both work)
- ✅ 24/24 assertions PASS
- ✅ Compiler bootstrap intact (172 functions, 3911 constants)
- ✅ Level 1 regression: 8/8 PASS (Level 1 test NOT modified)
- ✅ P1-01 Secure Random: PASS
- ✅ P1-02 Password Hashing: 36/36 PASS
- ✅ P1-03 HMAC-SHA256: 20/20 PASS
- ✅ Three-platform CI updated with Level 2 test steps
- ✅ No fake passes, no `|| true`, no `continue-on-error`

**The existing HTTP Client implementation qualifies for Level 2 (POST + headers + timeout + error handling).**

---

## 10. Commit

**Commit message**: `p1-04(level2): POST + custom headers + timeout + error handling`

**Files changed**:
- `tests/net/gate_http_client_level2.tll` (NEW)
- `.github/workflows/p1-04-http-client.yml` (MODIFIED — added Level 2 steps to all 3 platforms)
- `docs/P1-04-HTTP-CLIENT-LEVEL2-EVIDENCE.md` (NEW)

**Zero C code modifications. Level 1 test file NOT modified.**
