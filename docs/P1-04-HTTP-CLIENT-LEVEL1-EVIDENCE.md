# P1-04 HTTP Client Level 1 — Evidence Document

**Status**: LEVEL 1 COMPLETE — Minimal HTTP GET verified
**Date**: 2026-09-07
**Phase**: P1-04 Level 1
**Predecessor**: P1-03 HMAC-SHA256 🔒 SEALED

---

## 1. Objective

Verify that the existing HTTP Client implementation (`host/c/http_client_builtin.c`, 35KB, idx 200-208) can complete a true minimal closed loop:

```
TLL → httpc.get(url) → HTTP Server → Response → status/headers/body → assertions → Evidence → CI
```

**This phase does NOT reimplement HTTP Client.** The existing implementation is the object under verification.

---

## 2. Implementation Status

### 2.1 Existing Implementation (NOT modified)

| Component | File | Size | Platforms |
|-----------|------|------|-----------|
| C native HTTP client | `host/c/http_client_builtin.c` | 35,768 bytes | Windows (WinHTTP), Linux (POSIX+OpenSSL), macOS (POSIX+Secure Transport) |
| TLL codegen binding | `compiler/codegen.tll` L1772-1782 | — | httpc module idx 200-208 |
| TLL linker registration | `compiler/linker.tll` L146 | — | "httpc" in stdlibs |
| Builtin dispatch | `host/c/builtin.c` L491-492 | — | idx 200-209 → httpc_builtin_invoke |

### 2.2 Changes Made in Level 1

| File | Change | Reason |
|------|--------|--------|
| `tests/net/gate_http_client_minimal.tll` | NEW | Minimal acceptance test (8 assertions) |
| `.github/workflows/p1-04-http-client.yml` | NEW | Three-platform CI for Level 1 |
| `docs/P1-04-HTTP-CLIENT-LEVEL1-EVIDENCE.md` | NEW | This evidence document |

**Zero C code modifications.** The existing `http_client_builtin.c` passed Level 1 verification as-is.

---

## 3. Test Commands

### 3.1 Server Command

```bash
# Linux / macOS
python3 tests/net/test_server.py 18080 &

# Windows (cmd)
start /B python tests\net\test_server.py 18080
```

Server endpoint used: `GET http://127.0.0.1:18080/status`
Returns: HTTP 200, `Content-Type: application/json`, body `{"status": "ok", "code": 200}`

### 3.2 Compiler Bootstrap Command

```bash
./host/c/tllvm tools/TLLC/tllc.tllbc compile tools/TLLC/main.tll -o tools/TLLC/tllc_level1.tllbc
```

**Result**: Compilation Successful, Functions: 172, Constants: 3911

### 3.3 Test Compile Command

```bash
./host/c/tllvm tools/TLLC/tllc_level1.tllbc compile tests/net/gate_http_client_minimal.tll -o tests/net/gate_http_client_minimal.tllbc
```

**Result**: Compilation Successful (1 type warning, non-blocking)

### 3.4 Test Run Command

```bash
./host/c/tllvm tests/net/gate_http_client_minimal.tllbc
```

---

## 4. Actual Result

### 4.1 Response Field Inspection (actual values)

```
=== P1-04 Level 1: Minimal HTTP GET ===

GET http://127.0.0.1:18080/status

--- Response Field Inspection ---
  status     = 200
  ok         = true
  statusText = [OK]
  url        = [http://127.0.0.1:18080/status]
  error      = []
  body len   = 29
  body       = {"status": "ok", "code": 200}
  headers[content-type] = [application/json]
```

### 4.2 All 7 Response Fields Verified

| Field | Actual Value | Semantic Check |
|-------|-------------|----------------|
| `status` | 200 | HTTP status code, int ✅ |
| `ok` | true | bool, status 200-299 → true ✅ |
| `statusText` | "OK" | non-empty string ✅ |
| `url` | "http://127.0.0.1:18080/status" | matches request URL ✅ |
| `error` | "" (empty) | empty on success ✅ |
| `body` | `{"status": "ok", "code": 200}` | non-empty, 29 bytes ✅ |
| `headers` | map with `content-type: application/json` | lowercase keys ✅ |

---

## 5. Assertion Results

### 5.1 Core Assertions (3 — status / headers / body)

| # | Assertion | Result |
|---|-----------|--------|
| 1 | `response.status == 200` | **PASS** |
| 2 | `response.body` is non-empty | **PASS** |
| 3 | `response.headers` contains content-type | **PASS** |

### 5.2 Semantic Sanity Checks (5 — success path)

| # | Assertion | Result |
|---|-----------|--------|
| 4 | `response.ok == true` for status 200 | **PASS** |
| 5 | `response.statusText` is non-empty | **PASS** |
| 6 | `response.url` contains 127.0.0.1 | **PASS** |
| 7 | `response.error` is empty on success | **PASS** |
| 8 | `response.body` contains "status" field | **PASS** |

### 5.3 Final Result

```
=== Results ===
Passed: 8
Failed: 0

ALL TESTS PASSED
```

**8/8 assertions PASS. Zero failures.**

---

