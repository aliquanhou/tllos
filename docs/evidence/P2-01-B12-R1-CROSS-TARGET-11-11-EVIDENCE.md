# P2-01-B12-R1 Cross-Target 11/11 Conformance Evidence

**Baseline:** 5bd31facb78ba640850ecd964ab70a78d1259562
**Branch:** feature/P2-01-B12-native-target-final-seal
**Date:** 2026-09-10
**Runner:** scripts/cross-target-conformance.ps1 (existing repository tool)
**Status:** Evidence Closure — awaiting independent architecture audit

---

## 1. Methodology

Each of the first 11 Native tests (01-11) was run through the existing `scripts/cross-target-conformance.ps1` runner, which:

1. Compiles the TLL source to Bytecode via `tools/TLLC/tllc.tllbc`
2. Lowers the TLL source to C via `compiler/native_compile_driver.tllbc` (native_lower.tll)
3. Compiles the generated C with MSVC (cl.exe, /O2)
4. Runs the Bytecode on tllvm.exe
5. Runs the Native executable
6. Compares stdout and exit code

**No compiler/runtime/source modifications were made.** This is evidence-only closure.

---

## 2. Machine-Readable Summary

| # | Test | Bytecode Exit | Native Exit | Exit Identical | Stdout Identical | Overall |
|---|------|---------------|-------------|----------------|-------------------|---------|
| 01 | basic | 0 | 0 | True | True | PASS |
| 02 | function | 0 | 0 | True | True | PASS |
| 03 | io | 0 | 0 | True | True | PASS |
| 04 | control_flow | 0 | 0 | True | True | PASS |
| 05 | array | 0 | 0 | True | True | PASS |
| 06 | map | 0 | 0 | True | True | PASS |
| 07 | ownership_local | 0 | 0 | True | True | PASS |
| 08 | ownership_assignment | 0 | 0 | True | True | PASS |
| 09 | ownership_return | 0 | 0 | True | True | PASS |
| 10 | ownership_container | 0 | 0 | True | True | PASS |
| 11 | ownership_function_argument | 0 | 0 | True | True | PASS |

**Total: 11/11 PASS**

---

## 3. Per-Test Evidence Details

### 3.1 01_basic
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.2 02_function
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.3 03_io
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.4 04_control_flow
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.5 05_array
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.6 06_map
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.7 07_ownership_local
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.8 08_ownership_assignment
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.9 09_ownership_return
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.10 10_ownership_container
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

### 3.11 11_ownership_function_argument
- Bytecode compile: PASS
- Native lower: PASS
- Native compile: PASS
- Bytecode exit: 0
- Native exit: 0
- Exit identical: True
- Stdout identical: True
- Overall: PASS

---

## 4. Build Environment

- **OS:** Windows x64
- **Bytecode compiler:** tools/TLLC/tllc.tllbc (tracked)
- **Native lowerer:** compiler/native_compile_driver.tllbc → compiler/native_lower.tll
- **Native compiler:** MSVC cl.exe (Visual Studio 2022 Build Tools)
- **Native compile flags:** /nologo /O2 /utf-8 /I native\runtime /I runtime
- **Runtime sources:** native/runtime/tll_native.c + runtime/value.c + runtime/arithmetic.c + runtime/io.c
- **Bytecode VM:** host/c/tllvm.exe

---

## 5. Artifact Hygiene

The following temporary artifacts were generated during conformance testing and are NOT committed:
- `tests/native/*.tllbc` (compiled bytecode)
- `tests/native/*.c` (generated C)
- `tests/native/*.exe` (compiled native executables)
- `tests/native/*.native_out.txt` (native stdout capture)
- `tests/native/*.bytecode_out.txt` (bytecode stdout capture)
- `tests/native/*.evidence.txt` (per-test evidence files, content consolidated into this document)

Only this consolidated evidence document is committed.

---

## 6. Scope Boundary

- **No compiler modifications**
- **No runtime modifications**
- **No source/test modifications**
- **No ownership semantics changes**
- **Only evidence closure** using the existing `scripts/cross-target-conformance.ps1` runner

This document closes the B12 Cross-Target 11/11 evidence gap identified in the independent architecture audit of 5bd31fa.

---

**施工完成，等待架构师审查与于秋鸿博士最终验收。**
