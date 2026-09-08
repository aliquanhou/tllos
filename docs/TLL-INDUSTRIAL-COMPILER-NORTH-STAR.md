# TLL Industrial Compiler — Architecture North Star

> Status: LONG-TERM STRATEGY / NOT CURRENT PHASE
> Created: 2026-09-08
> This document is the strategic north star for TLL Compiler evolution.
> It is NOT an implementation plan for any single phase.

## 1. Strategic Positioning

The current TLL Compiler (180 functions / 4706 constants) is classified as:

**Bootstrap / Development Compiler**

It is NOT the final TLL Compiler. The final goal is:

> Build an industrial-grade, self-hosting, optimizing, cross-platform TLL Compiler
> capable of supporting large-scale real-world software.

Final code size may reach millions of lines, but:
- **NEVER pile code for line count**
- All scale must come from real compiler capability

## 2. Final Compiler Pipeline

```
TLL Source
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
Name Resolution
    ↓
Module Resolution
    ↓
Type System
    ↓
Generic / Trait System
    ↓
Semantic Analysis
    ↓
HIR
    ↓
MIR
    ↓
TLL IR
    ↓
Optimization Pipeline
    ↓
Backend
 ┌──────┼────────┐
 ↓      ↓        ↓
Native  WASM    Future Backends
 ↓
Machine Code
```

## 3. Required Capabilities (Long Term)

- Debug Information
- Error Diagnostics
- Incremental Compilation
- Dependency Management
- Package Compilation
- Cross Compilation
- Profile Guided Optimization
- Linking / LTO
- Caching
- Parallel Compilation
- Reproducible Builds
- Security / Capability Checks
- FFI
- Testing Infrastructure
- Compiler Tooling
- Language Server
- Formatter
- Linter
- Documentation Generator

## 4. IR Layer (Critical)

The current `AST → VM opcode` path is temporary. Final architecture must include:

```
AST → HIR → MIR → TLL IR → Backend
```

This enables: optimization, multi-backend, Native, WASM, JIT, AOT, SIMD, parallel compilation, PGO.

## 5. Backend Strategy

Do not reinvent what LLVM already solves. Future evaluation:

```
TLL Frontend → TLL IR → Backend Layer (Native / LLVM / Cranelift / WASM)
```

**Current priority: build TLL Frontend / Type System / IR first. Do not integrate LLVM yet.**

## 6. Large Project Support

Final validation targets are NOT just hello.tll / test.tll. Must support:

- Large CLI tools
- HTTP Servers
- Database Applications
- Web Applications
- Agent Systems
- Blockchain
- Compiler
- Runtime
- TLL OS

**TLL Compiler must eventually compile itself.** (Self-hosting is final phase, not current prerequisite.)

## 7. Performance Benchmarks

Must establish real metrics:
- Compile Time
- Incremental Compile Time
- Memory Usage
- AST Size / IR Size
- Optimization Time
- Code Generation Time
- Binary Size
- Runtime Performance
- Parallel Compilation Scaling

No "feels fast" — must have data.

## 8. Current Phase Roadmap

```
Language Completeness
        ↓
Type System
        ↓
Module / Package
        ↓
Error / Resource
        ↓
Concurrency
        ↓
Compiler IR
        ↓
Optimization
        ↓
Backend
        ↓
Toolchain
        ↓
Self-hosting
```

Each phase: Implement → Minimal Verify → Persistent Tests → Evidence → CI → Seal.

## 9. Success Metric

NOT: "few hundred functions" (that's just the spark)
NOT: "millions of lines" (that's not success by itself)

**TRUE SUCCESS: TLL Compiler is an industrial-grade compiler that can long-term support
TLL language, TLL Runtime, TLL OS, and a large real-world software ecosystem.**

We are building an industrial machine, not a toy compiler.

---

*This document is a living north star. Update as architecture evolves.
Do NOT implement everything at once. One ladder at a time.*
