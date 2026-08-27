# TLL OS Host ABI Specification

**Version**: 1.2
**Status**: Genesis 0-97 FROZEN; P0-2 extensions 120+ active

---

## 1. Overview

The Host ABI defines the interface between TLL VM implementations and the underlying operating system. Host capabilities are exposed as builtin functions with specific index ranges.

> **Principle**: The Host ABI is NOT part of the TLL language semantics. It is the boundary between TLL and the OS. A conforming TLL implementation must provide these host capabilities, but the implementation is platform-specific.

> **Consistency**: This spec MUST match `host/c/builtin.c`. Run `scripts/check-abi.bat` / `scripts/check-abi.sh` to verify.

---

## 2. Host vs Stdlib Classification

| Category | Index Range | Count | Type |
|----------|------------|-------|------|
| `io` | 0-2 | 3 | **Host ABI** |
| `json` | 3-4 | 2 | Stdlib (pure computation) |
| `math` | 5-23 | 19 | Stdlib (pure computation) |
| `strings` | 24-48 | 25 | Stdlib (pure computation) |
| `arrays` | 49-71 | 23 | Stdlib (pure computation) |
| `convert` | 72-78 | 7 | Stdlib (pure computation) |
| `fs` | 79-90 | 12 | **Host ABI** |
| `http` | 91-97 | 7 | **Host ABI** (client implemented P0-3.1; serve=94 stub) |
| `agent`/`workflow` | 98-119 | 22 | Deferred |
| `process` | 120-122, 127-128, 131 | 6 | **Host ABI** (P0-2 + P0-3.1 extension) |
| `time` | 123-126 | 4 | **Host ABI** (P0-3.1 extension) |
| `io_stderr` | 129-130 | 2 | **Host ABI** (P0-3.1 extension) |

**Host ABI total**: 34 builtins (io: 3, fs: 12, http: 7, process: 6, time: 4, io_stderr: 2)
**Stdlib total**: 76 builtins (pure computation, can be implemented in TLL)
**Total defined**: 110 (0-97 + 120-131)

---

## 3. io Module (Host ABI)

| Index | Name | Signature | Description |
|-------|------|-----------|-------------|
| 0 | `io.println` | `(value: any) -> void` | Print value + newline to stdout |
| 1 | `io.print` | `(value: any) -> void` | Print value to stdout (no newline) |
| 2 | `io.readLine` | `(prompt?: string) -> string` | Read line from stdin |

**Compiler Intrinsic Note**: `io.println` and `io.print` are typically inlined by the compiler as OP_PRINTLN (24) and OP_PRINT (23) opcodes. They remain available as builtins for indirect calls.

---

## 4. fs Module (Host ABI)

| Index | Name | Signature | Description |
|-------|------|-----------|-------------|
| 79 | `fs.readFile` | `(path: string) -> string` | Read entire file as string |
| 80 | `fs.writeFile` | `(path: string, content: string) -> void` | Write string to file (overwrite) |
| 81 | `fs.appendFile` | `(path: string, content: string) -> void` | Append string to file |
| 82 | `fs.exists` | `(path: string) -> bool` | Check if path exists |
| 83 | `fs.mkdir` | `(path: string) -> void` | Create directory |
| 84 | `fs.remove` | `(path: string) -> void` | Delete file or empty directory |
| 85 | `fs.listDir` | `(path: string) -> array<string>` | List directory contents |
| 86 | `fs.isFile` | `(path: string) -> bool` | Check if path is a regular file |
| 87 | `fs.isDir` | `(path: string) -> bool` | Check if path is a directory |
| 88 | `fs.fileSize` | `(path: string) -> int` | Get file size in bytes |
| 89 | `fs.copyFile` | `(src: string, dst: string) -> void` | Copy file |
| 90 | `fs.rename` | `(old: string, new: string) -> void` | Rename/move file |

---

## 5. http Module (Host ABI) — Client Implemented (P0-3.1)

| Index | Name | Signature | Description |
|-------|------|-----------|-------------|
| 91 | `http.get` | `(url: string) -> map` | HTTP GET request (WinHTTP on Windows) |
| 92 | `http.post` | `(url: string, body: string) -> map` | HTTP POST request |
| 93 | `http.request` | `(options: map) -> map` | Generic HTTP request |
| 94 | `http.serve` | `(addr: string, handler: fn) -> void` | Start HTTP server **[STUB]** |
| 95 | `http.encodeURI` | `(s: string) -> string` | URL encode |
| 96 | `http.decodeURI` | `(s: string) -> string` | URL decode |
| 97 | `http.parseJSON` | `(s: string) -> map` | Parse JSON response |

> **Status**: HTTP client (get/post/request) implemented via WinHTTP on Windows in P0-3.1 (commit 5744bf3). Returns `{ok, status, body, error}` map. `http.serve` (94) remains stub. `encodeURI`/`decodeURI`/`parseJSON` are pure computation helpers.

---

## 6. process Module (Host ABI) — P0-2 + P0-3.1 extension

| Index | Name | Signature | Description |
|-------|------|-----------|-------------|
| 120 | `process.exit` | `(code?: int) -> void` | Exit VM with status code |
| 121 | `process.argv` | `() -> array<string>` | Command-line arguments |
| 122 | `process.env` | `() -> map<string,string>` | Environment variables |
| 127 | `process.cwd` | `() -> string` | Current working directory |
| 128 | `process.chdir` | `(path: string) -> void` | Change working directory |
| 131 | `process.platform` | `() -> string` | OS platform: "windows"/"linux"/"darwin" |

## 6b. time Module (Host ABI) — P0-3.1

| Index | Name | Signature | Description |
|-------|------|-----------|-------------|
| 123 | `time.now` | `() -> int` | Unix timestamp in seconds |
| 124 | `time.nowMs` | `() -> int` | Unix timestamp in milliseconds |
| 125 | `time.sleep` | `(ms: int) -> void` | Sleep for given milliseconds |
| 126 | `time.date` | `() -> string` | Local date/time as "YYYY-MM-DD HH:MM:SS" |

## 6c. io stderr (Host ABI) — P0-3.1

| Index | Name | Signature | Description |
|-------|------|-----------|-------------|
| 129 | `io.eprint` | `(value: any) -> void` | Print to stderr (no newline) |
| 130 | `io.eprintln` | `(value: any) -> void` | Print to stderr + newline |

### process.argv layout
`[tllvm_path, bytecode_path, user_arg1, user_arg2, ...]`
User arguments start at index 2.

### process.env behavior
- Returns a Map of all environment variables at call time.
- Read-only (no set/unset in current version).
- On Windows, keys are normalized to uppercase.
- Missing keys return `null`.

### process.exit behavior
- Sets VM exit flag and returns.
- Native launcher propagates the exit code to the OS.
- Default code is 0 if omitted.

---

## 7. Host ABI Requirements

A conforming TLL implementation must:

1. Provide all Host ABI builtins (or throw "not implemented" for unavailable ones)
2. File paths use the host OS's native path format
3. stdin/stdout/stderr map to the process's standard streams
4. Network operations follow the host OS's network stack
5. process.exit code must propagate to the OS exit code
6. process.argv must include the launcher path and bytecode path as indices 0 and 1

---

## 8. Implementation Freedom

Host ABI implementations are platform-specific. For example:

| Platform | io.println | fs.readFile | process.env |
|----------|-----------|-------------|-------------|
| C (Native VM) | printf | fopen/fread | environ |
| WASM | JS bridge | WASI fs | JS bridge |
| Rust | println! | std::fs::read | std::env::vars |

All must produce the same observable behavior from the TLL program's perspective.
