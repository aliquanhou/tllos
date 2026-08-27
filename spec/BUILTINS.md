# TLL OS Builtins Specification

**Version**: 1.2
**Status**: Genesis 0-97 FROZEN; P0-2 extensions 120+ active
**Total defined**: 101 builtins (idx 0-97, 120-122)
**Reserved**: 98-119 (agent/workflow, deferred)

> This file is the canonical builtin ABI specification. It MUST match `host/c/builtin.c` exactly. Run `scripts/check-abi.sh` / `scripts\check-abi.bat` to verify consistency.

---

## io (Host ABI) — idx 0-2

| # | Name | Signature |
|---|------|-----------|
| 0 | `io.println` | `(value: any) -> void` |
| 1 | `io.print` | `(value: any) -> void` |
| 2 | `io.readLine` | `(prompt?: string) -> string` |

## json (Stdlib) — idx 3-4

| # | Name | Signature |
|---|------|-----------|
| 3 | `json.parse` | `(s: string) -> any` |
| 4 | `json.stringify` | `(value: any) -> string` |

## math (Stdlib) — idx 5-23

| # | Name | Signature |
|---|------|-----------|
| 5 | `math.sqrt` | `(n: float) -> float` |
| 6 | `math.abs` | `(n: number) -> number` |
| 7 | `math.floor` | `(n: float) -> int` |
| 8 | `math.ceil` | `(n: float) -> int` |
| 9 | `math.round` | `(n: float) -> int` |
| 10 | `math.min` | `(a: number, b: number) -> number` |
| 11 | `math.max` | `(a: number, b: number) -> number` |
| 12 | `math.pow` | `(base: number, exp: number) -> number` |
| 13 | `math.sin` | `(n: float) -> float` |
| 14 | `math.cos` | `(n: float) -> float` |
| 15 | `math.tan` | `(n: float) -> float` |
| 16 | `math.log` | `(n: float) -> float` (natural log) |
| 17 | `math.log2` | `(n: float) -> float` |
| 18 | `math.log10` | `(n: float) -> float` |
| 19 | `math.exp` | `(n: float) -> float` |
| 20 | `math.pi` | `() -> float` (constant) |
| 21 | `math.e` | `() -> float` (constant) |
| 22 | `math.random` | `() -> float` [0,1) |
| 23 | `math.randomInt` | `(min: int, max: int) -> int` [min,max] |

## strings (Stdlib) — idx 24-48

| # | Name | Signature |
|---|------|-----------|
| 24 | `strings.length` | `(s: string) -> int` |
| 25 | `strings.toUpper` | `(s: string) -> string` |
| 26 | `strings.toLower` | `(s: string) -> string` |
| 27 | `strings.trim` | `(s: string) -> string` |
| 28 | `strings.trimStart` | `(s: string) -> string` |
| 29 | `strings.trimEnd` | `(s: string) -> string` |
| 30 | `strings.split` | `(s: string, sep: string) -> array<string>` |
| 31 | `strings.join` | `(arr: array, sep: string) -> string` |
| 32 | `strings.contains` | `(s: string, sub: string) -> bool` |
| 33 | `strings.startsWith` | `(s: string, prefix: string) -> bool` |
| 34 | `strings.endsWith` | `(s: string, suffix: string) -> bool` |
| 35 | `strings.substring` | `(s: string, start: int, end: int) -> string` |
| 36 | `strings.replace` | `(s: string, old: string, new: string) -> string` |
| 37 | `strings.replaceAll` | `(s: string, old: string, new: string) -> string` |
| 38 | `strings.repeat` | `(s: string, n: int) -> string` |
| 39 | `strings.padStart` | `(s: string, len: int, pad: string) -> string` |
| 40 | `strings.padEnd` | `(s: string, len: int, pad: string) -> string` |
| 41 | `strings.charAt` | `(s: string, i: int) -> string` |
| 42 | `strings.charCodeAt` | `(s: string, i: int) -> int` |
| 43 | `strings.indexOf` | `(s: string, sub: string) -> int` |
| 44 | `strings.lastIndexOf` | `(s: string, sub: string) -> int` |
| 45 | `strings.isEmpty` | `(s: string) -> bool` |
| 46 | `strings.reverse` | `(s: string) -> string` |
| 47 | `strings.lines` | `(s: string) -> array<string>` |
| 48 | `strings.words` | `(s: string) -> array<string>` |

## arrays (Stdlib) — idx 49-71

> No `set` function. Use direct index assignment: `arr[idx] = val`.

