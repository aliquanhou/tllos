# TLL OS

> An AI-Native Programming Language and Runtime

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-green.svg)](https://github.com/aliquanhou/tllos)

TLL OS is a **specification-driven, self-hosted programming language** with a pure-TLL compiler, native bytecode VM, and first-class support for functions, closures, modules, and packages. It is designed to be the foundation for AI-native application development.

**TLL OS v1 is Native-Only.** The production toolchain does not depend on Node.js, npm, TypeScript, or JavaScript. A C compiler is only needed to build the native launcher once; after that, TLL compiles and runs itself.

**Licensed under the Apache License, Version 2.0.**

---

## Features

- **Self-hosting compiler** — The TLL compiler is written in TLL and compiles itself natively
- **Native bytecode VM** — 46 opcodes, including closure support (OP_CLOSURE 42, OP_GET_UPVALUE 43, OP_SET_UPVALUE 44, OP_BOX_LOCAL 45)
- **First-class functions and closures** — Function values, higher-order functions, nested functions, mutable capture, shared box, escaping closures
- **Module and package system** — `from "./path" import name`, `tll.toml` manifest
- **Native self-hosting** — Deterministic SHA256-verified multi-generation bootstrap
- **Spec First Architecture** — Language Specification is the sole semantic authority; all VMs are implementations of the Spec

---

## Quick Start

### Prerequisites

- A C compiler (gcc, clang, or MSVC) — only for building the native launcher
- **No Node.js, npm, TypeScript, or JavaScript required**

### Build Native Launcher

```bash
git clone https://github.com/aliquanhou/tllos.git
cd tllos
cd host/c
gcc -O2 -std=c99 -o tllvm main.c vm.c value.c json.c builtin.c
```

On Windows with MSVC:

```cmd
cd host\c
cl /O2 /D_CRT_SECURE_NO_WARNINGS /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c
```

### Run a Program

```bash
# Run pre-compiled bytecode
./tllvm ../../tests/acceptance/01_hello.tllbc
# Output: Hello, TLL!
```

### Native Self-Hosting

```bash
cd host/c
# The compiler seed (compiler.tllbc) is tracked in git
./tllvm ../../compiler/compiler.tllbc
# This compiles compiler.tll → compiler_self_compiled.tllbc
# Run it again to verify deterministic self-hosting
./tllvm ../../compiler/compiler_self_compiled.tllbc
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
│       └── tllvm.h
├── stdlib/            # Standard library
├── tools/             # Developer tooling (TLL)
├── tests/             # Test suite
├── examples/          # Example programs
├── language/          # Language specification
├── spec/              # Machine-readable specs
├── docs/              # Developer documentation
└── website/           # Project website
```

---

## Native Bootstrap Verification

TLL OS v1 verifies self-hosting deterministically:

1. **Generation 1:** `tllvm` + `compiler.tllbc` → compiles `compiler.tll` → `compiler_v2.tllbc`
2. **Generation 2:** `tllvm` + `compiler_v2.tllbc` → compiles `compiler.tll` → `compiler_v3.tllbc`
3. **Determinism:** `SHA256(compiler_v2.tllbc) == SHA256(compiler_v3.tllbc)`

Both generations produce byte-identical output, proving the compiler is self-consistent.

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