## 6. Compiler Bootstrap

| Step | Result |
|------|--------|
| Seed compiler compiles `tools/TLLC/main.tll` | ✅ Compilation Successful |
| Functions | 172 |
| Constants | 3911 |
| Gen1 compiler compiles minimal HTTP test | ✅ Compilation Successful |
| Gen1 compiler compiles P1-01/02/03 regression tests | ✅ All compile |

**Bootstrap not broken by Level 1 changes.**

---

## 7. Regression Verification

### 7.1 P1-01 Secure Random

```
Boundary conditions tested: 0, 1, 32, 1024, negative, large range
Concurrency: 1000 rapid calls, no duplicates
Compiler bootstrap: verified (self-hosting)
```
**Result**: PASS ✅

### 7.2 P1-02 Password Hashing

```
PASS: 36
FAIL: 0
Total: 36
RESULT: ALL TESTS PASSED
```
**Result**: PASS ✅

### 7.3 P1-03 HMAC-SHA256

```
PASS: 20
FAIL: 0
Total: 20
RESULT: ALL TESTS PASSED
```
**Result**: PASS ✅

### 7.4 P1-03 RFC 4231

```
PASS: 8
FAIL: 0
Total: 8
ALL TESTS PASSED
```
**Result**: PASS ✅

**No regressions detected in P1-01/P1-02/P1-03 sealed capabilities after adding http_client_builtin.c to the build.**

---

## 8. CI Configuration

### 8.1 Workflow

File: `.github/workflows/p1-04-http-client.yml`
Name: `P1-04 HTTP Client Level 1 Tests`

### 8.2 Three-Platform Matrix

| Platform | OS | Compiler | HTTP Backend | TLS Framework |
|----------|-----|----------|-------------|---------------|
| Linux | Ubuntu 22.04 | gcc | POSIX socket | OpenSSL (-lssl -lcrypto) |
| macOS | macos-latest | clang | POSIX socket | Secure Transport (-framework Security) |
| Windows | windows-latest | MSVC | WinHTTP | WinHTTP (winhttp.lib) |

### 8.3 CI Steps (per platform)

1. Checkout (with CRLF conversion disabled)
2. Build tllvm (per-file compilation, includes http_client_builtin.c)
3. Build TLL compiler (bootstrap)
4. Start test_server.py on port 18080 (background)
5. Verify server responds (curl)
6. Compile minimal HTTP GET test
7. Run minimal HTTP GET test
8. Verify output contains "ALL TESTS PASSED" (fail if not found)
9. Stop test server (always)

### 8.4 Failure Handling

- Build failure → CI fails (exit code checked)
- Compile failure → CI fails
- Test output does not contain "ALL TESTS PASSED" → CI fails with explicit error
- No `|| true`, no `continue-on-error`, no test deletion

---

## 9. Known Limitations (Level 1 scope)

The following are NOT tested in Level 1 and remain for subsequent levels:

| Capability | Level | Status |
|------------|-------|--------|
| HTTP GET (minimal) | Level 1 | ✅ VERIFIED |
| POST / PUT / DELETE | Level 2 | Not tested |
| Custom request headers | Level 2 | Not tested |
| Request body | Level 2 | Not tested |
| Timeout | Level 2 | Not tested |
| Error handling (connection refused, etc.) | Level 2 | Not tested |
| HTTPS / TLS | Level 3 | Not tested |
| Connection pooling / reuse | Level 4 | Not tested |
| Concurrency / parallel requests | Level 4 | Not tested |
| getJson / postJson helpers | Level 5 | Not tested |
| Rapid sequential request stability | Known issue from P1-04-r2 (SO_LINGER, graceful delay fixes) | Not re-verified in Level 1 |

**Level 1 only verifies the minimal GET closed loop. It does not claim full HTTP Client capability.**

---

## 10. Conclusion

The existing 35KB `http_client_builtin.c` implementation **passes Level 1 minimal HTTP GET verification** without any C code modifications:

- ✅ Compiles on Windows (MSVC + WinHTTP)
- ✅ Compiles on Linux (gcc + POSIX/OpenSSL)
- ✅ Compiles on macOS (clang + POSIX/Secure Transport)
- ✅ `httpc.get(url)` returns a valid Response map
- ✅ All 7 Response fields (status/ok/statusText/url/error/body/headers) have correct semantics on success
- ✅ 8/8 assertions PASS
- ✅ Compiler bootstrap intact (172 functions, 3911 constants)
- ✅ P1-01/P1-02/P1-03 sealed capabilities show no regressions
- ✅ Three-platform CI configured with real server + real assertions

**The existing HTTP Client implementation qualifies for entry into TLL's formal capability layer at Level 1 (minimal HTTP GET).**

---

## 11. Commit

**Commit message**: `p1-04(level1): seal minimal HTTP GET`

**Files changed**:
- `tests/net/gate_http_client_minimal.tll` (NEW)
- `.github/workflows/p1-04-http-client.yml` (NEW)
- `docs/P1-04-HTTP-CLIENT-LEVEL1-EVIDENCE.md` (NEW)

**Zero C code modifications.**