| # | Name | Signature |
|---|------|-----------|
| 49 | `arrays.length` | `(a: array) -> int` |
| 50 | `arrays.get` | `(a: array, i: int) -> any` |
| 51 | `arrays.push` | `(a: array, v: any...) -> int` |
| 52 | `arrays.pop` | `(a: array) -> any` |
| 53 | `arrays.shift` | `(a: array) -> any` |
| 54 | `arrays.unshift` | `(a: array, v: any...) -> int` |
| 55 | `arrays.concat` | `(a: array, b: array) -> array` |
| 56 | `arrays.slice` | `(a: array, start: int, end: int) -> array` |
| 57 | `arrays.includes` | `(a: array, v: any) -> bool` |
| 58 | `arrays.indexOf` | `(a: array, v: any) -> int` |
| 59 | `arrays.join` | `(a: array, sep: string) -> string` |
| 60 | `arrays.reverse` | `(a: array) -> array` (mutates) |
| 61 | `arrays.sort` | `(a: array) -> array` (mutates, numeric) |
| 62 | `arrays.filter` | `(a: array, fn: fn) -> array` |
| 63 | `arrays.map` | `(a: array, fn: fn) -> array` |
| 64 | `arrays.reduce` | `(a: array, fn: fn, init?: any) -> any` |
| 65 | `arrays.forEach` | `(a: array, fn: fn) -> void` |
| 66 | `arrays.find` | `(a: array, fn: fn) -> any` |
| 67 | `arrays.some` | `(a: array, fn: fn) -> bool` |
| 68 | `arrays.every` | `(a: array, fn: fn) -> bool` |
| 69 | `arrays.flat` | `(a: array, depth?: int) -> array` |
| 70 | `arrays.fill` | `(a: array, v: any, start?: int, end?: int) -> array` |
| 71 | `arrays.range` | `(start: int, end: int, step?: int) -> array<int>` |

## convert (Stdlib) — idx 72-78

| # | Name | Signature |
|---|------|-----------|
| 72 | `convert.toInt` | `(v: any) -> int` |
| 73 | `convert.toFloat` | `(v: any) -> float` |
| 74 | `convert.toString` | `(v: any) -> string` |
| 75 | `convert.toBool` | `(v: any) -> bool` |
| 76 | `convert.toChar` | `(code: int) -> string` |
| 77 | `convert.charCode` | `(s: string) -> int` |
| 78 | `convert.typeOf` | `(v: any) -> string` |

## fs (Host ABI) — idx 79-90

| # | Name | Signature |
|---|------|-----------|
| 79 | `fs.readFile` | `(path: string) -> string` |
| 80 | `fs.writeFile` | `(path: string, content: string) -> void` |
| 81 | `fs.appendFile` | `(path: string, content: string) -> void` |
| 82 | `fs.exists` | `(path: string) -> bool` |
| 83 | `fs.mkdir` | `(path: string) -> void` |
| 84 | `fs.remove` | `(path: string) -> void` |
| 85 | `fs.listDir` | `(path: string) -> array<string>` |
| 86 | `fs.isFile` | `(path: string) -> bool` |
| 87 | `fs.isDir` | `(path: string) -> bool` |
| 88 | `fs.fileSize` | `(path: string) -> int` |
| 89 | `fs.copyFile` | `(src: string, dst: string) -> void` |
| 90 | `fs.rename` | `(old: string, new: string) -> void` |

## http (Host ABI) — idx 91-97 (STUB)

> HTTP builtins return `null` in bootstrap mode. Full implementation planned for P0-2.8.

| # | Name | Signature |
|---|------|-----------|
| 91 | `http.get` | `(url: string) -> map` |
| 92 | `http.post` | `(url: string, body: string) -> map` |
| 93 | `http.request` | `(options: map) -> map` |
| 94 | `http.serve` | `(addr: string, handler: fn) -> void` |
| 95 | `http.encodeURI` | `(s: string) -> string` |
| 96 | `http.decodeURI` | `(s: string) -> string` |
| 97 | `http.parseJSON` | `(s: string) -> map` |

## process (Host ABI) — idx 120-122, 127-128, 131 (P0-2 + P0-3.1 extensions)

> P0-2 process API (120-122). P0-3.1 extensions (127-128, 131).

| # | Name | Signature |
|---|------|-----------|
| 120 | `process.exit` | `(code?: int) -> void` |
| 121 | `process.argv` | `() -> array<string>` |
| 122 | `process.env` | `() -> map<string,string>` |
| 127 | `process.cwd` | `() -> string` |
| 128 | `process.chdir` | `(path: string) -> void` |
| 131 | `process.platform` | `() -> string` ("windows"/"linux"/"darwin") |

## time (Host ABI) — idx 123-126 (P0-3.1)

| # | Name | Signature |
|---|------|-----------|
| 123 | `time.now` | `() -> int` (Unix timestamp seconds) |
| 124 | `time.nowMs` | `() -> int` (Unix timestamp milliseconds) |
| 125 | `time.sleep` | `(ms: int) -> void` |
| 126 | `time.date` | `() -> string` ("YYYY-MM-DD HH:MM:SS" local time) |

## io stderr (Host ABI) — idx 129-130 (P0-3.1)

| # | Name | Signature |
|---|------|-----------|
| 129 | `io.eprint` | `(value: any) -> void` (print to stderr, no newline) |
| 130 | `io.eprintln` | `(value: any) -> void` (print to stderr + newline) |

---

## Reserved
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

## Reserved

- **98-119**: agent/workflow builtins (deferred)

---

## Notes

1. All builtins are called via `OP_LOAD_BUILTIN` + `OP_CALL` (indirect call with fnIdx >= 100000)
2. `io.println` and `io.print` are compiler intrinsics, inlined as OP_PRINTLN/OP_PRINT when called directly
3. Stdlib builtins (json/math/strings/arrays/convert) are pure computation and could be reimplemented in TLL
4. Host ABI builtins (io/fs/http/process) require OS access and must be implemented by the VM host
5. **ABI consistency check**: `scripts/check-abi.bat` (Windows) / `scripts/check-abi.sh` (Linux/macOS) verifies this spec matches `host/c/builtin.c`
