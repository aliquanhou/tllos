# P1-04 HTTP Client - Evidence Document

**Status**: Linux + Windows COMPLETE, macOS PARTIAL (DEFERRED)
**Date**: 2026-09-05
**Module**: httpc (TLL Native HTTP Client)
**Index Range**: 200-209
**Final CI Run**: #220 (commit 9b6e551) - 3/3 jobs completed successfully, 18m 20s

## 0. Platform Support Matrix

| Platform | HTTP Client Support | Backend | TLS | CI Status |
|----------|---------------------|---------|-----|-----------|
| **Linux** | ✅ COMPLETE | POSIX socket + OpenSSL | OpenSSL TLS 1.2+ | ✅ PASS |
| **Windows** | ✅ COMPLETE | WinHTTP (system native) | Schannel | ✅ PASS |
| **macOS** | ⚠️ PARTIAL (DEFERRED) | Not implemented | N/A | ✅ Build PASS (no HTTP Client) |

**Important**: macOS support is explicitly DEFERRED, not omitted. The current implementation does not include native macOS TLS (Secure Transport / Network framework). HTTP Client calls on macOS will return an error. This is a known limitation tracked for future implementation.

## 1. API Specification

### TLL Builtin Functions (idx 200-209)

| idx | Function | Signature | Description | Linux | Windows | macOS |
|-----|----------|-----------|-------------|-------|---------|-------|
| 200 | httpc.get | `httpc.get(url, headers?) -> Response` | HTTP GET request | ✅ | ✅ | ⚠️ DEFERRED |
| 201 | httpc.post | `httpc.post(url, body, headers?) -> Response` | HTTP POST request | ✅ | ✅ | ⚠️ DEFERRED |
| 202 | httpc.put | `httpc.put(url, body, headers?) -> Response` | HTTP PUT request | ✅ | ✅ | ⚠️ DEFERRED |
| 203 | httpc.delete | `httpc.delete(url, headers?) -> Response` | HTTP DELETE request | ✅ | ✅ | ⚠️ DEFERRED |
| 204 | httpc.head | `httpc.head(url, headers?) -> Response` | HTTP HEAD request | ✅ | ✅ | ⚠️ DEFERRED |
| 205 | httpc.patch | `httpc.patch(url, body, headers?) -> Response` | HTTP PATCH request | ✅ | ✅ | ⚠️ DEFERRED |
| 206 | httpc.request | `httpc.request(map) -> Response` | Full control request | ✅ | ✅ | ⚠️ DEFERRED |
| 207 | httpc.getJson | `httpc.getJson(url, headers?) -> parsed JSON` | GET + auto-parse JSON | ✅ | ✅ | ⚠️ DEFERRED |
| 208 | httpc.postJson | `httpc.postJson(url, body, headers?) -> parsed JSON` | POST JSON + auto-parse | ✅ | ✅ | ⚠️ DEFERRED |
| 209 | httpc.options | `httpc.options(url, headers?) -> Response` | HTTP OPTIONS request | ✅ | ✅ | ⚠️ DEFERRED |

### Response Map Structure

| Field | Type | Description |
|-------|------|-------------|
| ok | bool | true if status 200-299 |
| status | int | HTTP status code |
| statusText | string | HTTP status text (e.g., "OK", "Not Found") |
| headers | map | Response headers (lowercase keys) |
| body | string | Response body |
| error | string | Error message (empty if successful) |
| url | string | Final request URL |

### httpc.request Map Parameters

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| method | string | no | "GET" | HTTP method |
| url | string | yes | - | Target URL |
| body | string | no | null | Request body |
| headers | map | no | null | Custom request headers |
| timeout | int | no | 30000 | Timeout in milliseconds |

## 2. Cross-Platform Implementation

### Windows (WinHTTP)
- **Backend**: Microsoft WinHTTP (system native, no external dependencies)
- **Features**: HTTP/HTTPS, custom headers, timeout, response headers, body
- **Libraries**: winhttp.lib, ws2_32.lib
- **TLS**: Handled by WinHTTP (Schannel)
- **Status**: ✅ COMPLETE

### Linux (POSIX Socket + OpenSSL)
- **Backend**: POSIX socket for HTTP, OpenSSL for HTTPS
- **Features**: HTTP/HTTPS, custom headers, timeout (SO_RCVTIMEO/SO_SNDTIMEO + poll), response headers, body, chunked transfer encoding
- **Libraries**: -lssl -lcrypto
- **TLS**: OpenSSL (TLS 1.2+ minimum, SNI support)
- **DNS**: getaddrinfo()
- **Connection timeout**: Non-blocking connect + poll()
- **Status**: ✅ COMPLETE

