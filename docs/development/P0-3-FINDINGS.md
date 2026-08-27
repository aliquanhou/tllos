# P0-3 Dogfooding Findings

**Date**: 2026-08-27
**Milestone**: P0-3 TLL Commercial Foundation
**Dogfooding Project**: tools/tllhttp/ (TLL HTTP CLI Client)

---

## Finding #1: process.argv / process.env not registered in compiler codegen

**Severity**: Critical
**Layer**: Compiler (codegen.tll)
**Status**: Fixed

### Problem
process.argv() and process.env() returned empty results when called from TLL programs compiled via tllc. process.argv() returned argc=0 even when command-line arguments were provided.

### Root Cause
compiler/codegen.tll function cg_getBuiltinIndex() only registered process.exit (idx 120) but was missing mappings for process.argv (idx 121) and process.env (idx 122). The Runtime implementations in host/c/builtin.c existed and were correct, but the compiler never emitted the correct builtin call opcodes.

### Reproduction
fn main() -> void {
    let argv = process.argv()
    io.println("argc: " + convert.toString(arrays.length(argv)))
}
main()
Compiled via tllc compile test.tll -o test.tllbc, then tllvm test.tllbc arg1 arg2 -> output argc: 0.

### Fix
Added missing mappings in compiler/codegen.tll:
if modName == "process" {
    if fnName == "exit" { return 120 }
    if fnName == "argv" { return 121 }
    if fnName == "env" { return 122 }
}

### Regression
- Re-bootstrap compiler (seed updated)
- Re-bootstrap tllc
- process.argv() now returns correct argc=4 with all arguments
- process.env() verified working via tools/envget/

---

## Finding #2: Linker getDir() only handles '/' path separator, breaks Windows

**Severity**: Critical
**Layer**: Compiler (linker.tll)
**Status**: Fixed

### Problem
When compiling a TLL program with relative imports from a directory other than the current working directory (e.g., tllc compile tools/tllhttp/main.tll from repo root), imported modules were not linked. The resulting bytecode had fewer functions than expected, and calls to imported functions were silently no-ops.

### Root Cause
compiler/linker.tll function getDir() only searched for '/' as path separator. On Windows, paths use '\' (e.g., tools\tllhttp\main.tll). Since no '/' was found, getDir returned '.' (cwd), causing resolveModulePath to look for ./http_client.tll in the repo root instead of tools/tllhttp/http_client.tll.

### Reproduction
From repo root: tllc compile tools/tllhttp/main.tll -o tllhttp.tllbc
Output: Functions: 3 (should be 6)
http_client.tll functions not linked.
From tools/tllhttp/ directory: Functions: 6 (correct).

### Fix
Updated getDir() to handle both '/' and '\' separators.

### Regression
- Re-bootstrap compiler (seed updated)
- From repo root: tllc compile tools/tllhttp/main.tll -> Functions: 6 (correct)
- tllhttp get command works: fetches URL, prints response, saves to file

---

## Capability Gaps Identified

1. No uninitialized variable declaration: let result: map (without initializer) is not supported.
2. time.now() resolution is seconds only, no millisecond precision.
3. No stderr output builtin (no io.eprintln).
4. http.post/request/serve are stub, only http.get implemented.

---

## Verification Status

| Item | Status |
|------|--------|
| process.argv/env codegen mapping | Fixed |
| Linker getDir Windows separator | Fixed |
| Self-host deterministic (Gen1==Gen2) | Verified (hash: 69A3C7E2...) |
| ABI spec alignment (123-125) | Done |
| ABI consistency check | PASS |
| tllhttp Dogfooding project | Working (get, get -o, help) |
| Full test suite | Under investigation (1 failure) |
| Fresh Clone verification | Pending |
| Tag TLL-OS-P0-3.0 | Pending |
