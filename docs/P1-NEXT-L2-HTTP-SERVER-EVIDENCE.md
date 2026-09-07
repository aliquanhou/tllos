# P1-NEXT L2: HTTP Server Gate — Evidence

## Capability
HTTP Server (http.serve builtin idx 94)

## Existing Capability Audit
HTTP Server was listed as PARTIAL in TLL-V1-CAPABILITY-MATRIX.md ("in mall/, not abstracted to stdlib"). Audit revealed:
- `http.serve(addr, handler)` already implemented in `host/c/builtin.c` (idx 94) for all 3 platforms
- Uses worker pool (8 threads) with VM lock serialization
- Request map: method, path, rawPath, query, queryMap, headers, body
- Response map: status, body, contentType, headers (optional)
- Already used by mall/ (mall/main.tll + mall/core/router.tll)
- No standalone Gate test existed (only tests/http_server_upgrade_test.tll with handler definition, no test driver)

## Bug Discovery
**Test infrastructure bug**: Python subprocess.Popen with stderr=PIPE caused server process to deadlock/crash after ~7 requests because stderr pipe buffer filled up (server outputs startup messages to stderr, and Python never drained the pipe).

### Root Cause
subprocess.PIPE for stderr without concurrent reading → buffer full → server write() blocks → worker pool thread deadlock → process appears dead.

### Fix
Modified `tests/http/test_http_server.py` to use `stderr=subprocess.DEVNULL` instead of `subprocess.PIPE`.

**Note**: This is a test infrastructure bug, not an http.serve runtime bug. The server itself is stable (verified with PowerShell Invoke-WebRequest: 10/10 sequential requests, server stays alive).

## Test
- `tests/http/gate_http_server.tll` — Server-side handler with 8 test endpoints
- `tests/http/test_http_server.py` — Python test driver: compiles server, starts subprocess, sends requests, validates responses, shuts down

### Gates (19 assertions)
- Gate 1: Basic GET / → 200 + body + Content-Type (3 assertions)
- Gate 2: Query parsing /search?q=test&page=2 → q and page parsed (3 assertions)
- Gate 3: Request headers /headers → User-Agent echoed (2 assertions)
- Gate 4: Custom response headers + 201 status /create → X-Custom-Header present and correct (4 assertions)
- Gate 5: 404 status /notfound → status 404 + body (2 assertions)
- Gate 6: POST body echo /echo → body echoed (2 assertions)
- Gate 7: 500 error status /error → status 500 + body (2 assertions)
- Gate 8: Unknown path → 404 (1 assertion)

## Gate Result
**19/19 PASS** (Windows local verification)

## Compiler Bootstrap
Not modified (no compiler changes). Existing bootstrap verified in L1.

## Regression
- P1-01 Secure Random: PASS (L1 verification)
- P1-02 Password Hashing: 36/36 PASS (L1 verification)
- P1-03 HMAC-SHA256: 20/20 PASS (L1 verification)
- P1-04 Level 1-4: not re-run (no HTTP client code modified)
- File System L1: 25/25 PASS

## CI
Added to `.github/workflows/p1-04-http-client.yml` for all 3 platforms (Ubuntu, Windows, macOS), placed after File System test.

## Files Added
- `tests/http/gate_http_server.tll` — Server handler (NEW)
- `tests/http/test_http_server.py` — Python test driver (NEW)

## Files Modified
- `.github/workflows/p1-04-http-client.yml` — added HTTP Server test to 3 platforms

## Capability Matrix Correction
HTTP Server status: PARTIAL → COMPLETE (with this Gate test). Router abstraction remains as separate future task (mall/core/router.tll still needs stdlib extraction).

## Known Limitations
- Router (path parameters, middleware, route grouping) still lives in mall/core/router.tll, not abstracted to stdlib/http/
- No HTTPS server (only HTTP)
- No WebSocket upgrade
- No connection keep-alive (server sends Connection: close)
- No request body size limit (64KB hardcoded buffer)
- No streaming response
- Worker pool uses global VM lock (serialized TLL execution, not truly concurrent)
