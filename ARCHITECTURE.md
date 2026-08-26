# TLL OS Architecture

## High-Level Architecture

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

## Layers

### 1. TLL Language Core (Frozen v1.1)

- **Compiler** (`compiler/`): lexer, parser, typechecker, codegen, linker — all pure TLL
- **Semantic VM** (`runtime/vm.tll`): executable language specification — pure TLL
- **Package** (`package/`): tll.toml manifest and dependency resolution — pure TLL

### 2. Native Host Layer (`host/c/`)

- C Native Launcher (`tllvm`): Stage-0 bootstrap loader
- Loads `.tllbc` bytecode, initializes VM, executes opcodes, provides Host ABI
- **C is only the first spark** — once tllvm is built, TLL compiles and runs itself
- C does NOT implement TLL language semantics (lexer, parser, typechecker, codegen, closure semantics)

### 3. Bootstrap Seed (`compiler/compiler.tllbc`)

- Pre-compiled TLL compiler bytecode, tracked in git
- Enables fresh-clone self-hosting without any TS/JS toolchain
- `tllvm compiler.tllbc` → compiles `compiler.tll` → new `compiler.tllbc`

### 4. Production Execution Chain

```
C Compiler → tllvm (Native Launcher)
    ↓
compiler.tllbc (Bootstrap Seed)
    ↓
TLL Compiler (pure TLL)
    ↓
user.tll → user.tllbc
    ↓
Native VM (host/c)
    ↓
user program output
```

No Node.js, npm, TypeScript, or JavaScript in the production chain.

## Native Self-Hosting (Deterministic)

```
Generation 1: tllvm + compiler.tllbc → compiles compiler.tll → compiler_v2.tllbc
Generation 2: tllvm + compiler_v2.tllbc → compiles compiler.tll → compiler_v3.tllbc

Verify: SHA256(compiler_v2.tllbc) == SHA256(compiler_v3.tllbc)
```

Both generations produce byte-identical output, proving the compiler is self-consistent.

## Spec First Architecture

TLL OS has exactly one semantic authority: the **Language Specification** (`spec/`).

- Native VM (`host/c/`) is an implementation of the Spec
- Semantic VM (`runtime/vm.tll`) is an executable reference implementation of the Spec
- Any VM (C, Rust, Go, WASM) must conform to the same Spec
- When implementations disagree, the Spec is the source of truth

## Closure Model

```
outer frame
    │
    ├── local x
    │
    ▼
UpvalueBox { value: x }
    ▲
    │
closure.env.upvalues[0]  (shared by all sibling closures)
```

- **Shared box:** sibling closures reference the same UpvalueBox
- **Isolation:** each outer invocation creates new UpvalueBox instances
- **Flat closure:** deeply nested closures directly reference outer UpvalueBox, no chain
- **Escaping:** UpvalueBox survives frame destruction via closure.env reference
- **Ownership:** reference counting; frozen in `spec/VALUE_MODEL.md` §11

## Frozen Opcode Contract (0-45)

| Opcode | Number | Purpose |
|--------|--------|---------|
| OP_CLOSURE | 42 | Create closure from function value |
| OP_GET_UPVALUE | 43 | Read captured upvalue |
| OP_SET_UPVALUE | 44 | Write captured upvalue |
| OP_BOX_LOCAL | 45 | Box local variable for closure capture |

Full specification: `spec/OPCODES.md`

## Repository Identity

- **Repository:** aliquanhou/tllos (sole official source of truth)
- **License:** Apache-2.0
- **Genesis:** TLL-OS-GENESIS-NATIVE
- **No TS/JS dependency** in production toolchain
- **C compiler** is only needed to build the native launcher once
