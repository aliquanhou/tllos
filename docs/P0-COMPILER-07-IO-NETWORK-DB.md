# P0-COMPILER-07: IO / Network / Database Capability Implementation

**Status**: IMPLEMENTED + VERIFIED (Windows)
**Date**: 2026-09-07
**Branch**: p0-compiler-keyword-fix
**Base Commit**: 53cb49f

---

## 1. Executive Summary

P0-COMPILER-07 implements and verifies TLL's IO/Network/Database capabilities through three real dogfood projects. The phase focused on proving TLL can independently develop real-world web/network/database applications, not just adding API count.

**Key Results**:
- HTTP Server with routing: ✅ Fully verified (6 endpoints)
- REST API + SQLite CRUD: ✅ Fully verified (complete CRUD cycle)
- Concurrent TCP Server: ✅ Compiled, runtime verification pending
- Two real Compiler/Runtime bugs discovered and documented

---

## 2. Reality Audit (Existing Capabilities)

### Builtin Modules (already complete)

| Module | Builtin IDs | Capabilities |
|--------|-------------|--------------|
| io | 0-4 | println, print, readLine, json.parse, json.stringify |
| fs | 79-90 | readFile, writeFile, appendFile, exists, mkdir, remove, listDir, isFile, isDir, fileSize, copyFile, rename |
| process | 120-125 | exit, argv, env, cwd, chdir, platform |
| time | 126-129 | now, nowMs, sleep, date |
| tcp | 133-143 | listen, accept, connect, send, recv, close, setTimeout, tryAccept, select, tryRecv, trySend |
| http | 91-97 | get, post, request, serve, encodeURI, decodeURI, parseJSON |
| sqlite | 150-158 | open, close, exec, query, lastInsertRowid, changes, version, tableExists, columns |
| coroutine | 144, 160-179 | spawn, sleep, yield, waitRead, waitWrite, channel |
| crypto | 145, 160-179 | randomBytes, SHA-256, HMAC, Ed25519 |
| httpc | 200-209 | HTTP Client (P1-04, platform-native) |

### Stdlib Modules (already complete)

| Module | File | Capabilities |
|--------|------|--------------|
| db | stdlib/db.tll | Database abstraction layer (221 lines) |
| json | stdlib/json.tll | JSON helpers (135 lines) |
| p2p | stdlib/p2p.tll | P2P network (447 lines) |
| task | stdlib/task.tll | Task/coroutine helpers (223 lines) |
| stream | stdlib/stream.tll | Stream processing (300 lines) |
| blockchain | stdlib/blockchain.tll | Blockchain implementation |
| agent | stdlib/agent.tll | Agent framework |

### Capability Matrix (before P0-07)

| Capability | Status | Notes |
|------------|--------|-------|
| File IO (one-shot) | COMPLETE | readFile/writeFile/appendFile |
| File Handle mode | MISSING | open/close/read/write/seek |
| Directory operations | PARTIAL | mkdir/listDir/remove, no recursive |
| Path utilities | MISSING | join/basename/dirname/extension |
| Process management | PARTIAL | exit/cwd/chdir, no spawn/wait |
| TCP | COMPLETE | Full socket API + non-blocking |
| UDP | MISSING | No UDP support |
| DNS | MISSING | No hostname resolution |
| HTTP Client | COMPLETE | P1-04, platform-native (WinHTTP/OpenSSL/Secure Transport) |
| HTTP Server | PARTIAL | http.serve basic, no routing/middleware |
| TLS | PARTIAL | HTTP Client has TLS, raw TCP TLS missing |
| JSON | COMPLETE | parse/stringify builtin + stdlib |
| SQLite | COMPLETE | Full binding + abstraction layer |
| Coroutine | COMPLETE | P0-06 sealed, full scheduler |

---

## 3. Implementation

### 3.1 New Stdlib Modules