### macOS (DEFERRED)
- **Status**: ⚠️ PARTIAL (DEFERRED)
- **Reason**: Native macOS TLS (Secure Transport / Network framework) not yet implemented
- **Current behavior**: `httpc_builtin_invoke` is excluded from macOS build via `#if !defined(__APPLE__)` conditional compilation
- **Future plan**: Implement using Apple Network framework or Secure Transport for native TLS support
- **CI**: macOS build passes (without HTTP Client), all other tests pass

### URL Parsing
- Scheme detection (http://, https://)
- Host extraction
- Port extraction (default 80/443)
- Path + query string preservation

### Header Handling
- Custom headers iterated from TLL map (all keys, not just predefined)
- Response headers parsed and stored in map with lowercase keys
- Default headers: Host, User-Agent (TLL-HTTP-Client/1.0), Accept, Connection: close

### Chunked Transfer Encoding
- Detected via Transfer-Encoding: chunked response header
- Dechunking implemented per RFC 7230

## 3. Compiler Integration

### Files Modified

| File | Change | macOS Conditional Compilation |
|------|--------|-------------------------------|
| `host/c/http_client_builtin.c` | NEW (~700 lines) | N/A (not compiled on macOS) |
| `host/c/tllvm.h` | MODIFIED (+4 lines) | `#if !defined(__APPLE__)` around declaration |
| `host/c/builtin.c` | MODIFIED (+5 lines) | `#if !defined(__APPLE__)` around dispatch |
| `host/c/Makefile` | MODIFIED (+1 line) | N/A |
| `compiler/codegen.tll` | MODIFIED (+12 lines) | N/A (compiler is cross-platform) |
| `compiler/linker.tll` | MODIFIED (+1 line) | N/A |
| `tools/TLLC/tllc.tllbc` | MODIFIED (binary) | N/A |
| `.github/workflows/ci.yml` | MODIFIED | Split Linux/macOS build steps |
| `.github/workflows/p1-crypto-tests.yml` | MODIFIED | macOS excludes http_client_builtin.c |
| `tests/net/gate_http_client.tll` | NEW (~170 lines) | N/A |

### Compiler Bootstrap
- **Pass 1**: tllc_httpc.tllbc (665,681 bytes, Functions 172, Constants 3911)
- **Pass 2**: /tmp/tllc_boot2.tllbc (665,681 bytes, Functions 172, Constants 3911)
- **MD5**: 0181be6cd8d76fc32d2d1f7adf8ff7fd (both passes identical)
- **Status**: Bootstrap consistency verified ✅

### Conditional Compilation Strategy

To maintain three-platform CI while deferring macOS HTTP Client support:

1. **`tllvm.h`**: `httpc_builtin_invoke` declaration wrapped in `#if !defined(__APPLE__)`
2. **`builtin.c`**: idx 200-209 dispatch wrapped in `#if !defined(__APPLE__)`
3. **`ci.yml`**: Linux and macOS build steps split; Linux compiles `http_client_builtin.c` + links `-lssl -lcrypto`, macOS does not
4. **`p1-crypto-tests.yml`**: Same split for P1-01 regression tests
5. **P1-04 Gate Test**: Runs only on Linux and Windows (`if: runner.os == 'Linux'` / `if: runner.os == 'Windows'`)

## 4. Gate Test Results

### Test Suite: tests/net/gate_http_client.tll

| # | Test | Result |
|---|------|--------|
| 1 | httpc.get (HTTP) - status/ok/body/url/statusText | 5/5 PASS |
| 2 | httpc.get with custom headers - X-Test-Header sent | 3/3 PASS |
| 3 | httpc.post with body - data received | 3/3 PASS |
| 4 | httpc.post with Content-Type header | 1/1 PASS |
| 5 | httpc.request GET (full control) | 3/3 PASS |
| 6 | httpc.request with POST | 2/2 PASS |
| 7 | Response headers parsing - content-type | 2/2 PASS |
| 8 | Error handling - invalid URL (.invalid TLD) | 3/3 PASS |
| 9 | httpc.put | 2/2 PASS |
| 10 | httpc.delete | 1/1 PASS |
| 11 | url field in response | 1/1 PASS |
| 12 | HTTPS request (OpenSSL) | 3/3 PASS |

**Total: 29/29 PASS (100%)** — verified on Linux server (1.117.221.61)

### CI Verification (Run #220, commit 9b6e551)

| Platform | Build | P1-04 Gate Test | All Regression Tests |
|----------|-------|-----------------|---------------------|
| Ubuntu (Linux) | ✅ PASS | ✅ PASS (29/29) | ✅ PASS |
| Windows (MSVC) | ✅ PASS | ✅ PASS (29/29) | ✅ PASS |
| macOS | ✅ PASS (no HTTP Client) | ⚠️ Skipped (DEFERRED) | ✅ PASS |

**CI Run #220**: 3/3 jobs completed successfully, 18m 20s, only 3 Node.js deprecated warnings (non-blocking)

### Test Endpoint
- httpbin.org (HTTP + HTTPS)
- test.invalid (RFC 2606 reserved TLD for error testing)

## 5. Bugs Found and Fixed During Development

1. **map_new()/map_set() not TLL language functions** — TLL uses `{}` literal for map creation and `.key = value` / `m["key"] = value` for assignment. Fixed all test code.
2. **headers_to_string only checked predefined keys** — Changed to iterate all map entries via TLLMap buckets.
3. **httpc.request headers default** — Added null check and default to tll_null() when headers not a map.
4. **Invalid URL test domain** — `invalid.nonexistent.domain.xyz` returned 302 (DNS hijack), changed to `test.invalid` (RFC 2606 reserved).
5. **macOS CI build failures** — Root cause: http_client_builtin.c POSIX+OpenSSL backend not compatible with macOS CI environment. Solution: conditional compilation + split build steps. macOS HTTP Client support explicitly DEFERRED.

## 6. CI Configuration

### Linux (Ubuntu 22.04)
- Added `libssl-dev` to apt-get install
- Compile: `http_client_builtin.c` + `-lssl -lcrypto`
- Test: P1-04 HTTP Client Gate Test (Linux only)

### macOS
- Compile: **excludes** `http_client_builtin.c` (no OpenSSL linking)
- `builtin.c` / `tllvm.h`: httpc code excluded via `#if !defined(__APPLE__)`
- Test: P1-04 Gate Test **skipped** (DEFERRED)
- All other regression tests: ✅ PASS

### Windows (MSVC)
- Compile: `http_client_builtin.c` (WinHTTP backend, no OpenSSL needed)
- Libraries: ws2_32.lib, winhttp.lib, bcrypt.lib
- Test: P1-04 HTTP Client Gate Test (Windows only)

## 7. Known Limitations and Future Work

### Deferred (macOS)
1. **macOS HTTP Client support** — Native TLS implementation using Apple Network framework or Secure Transport. Currently DEFERRED.

### General Limitations (all platforms)
1. **Redirect following**: Currently does not automatically follow 3xx redirects. User must handle manually.
2. **Cookie jar**: No automatic cookie management.
3. **Compression**: Does not automatically decompress gzip/deflate responses.
4. **Connection pooling**: Each request creates a new connection (Connection: close).
5. **Streaming**: Response body is fully buffered in memory.
6. **Multipart/form-data**: Not natively supported (can be constructed manually).
7. **WebSocket**: Not supported (separate protocol).

### Future Enhancements
1. macOS native TLS support (Network framework / Secure Transport)
2. Connection pooling and keep-alive
3. Automatic redirect following
4. Cookie jar management
5. Response compression (gzip/deflate)
6. Streaming response body
7. Multipart/form-data support
8. Concurrent request support
9. HTTP/2 support

## 8. Files Summary

| File | Change | Lines |
|------|--------|-------|
| host/c/http_client_builtin.c | NEW | ~700 |
| host/c/tllvm.h | MODIFIED | +4 (conditional) |
| host/c/builtin.c | MODIFIED | +5 (conditional) |
| host/c/Makefile | MODIFIED | +1 |
| compiler/codegen.tll | MODIFIED | +12 |
| compiler/linker.tll | MODIFIED | +1 |
| tools/TLLC/tllc.tllbc | MODIFIED | binary (665,681 bytes) |
| tests/net/gate_http_client.tll | NEW | ~170 |
| .github/workflows/ci.yml | MODIFIED | split build + test step |
| .github/workflows/p1-crypto-tests.yml | MODIFIED | macOS excludes httpc |
| docs/P1-04-HTTP-CLIENT-EVIDENCE.md | NEW | this file |

## 9. Final Status Summary

| Dimension | Linux | Windows | macOS |
|-----------|-------|---------|-------|
| Core Implementation | ✅ | ✅ | ⚠️ DEFERRED |
| Compiler Integration | ✅ | ✅ | ✅ (conditional) |
| Gate Tests (29/29) | ✅ | ✅ | ⚠️ Skipped |
| CI Build | ✅ | ✅ | ✅ |
| All Regression Tests | ✅ | ✅ | ✅ |
| HTTPS/TLS | ✅ OpenSSL | ✅ Schannel | ⚠️ DEFERRED |
| Custom Headers | ✅ | ✅ | ⚠️ DEFERRED |
| Chunked Encoding | ✅ | ✅ (WinHTTP) | ⚠️ DEFERRED |
| Error Handling | ✅ | ✅ | ⚠️ DEFERRED |

**Overall Status**: P1-04 HTTP Client is COMPLETE for Linux and Windows, PARTIAL (DEFERRED) for macOS. Three-platform CI passes (macOS builds without HTTP Client). macOS native TLS support is tracked as future work.

**Evidence**: CI Run #220 (commit 9b6e551) — 3/3 jobs success, 18m 20s. Linux Gate 29/29 PASS verified on server.
