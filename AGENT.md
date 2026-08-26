# AGENT.md — Guide for AI Contributors

This file helps AI agents understand and contribute to TLL OS effectively.

## What is TLL OS?

TLL OS is a specification-driven, self-hosted programming language. The compiler, VM, and standard library are all written in TLL itself. A small Native Launcher written in C provides the Stage-0 bootstrap: it loads TLL bytecode and executes it. Once the TLL VM is running, all compilation and execution are handled by TLL itself.

**TLL OS Genesis does not depend on Node.js, npm, TypeScript, or JavaScript.**

## Directory Layout

```
compiler/    — TLL compiler source (pure .tll)
runtime/     — TLL VM source (pure .tll)
host/c/      — Native C Launcher (Stage-0 bootstrap only)
package/     — Package manager (pure .tll)
stdlib/      — Standard library (pure .tll)
spec/        — Language specification (Markdown)
tests/       — Test suite (.tll source + .tllbc artifacts)
docs/        — Developer documentation
examples/    — Example programs
tools/       — TLL developer tools (pure .tll)
```

## How to Build the Native Launcher

The Native Launcher is the only component that requires a C compiler. It is a Stage-0 bootstrap tool, not part of the TLL language implementation.

### Windows (MSVC)

```bash
cd host/c
cl /O2 /D_CRT_SECURE_NO_WARNINGS /Dalloca=_alloca /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c
```

### Windows (TCC)

```bash
host/c/tcc/tcc/tcc.exe -O2 -std=c99 -D_WIN32 "-Wl,-stack=0x4000000" -o tllvm.exe main.c vm.c value.c json.c builtin.c
```

### Linux/macOS (gcc/clang)

```bash
cd host/c
gcc -O2 -o tllvm main.c vm.c value.c json.c builtin.c
```

## How to Run

Execute a compiled TLL bytecode file:

```bash
tllvm program.tllbc
```

## Native Self-Hosting Bootstrap

The repository includes a pre-built compiler seed (`compiler/compiler.tllbc`). To verify self-hosting:

```bash
# Generation 1: seed compiler compiles compiler.tll
tllvm compiler/compiler.tllbc
# Output: compiler_self_compiled.tllbc

# Generation 2: new compiler compiles compiler.tll again
tllvm compiler_self_compiled.tllbc
# Output: compiler_self_compiled.tllbc

# Verify determinism: SHA256 of both generations must match
```

The bootstrap seed SHA256 is:
`7D45DC155804854EE08263E0A61D956FA28CC03E49B9140D4004C200A4624315`

## FROZEN Items (Do NOT Modify)

These are frozen at v1.1. Changes require major version bump:

1. **Opcodes 0-45** — See `spec/OPCODES.md`
2. **Closure semantics** — UpvalueBox, shared box, flat closure, isolation
3. **Bytecode schema** — `{functions, constants, mainFunctionIndex, globalCount}`
4. **Builtin indices 0-97** — See `spec/BUILTINS.md`
5. **Module import syntax** — `from "./path" import name`

## Key Implementation Details

- **Closure opcodes:** OP_CLOSURE(42), OP_GET_UPVALUE(43), OP_SET_UPVALUE(44), OP_BOX_LOCAL(45)
- **Function value:** `{__fn: true, fnIdx: N, env: null|ClosureEnv}`
- **Indirect call:** OP_CALL with func >= 100000 means register-based indirect call
- **TLL arrays have no `set` function** — use direct index: `arr[idx] = val`
- **vm_run.tll** reads `vm_run_target.tllbc` from cwd and executes it via TLL VM
- **Production chain:** C Compiler → tllvm → compiler.tllbc (seed) → TLL Compiler → user.tllbc → tllvm → execution
- **Native Launcher boundary:** C only loads bytecode, dispatches opcodes, and provides Host ABI (stdout, filesystem, etc.). It must NOT implement TLL language semantics (lexer, parser, typechecker, codegen, closure semantics).

## Testing Rules

- Every new feature needs tests
- Do not modify existing tests to make them pass
- Do not delete failing tests
- Test artifacts are `.tllbc` files compiled from `.tll` source
- Run tests via: `tllvm tests/<path>/<test>.tllbc`

## When Stuck

1. Check `spec/` for language specification
2. Check `docs/architecture/` for design docs
3. Look at existing tests in `tests/` for patterns
4. The TLL Semantic VM in `runtime/vm.tll` is the executable language specification
5. The Native VM in `host/c/` must conform to `spec/`, not the other way around