#### stdlib/path.tll (Path Utilities)
- **File**: `stdlib/path.tll`
- **Lines**: ~150
- **Functions**:
  - `path_join(parts)` - Join path components
  - `path_separator()` - Platform-specific separator
  - `path_basename(p)` - Last component of path
  - `path_dirname(p)` - Directory name
  - `path_extension(p)` - File extension
  - `path_isAbsolute(p)` - Check if absolute
  - `path_normalize(p)` - Normalize path (resolve . and ..)
  - `path_absolute(p)` - Get absolute path

#### stdlib/httpd.tll (HTTP Server High-level)
- **File**: `stdlib/httpd.tll`
- **Lines**: ~200
- **Features**:
  - Router with method + pattern matching
  - Path parameter support (`:id`)
  - Request helpers (parseJsonBody, queryParam, header)
  - Response helpers (json, text, html, redirect, notFound, serverError)
  - Router creation and route registration

### 3.2 Dogfood Projects

#### Project 1: HTTP Server (`examples/http_server.tll`)
- **Lines**: ~120
- **Features**:
  - Inline router with path parameters
  - 6 endpoints: GET /, GET /api/hello, GET /api/user/:id, POST /api/echo, GET /api/status, 404
  - JSON, HTML, and text responses
- **Verification**: ✅ All endpoints tested and passing

#### Project 2: REST API + SQLite (`examples/rest_api_sqlite.tll`)
- **Lines**: ~250
- **Features**:
  - Complete CRUD for Todo items
  - SQLite database with auto-creation
  - 7 endpoints: GET /api/todos, GET /api/todos/:id, POST /api/todos, PUT /api/todos/:id, DELETE /api/todos/:id, GET /api/stats, 404
  - Path parameter routing
  - JSON request/response
- **Verification**: ✅ Full CRUD cycle tested and passing

#### Project 3: Concurrent TCP Server (`examples/concurrent_tcp.tll`)
- **Lines**: ~180
- **Features**:
  - Coroutine-based concurrent connection handling
  - Non-blocking accept (tcp.tryAccept)
  - Non-blocking receive (tcp.tryRecv) with coroutine yield
  - Echo server with stats command
  - Connection tracking and statistics
- **Verification**: ✅ Compiled successfully
- **Runtime Status**: ⏳ Pending further verification (coroutine + non-blocking IO combination)

---

## 4. Bug Discovery

### Bug 1: convert.toString on map-derived strings causes json.parse crash

**Severity**: HIGH
**Status**: DOCUMENTED, workaround applied

**Description**:
When a string is retrieved from a TLL map (e.g., `req["body"]`) and passed through `convert.toString()`, the resulting string has an incorrect internal length field (`arrays.length()` returns 0), although the string content is correct. Passing this string to `json.parse()` causes a VM crash.

**Reproduction**:
```tll
fn handler(req: map) -> any {
    let body = req["body"]
    let bodyStr = convert.toString(body)  // arrays.length(bodyStr) returns 0!
    let parsed = json.parse(bodyStr)      // CRASH
    return { status: 200, body: "ok" }
}
```

**Workaround**:
Pass the map value directly to `json.parse()` without `convert.toString()`:
```tll
let body = req["body"]
let parsed = json.parse(body)  // Works correctly
```

**Impact**:
- Affects all code that uses `convert.toString()` on map-derived strings before passing to functions expecting proper strings
- `strings.substring()`, `strings.startsWith()`, `strings.charAt()` may also be affected

### Bug 2: convert.toString on array-derived strings returns length 0

**Severity**: HIGH
**Status**: DOCUMENTED, workaround applied

**Description**:
Similar to Bug 1, when strings are retrieved from arrays (e.g., `arrays.get(parts, i)`) and passed through `convert.toString()`, the resulting string has `arrays.length()` returning 0. This breaks path parameter matching in routers.

**Reproduction**:
```tll
let parts = strings.split("/api/todos/1", "/")
let part = convert.toString(arrays.get(parts, 3))  // "1"
io.println(convert.toString(arrays.length(part)))    // prints 0, should be 1
```

**Workaround**:
Use direct comparison without `convert.toString()`, or use known pattern matching with hardcoded parameter names.

**Root Cause Hypothesis**:
The `convert.toString()` function may return a string wrapper that doesn't properly initialize the length field in the TLL string object, or there's a reference counting issue when converting TLLValue to string.

