# P1-04 HTTP Client - Evidence Document

**Status**: Implementation complete, pending CI and总指挥 final SEAL验收
**Date**: 2026-09-05
**Module**: httpc (TLL Native HTTP Client)
**Index Range**: 200-209

## 1. API Specification

### TLL Builtin Functions (idx 200-209)

| idx | Function | Signature | Description |
|-----|----------|-----------|-------------|
| 200 | httpc.get | `httpc.get(url, headers?) -> Response` | HTTP GET request |
| 201 | httpc.post | `httpc.post(url, body, headers?) -> Response` | HTTP POST request |
| 202 | httpc.put | `httpc.put(url, body, headers?) -> Response` | HTTP PUT request |
| 203 | httpc.delete | `httpc.delete(url, headers?) -> Response` | HTTP DELETE request |
| 204 | httpc.head | `httpc.head(url, headers?) -> Response` | HTTP HEAD request |
| 205 | httpc.patch | `httpc.patch(url, body, headers?) -> Response` | HTTP PATCH request |
| 206 | httpc.request | `httpc.request(map) -> Response` | Full control request (method/url/body/headers/timeout) |
| 207 | httpc.getJson | `httpc.getJson(url, headers?) -> parsed JSON` | GET + auto-parse JSON response |
| 208 | httpc.postJson | `httpc.postJson(url, body, headers?) -> parsed JSON` | POST JSON + auto-parse response |
| 209 | httpc.options | `httpc.options(url, headers?) -> Response` | HTTP OPTIONS request |

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

### Linux/macOS (POSIX Socket + OpenSSL)
- **Backend**: POSIX socket for HTTP, OpenSSL for HTTPS
- **Features**: HTTP/HTTPS, custom headers, timeout (SO_RCVTIMEO/SO_SNDTIMEO + poll), response headers, body, chunked transfer encoding
- **Libraries**: -lssl -lcrypto
- **TLS**: OpenSSL (TLS 1.2+ minimum, SNI support)
- **DNS**: getaddrinfo()
- **Connection timeout**: Non-blocking connect + poll()

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
- `host/c/http_client_builtin.c` (new, ~27KB) - Cross-platform HTTP Client C binding
- `host/c/tllvm.h` - Added httpc_builtin_invoke declaration
- `host/c/builtin.c` - Added idx 200-209 dispatch to httpc_builtin_invoke
- `host/c/Makefile` - Added http_client_builtin.c to SRCS
- `compiler/codegen.tll` - Added httpc module function mapping (idx 200-209)
- `compiler/linker.tll` - Added "httpc" to stdlibs list
- `tools/TLLC/tllc.tllbc` - Updated bootstrap compiler (665,681 bytes)
- `.github/workflows/ci.yml` - Added OpenSSL dependency, http_client_builtin.c, HTTP Client test step

### Compiler Bootstrap
- **Pass 1**: tllc_httpc.tllbc (665,681 bytes, Functions 172, Constants 3911)
- **Pass 2**: /tmp/tllc_boot2.tllbc (665,681 bytes, Functions 172, Constants 3911)
- **MD5**: 0181be6cd8d76fc32d2d1f7adf8ff7fd (both passes identical)
- **Status**: Bootstrap consistency verified ✅

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

**Total: 29/29 PASS (100%)**

### Test Endpoint
- httpbin.org (HTTP + HTTPS)
- test.invalid (RFC 2606 reserved TLD for error testing)

## 5. Bugs Found and Fixed During Development

1. **map_new()/map_set() not TLL language functions** - TLL uses `{}` literal for map creation and `.key = value` / `m["key"] = value` for assignment. Fixed all test code.
2. **headers_to_string only checked predefined keys** - Changed to iterate all map entries via TLLMap buckets.
3. **httpc.request headers default** - Added null check and default to tll_null() when headers not a map.
4. **Invalid URL test domain** - `invalid.nonexistent.domain.xyz` returned 302 (DNS hijack), changed to `test.invalid` (RFC 2606 reserved).

## 6. CI Configuration

### Linux (Ubuntu 22.04)
- Added `libssl-dev` to apt-get install
- Compile: added `http_client_builtin.c` and `-lssl -lcrypto`
- Test: P1-04 HTTP Client Gate Test (Linux/macOS)

### macOS
- Compile: added `http_client_builtin.c` and `-lssl -lcrypto` (system LibreSSL/OpenSSL)
- Test: P1-04 HTTP Client Gate Test (Linux/macOS)

### Windows (MSVC)
- Compile: added `http_client_builtin.c` (WinHTTP backend, no OpenSSL needed)
- Libraries: ws2_32.lib, winhttp.lib, bcrypt.lib

## 7. Known Limitations and Future Work

1. **Redirect following**: Currently does not automatically follow 3xx redirects. User must handle manually.
2. **Cookie jar**: No automatic cookie management.
3. **Compression**: Does not automatically decompress gzip/deflate responses.
4. **Connection pooling**: Each request creates a new connection (Connection: close).
5. **Streaming**: Response body is fully buffered in memory.
6. **Multipart/form-data**: Not natively supported (can be constructed manually).
7. **WebSocket**: Not supported (separate protocol).

## 8. Files Summary

| File | Change | Lines |
|------|--------|-------|
| host/c/http_client_builtin.c | NEW | ~700 |
| host/c/tllvm.h | MODIFIED | +2 |
| host/c/builtin.c | MODIFIED | +4 |
| host/c/Makefile | MODIFIED | +1 |
| compiler/codegen.tll | MODIFIED | +12 |
| compiler/linker.tll | MODIFIED | +1 |
| tools/TLLC/tllc.tllbc | MODIFIED | binary (665,681 bytes) |
| tools/TLLC/tllc.tllbc.b64 | MODIFIED | base64 |
| tests/net/gate_http_client.tll | NEW | ~170 |
| .github/workflows/ci.yml | MODIFIED | +OpenSSL + test step |
| docs/P1-04-HTTP-CLIENT-EVIDENCE.md | NEW | this file |
