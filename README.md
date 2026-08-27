# TLL OS

> An AI-Native Programming Language and Runtime

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-P0--4%20dev-yellow.svg)](https://github.com/aliquanhou/tllos)

TLL OS is a **specification-driven, self-hosted programming language** with a pure-TLL compiler, native bytecode VM, and first-class support for functions, closures, modules, and packages. It is designed to be the foundation for AI-native application development.

**Current phase: P0-4 Language Capability Completion.** Active development includes Lambda/Closure, Struct, Enum, and a growing TLL-native standard library (stdlib/). See [docs/development/](docs/development/) for phase details.

**TLL OS v1 is Native-Only.** The production toolchain does not depend on Node.js, npm, TypeScript, or JavaScript. A C compiler is only needed to build the native launcher once; after that, TLL compiles and runs itself.

**Licensed under the Apache License, Version 2.0.**

---

## Features

- **Self-hosting compiler** — The TLL compiler is written in TLL and compiles itself natively
- **Native bytecode VM** — 46 opcodes, including closure support (OP_CLOSURE 42, OP_GET_UPVALUE 43, OP_SET_UPVALUE 44, OP_BOX_LOCAL 45)
- **First-class functions and closures** — Function values, higher-order functions, nested functions, mutable capture, shared box, escaping closures
- **Anonymous functions (Lambda)** — `fn(params) -> type { body }` inline function expressions (P0-4)
- **Struct declarations** — `struct Name { field: type }` with field access and mutation (P0-4, literal syntax deferred)
- **Enum declarations** — `enum Name { Variant = value }` for enumerated constants (P0-4, variant access deferred)
- **TLL-native standard library** — `stdlib/array.tll`, `stdlib/string.tll`, `stdlib/math.tll`, `stdlib/json.tll` — 34+ functions implemented in pure TLL (P0-4)
- **Module and package system** — `from "./path" import name`, `tll.toml` manifest
- **Native process API** — `process.argv`, `process.env`, `process.exit`, `process.cwd`, `process.chdir`, `process.platform`
- **Native time API** — `time.now`, `time.nowMs`, `time.sleep`, `time.date` (P0-3.1)
- **Native HTTP client** — `http.get`, `http.post`, `http.request` via WinHTTP (P0-3.1, `http.serve` stub)
- **Native file system API** — `fs.readFile`, `fs.writeFile`, `fs.listDir`, etc.
- **Native self-hosting** — Deterministic SHA256-verified multi-generation bootstrap
- **Spec First Architecture** — Language Specification is the sole semantic authority; all VMs are implementations of the Spec

---

## Quick Start

### Prerequisites

- A C compiler (gcc, clang, or MSVC) — only for building the native launcher
- **No Node.js, npm, TypeScript, or JavaScript required**

### 1. Build Native Launcher

**Linux/macOS:**
```bash
git clone https://github.com/aliquanhou/tllos.git
cd tllos
scripts/build.sh
```

**Windows (TCC, bundled):**
```cmd
git clone https://github.com/aliquanhou/tllos.git
cd tllos
scripts\build.bat
```

**Windows (MSVC):**
```cmd
cd host\c
cl /O2 /D_CRT_SECURE_NO_WARNINGS /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c
```

### 2. Bootstrap tllc (TLL Compiler CLI)

tllc is written in TLL and must be bootstrapped from the compiler seed:

**Linux/macOS:**
```bash
scripts/bootstrap-tllc.sh
```

**Windows:**
```cmd
scripts\bootstrap-tllc.bat
```

This produces `tools/TLLC/tllc.tllbc`.

### 3. Compile and Run a Program

```bash
# Compile hello.tll -> hello.tllbc
host/c/tllvm tools/TLLC/tllc.tllbc compile hello.tll

# Run the compiled bytecode
host/c/tllvm hello.tllbc
# Output: Hello from TLL!
```

### 4. Compile and Run Tests

```bash
# Compile all test .tll files -> .tllbc
scripts/compile-tests.sh    # or compile-tests.bat on Windows

# Run all tests
scripts/run-tests.sh        # or run-tests.bat on Windows
```

**Test assertion mechanism:**
- **Exit code:** Tests named `exitN.tll` (e.g. `exit42.tll`) expect exit code N. All others expect exit 0.
- **Stdout:** If `<testname>.expected.txt` exists alongside the test, stdout is compared against it byte-for-byte.
- Test `.tllbc` files are NOT tracked in git (except bootstrap seeds); always generate them via `compile-tests`.

### tllc Commands

| Command | Description |
|---------|-------------|
| `tllc help` | Show help |
| `tllc compile <file.tll>` | Compile to `.tllbc` (same name) |
| `tllc compile <file> -o <out>` | Compile to custom output |
| `tllc check <file.tll>` | Compile check, no output file |
| `tllc info <file.tllbc>` | Show bytecode program info |

> **Note:** tllc is invoked via `tllvm tools/TLLC/tllc.tllbc <command>`. A standalone wrapper is planned for a future release.

### Native Self-Hosting Verification

```bash
cd host/c
# The compiler seed (compiler.tllbc) is tracked in git
./tllvm ../../compiler/compiler.tllbc
# This compiles compiler.tll -> compiler_self_compiled.tllbc
# Run it again to verify deterministic self-hosting
./tllvm ../../compiler/compiler_self_compiled.tllbc
# SHA256 of both generations must match
```

---

## Architecture

```
                 TLL OS v1
                    │
          ┌─────────┴─────────┐
          │                   │
       Native VM         Native Compiler
          │                   │
          └─────────┬─────────┘
                    │
             compiler.tllbc
              【Git 火种】
                    │
                    ▼
             Native Self-Host
                    │
                    ▼
                TLL OS
```

**Bootstrap chain:** C compiler builds `tllvm` → `tllvm` loads `compiler.tllbc` seed → TLL compiler compiles `compiler.tll` → new `compiler.tllbc` → repeat for deterministic verification.

**Production chain:** TLL Compiler → `.tllbc` bytecode → Native VM → execution.

**C is only the first spark.** Once `tllvm` is built, all compilation and execution is handled by TLL itself.

---

## Project Structure

```
tllos/
├── compiler/          # TLL Compiler (pure TLL)
│   ├── compiler.tll   # Entry point
│   ├── compiler.tllbc # Bootstrap seed (tracked in git)
│   ├── bootstrap_tllc.tll # tllc bootstrap entry
│   ├── lexer.tll
│   ├── parser.tll
│   ├── typechecker.tll
│   ├── codegen.tll
│   └── linker.tll
├── runtime/           # TLL Semantic VM (pure TLL)
│   ├── vm.tll         # Executable language specification
│   ├── vm_run.tll     # VM runner entry
│   └── vm_run.tllbc   # VM runner seed (tracked in git)
├── package/           # Package system
│   └── package.tll
├── host/              # Native host implementation
│   └── c/             # C Native Launcher (Stage-0 bootstrap)
│       ├── main.c
│       ├── vm.c
│       ├── value.c
│       ├── json.c
│       ├── builtin.c
│       ├── tllvm.h
│       ├── Makefile
│       └── tcc.zip    # Bundled TCC for Windows
├── tools/
│   ├── TLLC/          # tllc - TLL Compiler CLI (pure TLL)
│   │   ├── main.tll
│   │   ├── cli.tll
│   │   ├── compiler_driver.tll
│   │   └── formatter.tll
│   └── envget/        # envget - Dogfooding CLI tool (process.argv + process.env + process.exit)
│       └── main.tll
├── scripts/           # Build & test automation
│   ├── build.bat / build.sh
│   ├── bootstrap-tllc.bat / bootstrap-tllc.sh
│   ├── compile-tests.bat / compile-tests.sh
│   └── run-tests.bat / run-tests.sh
├── tests/             # Test suite (.tll source; .tllbc generated by scripts)
│   ├── acceptance/    # Language feature tests
│   └── regression/    # Bug regression tests (exitN.tll = expected non-zero exit code)
├── examples/          # Example programs
├── spec/              # Machine-readable specs
├── docs/              # Developer documentation (docs/development/ for phase logs)
└── .github/           # CI workflows
```

---

## Native Bootstrap Verification

TLL OS verifies self-hosting deterministically:

1. **Generation 1:** seed compiler compiles `compiler.tll` → `compiler_self_compiled.tllbc`
2. **Generation 2:** Gen1 compiler compiles `compiler.tll` → overwrites `compiler_self_compiled.tllbc`
3. **Determinism:** `SHA256(Gen1) == SHA256(Gen2)`

**Important:** The compiler reads source files relative to the current working directory.
You MUST run self-host verification from the `compiler/` directory:

```bash
# From repository root:
cd compiler
../host/c/tllvm compiler.tllbc          # Generation 1
sha256sum compiler_self_compiled.tllbc  # Record Gen1 hash
../host/c/tllvm compiler_self_compiled.tllbc  # Generation 2
sha256sum compiler_self_compiled.tllbc  # Must match Gen1
```

On Windows, use `..\host\c\tllvm.exe compiler.tllbc` and `Get-FileHash -Algorithm SHA256`.

Both generations produce byte-identical output, proving the compiler is self-consistent.

**Current deterministic hash (P0-2.4.1):**
`623098D8246D6CB9A006364BFF6103DA340923F1A6888446EBFA390D74E30418`

---

## Language Core (Frozen v1.1)

The following are frozen and must not change without a major version bump:

- Lexer, Parser, AST, Type System
- Function Value, Nested Function, Closure semantics
- Upvalue / Shared Box / Isolation (flat closure model)
- Module / Package / Linker
- Bytecode schema
- **Opcode contract 0-45** (especially 42-45: CLOSURE, GET_UPVALUE, SET_UPVALUE, BOX_LOCAL)
- TLL VM execution model
- Builtin/stdlib API
- Value ownership model (reference counting)

See `spec/` for full machine-readable specification.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

[Apache License 2.0](LICENSE)