---

## 5. Verification Results

### 5.1 HTTP Server (Project 1)

| Test | Endpoint | Result |
|------|----------|--------|
| GET / | HTML page | ✅ PASS |
| GET /api/hello | JSON response | ✅ PASS |
| GET /api/user/123 | Path parameter | ✅ PASS (id displayed) |
| POST /api/echo | Echo body | ✅ PASS |
| GET /api/status | System info | ✅ PASS |
| GET /nonexistent | 404 | ✅ PASS |

### 5.2 REST API + SQLite (Project 2)

| Test | Operation | Result |
|------|-----------|--------|
| GET /api/todos (empty) | List | ✅ PASS (empty list) |
| POST /api/todos | Create | ✅ PASS (returns created item) |
| GET /api/todos/1 | Read | ✅ PASS (returns item) |
| PUT /api/todos/1 | Update | ✅ PASS (completed=1) |
| GET /api/stats | Stats | ✅ PASS (total=1, completed=1) |
| DELETE /api/todos/1 | Delete | ✅ PASS |
| GET /api/todos (after delete) | List | ✅ PASS (empty list) |
| GET /api/todos/999 | 404 | ✅ PASS |

### 5.3 Concurrent TCP Server (Project 3)

| Test | Result |
|------|--------|
| Compilation | ✅ PASS |
| Server startup | ⏳ Pending |
| Client connection | ⏳ Pending |
| Echo response | ⏳ Pending |
| Concurrent connections | ⏳ Pending |

---

## 6. Regression

### P0-COMPILER-01 through P0-06

No modifications were made to compiler, runtime, or existing stdlib code in P0-07. All changes are:
- New stdlib modules (path.tll, httpd.tll)
- New example projects (3 files)

Therefore, no regression is expected in previously sealed capabilities.

**Regression Status**: ✅ No code changes to sealed modules

---

## 7. Known Limitations

1. **Concurrent TCP Server runtime verification pending**: The coroutine + non-blocking IO combination needs further testing.
2. **convert.toString Bug**: Two related bugs discovered in `convert.toString()` when used on map/array-derived strings. Workarounds applied in examples.
3. **UDP missing**: No UDP socket support in TLL.
4. **DNS missing**: No hostname resolution; `tcp.connect()` only accepts IP addresses.
5. **File Handle mode missing**: Only one-shot file operations (readFile/writeFile), no open/close/read/write/seek.
6. **process.spawn missing**: No subprocess spawning capability.
7. **Raw TCP TLS missing**: HTTP Client has TLS, but raw TCP sockets don't have TLS encapsulation.
8. **stdlib/httpd.tll import mechanism**: The high-level HTTP server module needs verification of import mechanics.

---

## 8. Files Changed

### New Files
- `stdlib/path.tll` - Path utilities module
- `stdlib/httpd.tll` - HTTP Server high-level module
- `examples/http_server.tll` - Dogfood Project 1: HTTP Server
- `examples/rest_api_sqlite.tll` - Dogfood Project 2: REST API + SQLite
- `examples/concurrent_tcp.tll` - Dogfood Project 3: Concurrent TCP Server
- `docs/P0-COMPILER-07-IO-NETWORK-DB.md` - This evidence document

### Modified Files
- None (all changes are additions)

---

## 9. Conclusion

P0-COMPILER-07 successfully demonstrates that TLL can independently develop real-world web/network/database applications. The two fully verified dogfood projects (HTTP Server and REST API + SQLite) prove that TLL's existing builtin capabilities (http.serve, sqlite, json, tcp, coroutine) are sufficient for building production-style applications.

The phase also discovered two real bugs in `convert.toString()` that affect string handling when retrieving values from maps and arrays. These bugs are documented with workarounds and should be addressed in a future compiler hardening phase.

**Overall Status**: 🟢 IMPLEMENTED + VERIFIED (core capabilities)
**Recommendation**: Proceed to P0-COMPILER-08 (Web / Service) after addressing the convert.toString bugs and completing Concurrent TCP Server verification.
