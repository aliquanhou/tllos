# P2-01-B11-R1-R2-R3-FINAL-R1: Builtin Semantic Classification Closure

**施工对象**: `feature/P2-01-B11-R1-ownership-closure`
**基线**: `8379bc4` (R3-FINAL)
**本阶段**: R3-FINAL-R1 Three-tier Semantic Classification Closure
**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）

---

## 1. 架构裁决（第二轮 Reality Audit 结论）

### 1.1 方案 B：接受当前 Native 架构

经独立 Reality Audit 确认：
- **没有独立的 Native Builtin Registration / Dispatch Registry**
- `native/runtime/tll_native.c` 不是 builtin dispatcher，只负责 `tll_native_init/cleanup → tll_runtime_init/cleanup`
- Native Target 的 builtin 调用机制是：**TLL AST → native_lower.tll → 直接生成 C function call → runtime/*.c**
- 不是：TLL builtin → runtime registry → dispatch table → C implementation

### 1.2 禁止过度施工

**禁止**为了满足 validator 而去创建新的 C builtin registry / dispatch table。
当前 Native 架构本身就是直接生成 C call。如果为了"真正 binding registry"强行引入 `BuiltinRegistry[]` / `BuiltinID` / `dispatch()`，那就是为了 Gate 改架构，属于过度施工。

### 1.3 Runtime Header ≠ Builtin Registry

`runtime/tll_runtime.h` + `native/runtime/tll_native.h` 是 **Native ABI declaration surface**，不是严格意义上的 Language Builtin Registry。
Header 把以下东西放在同一个公共声明面：
- Value creation / Reference counting / Truth/equality / Assignment / Conversion
- Arithmetic / Comparison / Array/Map / IO
- Runtime Lifecycle (init/cleanup)

因此 Validator 必须**分类**，不能假设所有 header function = builtin。

---

## 2. Three-tier Semantic Classification

### 2.1 定义

**Tier 1: Language-Callable Builtins** (`nl_builtinFunctions`)
- Stable API invocable from TLL source (directly or via operator/method lowering)
- 这是 `nl_isBuiltinFunction()` 的唯一 canonical 来源
- 数量：**36**

**Tier 2: Runtime-Internal / Lifecycle APIs** (`nl_runtimeInternalFunctions`)
- Compiler-generated lifecycle calls only (init/cleanup)
- NOT language-callable
- 仅用于 validator 排除，不参与 `nl_isBuiltinFunction()`
- 数量：**4**

**Tier 3: Test-only Verification APIs** (`nl_testOnlyFunctions`)
- Compiler/runtime instrumentation for ownership/lifetime tests ONLY
- Marked "NOT part of public ABI / ONLY for verification tests" in runtime header
- MUST NOT be used in production code or exposed as stable API
- 数量：**2**

### 2.2 Canonical Registry 内容（36 项 Language-Callable）

**值创建 (6)**: `tll_null`, `tll_bool`, `tll_int`, `tll_float`, `tll_string`, `tll_string_n`
**容器创建 (2)**: `tll_array`, `tll_map`
**函数/builtin 创建 (2)**: `tll_function`, `tll_builtin`
**引用计数 (2)**: `tll_value_incref`, `tll_value_free`
**真值/相等 (2)**: `tll_truthy`, `tll_equals`
**赋值 (1)**: `tll_assign`
**转换 (2)**: `tll_to_string`, `tll_to_json`
**算术 (5)**: `tll_add`, `tll_sub`, `tll_mul`, `tll_div`, `tll_mod`
**比较 (6)**: `tll_eq`, `tll_neq`, `tll_lt`, `tll_gt`, `tll_le`, `tll_ge`
**数组操作 (3)**: `array_push`, `array_get`, `array_set`
**Map 操作 (3)**: `map_set`, `map_get`, `map_has`
**IO (2)**: `tll_io_print`, `tll_io_println`

### 2.3 Runtime-Internal（4 项，排除）

`tll_runtime_init`, `tll_runtime_cleanup`, `tll_native_init`, `tll_native_cleanup`

### 2.4 Test-only（2 项，排除）

`tll_debug_refcount`, `tll_debug_print_refcount`

---

## 3. Validator 升级（Tier-Aware Bidirectional Gate）

### 3.1 从 native_lower.tll 读取分类（无硬编码）

Validator 不再使用硬编码的 `$runtimeInternalNames` 列表。
所有三个分类列表都从 `compiler/native_lower.tll` 中提取：
- `nl_builtinFunctions` → Language-Callable
- `nl_runtimeInternalFunctions` → Runtime-Internal
- `nl_testOnlyFunctions` → Test-only

### 3.2 Header 函数分类

Validator 从 runtime headers 提取所有函数声明，然后按 canonical 列表分类：
- 在 `nl_builtinFunctions` 中 → Language-Callable
- 在 `nl_runtimeInternalFunctions` 中 → Runtime-Internal
- 在 `nl_testOnlyFunctions` 中 → Test-only
- 都不在 → Unclassified（FAIL）

### 3.3 验证检查项

1. **Duplicate check**: 每个 canonical 列表内无重复
2. **Cross-tier contamination check**: 一个函数不出现在多个 canonical 列表中
3. **Misclassification check**: `nl_builtinFunctions` 不包含 runtime-internal 或 test-only 函数
4. **Direction A (registry → binding)**: 每个 language-builtin 都存在于 runtime header
5. **Direction B (binding → registry)**: 每个 language-callable header 函数都在 registry 中
6. **Unclassified check**: header 中没有未分类的函数
7. **Runtime-internal completeness**: canonical runtime-internal 列表与 header 一致
8. **Test-only completeness**: canonical test-only 列表与 header 一致

### 3.4 Validator 输出

```
Canonical registry (from compiler/native_lower.tll):
  Language-Callable Builtins: 36
  Runtime-Internal/Lifecycle: 4
  Test-only Verification:     2

Runtime Header (Native ABI surface): 42 total functions

Header classification:
  Language-Callable: 36
  Runtime-Internal:  4
  Test-only:         2
  Unclassified:      0

Architecture: Native direct C-call surface (NO runtime dispatcher)
Canonical source: compiler/native_lower.tll (three-tier lists)
Runtime Header: Native ABI declaration surface (NOT a builtin registry)

Duplicates: 0
Cross-tier contamination: 0
Misclassification: 0
Direction A (registry -> binding): ALL PRESENT
Direction B (binding -> registry): ALL PRESENT
Runtime lifecycle != builtin: CONFIRMED
Test-only instrumentation != stable builtin: CONFIRMED

=== BUILTIN REGISTRY VERIFICATION: PASS ===
```

**Exit code: 0**

---

## 4. Final Validation Gates

| 验证项 | 结果 |
|--------|------|
| Builtin Registry Gate (三层分类, 双向) | **PASS** |
| Native Conformance | **21/21 PASS** |
| Assignment-scope ASan | **9/9 PASS** |
| Bootstrap Regression | **PASS** (856851 bytes) |
| Scope Regression | **10/10 PASS** (含 scope_10) |
| MSVC Baseline (/W4) | **SUCCESS** (所有 warnings 为已存在的 strdup/strcpy 弃用) |
| Git Diff Audit | **CLEAN** (仅 native_lower.tll + validator + evidence doc) |

---

## 5. Preserved B11 Fixes (No Regression)

以下所有 B11 已有修复全部保留，未回退：

1. ✅ Ownership Contract v2.0 (canonical)
2. ✅ Test 19 refcount machine instrumentation (`tll_debug_refcount`, `tll_debug_print_refcount`) — 现在明确分类为 Test-only
3. ✅ Test 20 assignment-as-return consumer with explicit machine assertions
4. ✅ `let b = a` Ident-RHS ownership/incref fix
5. ✅ Assignment ownership correct order: `incref(new) → free(old) → store → return borrow`
6. ✅ `nl_exprHasTemporaryRef()` recursive temporary ref detection
7. ✅ Nested assignment closure: `y = (x = "a")`, `let y = (x = "a")`
8. ✅ RHS exactly once observable proof (test 17)

---

## 6. Key Changes from R3-FINAL (8379bc4)

1. **`nl_builtinFunctions` 从 38 项减少到 36 项**：移除 `tll_debug_refcount` 和 `tll_debug_print_refcount`（重新分类为 Test-only）
2. **新增 `nl_testOnlyFunctions` 列表**（2 项）：明确 Test-only Verification API 分类
3. **Validator 完全重写**：
   - 从 native_lower.tll 读取三个分类列表（无硬编码）
   - Header 函数按 canonical 列表分类
   - 新增 cross-tier contamination check
   - 新增 misclassification check
   - 新增 unclassified check
   - 明确输出 "Runtime Header = Native ABI surface, NOT a builtin registry"
4. **注释更新**：明确架构裁决（方案 B）、三层分类定义、Runtime Header ≠ Builtin Registry

---

## 7. Known Limitations / Deferred GAPs

1. **Function Return Ownership GAP** (test 09 ASan UAF): Pre-existing, deferred to P2-01-B12 or later. Not in scope of B11-R3.
2. **MSVC ASan leak detection**: Windows platform does not support ASan leak detection. UAF/double-free/heap-overflow detection works.
3. **Linux/macOS native target**: Not yet validated. Windows/MSVC is the primary target for Phase 2-01.
4. **CI status**: GitHub CI for this commit not yet verified. Local tests all PASS.

---

## 8. Exact Commands

```powershell
# Builtin Registry Verification (three-tier, bidirectional)
powershell -ExecutionPolicy Bypass -File scripts\verify-builtin-registry.ps1

# Native Conformance (per test)
& host\c\tllvm.exe compiler\native_compile_driver.tllbc tests\native\<test>.tll tests\native\<test>.c
cmd /c "vcvarsall.bat x64 && cl /nologo /O2 /utf-8 /I native\runtime /I runtime <test>.c native\runtime\tll_native.c runtime\value.c runtime\arithmetic.c runtime\io.c /Fe:<test>.exe"

# Assignment-scope ASan
cl /nologo /O2 /utf-8 /fsanitize=address /I native\runtime /I runtime <test>.c native\runtime\tll_native.c runtime\value.c runtime\arithmetic.c runtime\io.c /Fe:<test>_asan.exe

# Bootstrap
cmd /c scripts\bootstrap-tllc.bat

# Scope Regression
& host\c\tllvm.exe tools\TLLC\tllc.tllbc compile tests\scope\<test>.tll tests\scope\<test>.tllbc
& host\c\tllvm.exe tests\scope\<test>.tllbc
```

---

## 9. CI Status and Causal Isolation (Acceptance Closure)

### 9.1 Real GitHub CI Status

**Commit**: `2b1aff7`
**CI Run**: #444, Run ID: `34314962153`
**Branch**: `feature/P2-01-B11-R1-ownership-closure`
**Overall CI Result**: **FAILURE**

**Failure point**: macOS Native Build/Test Job → Coroutine 100K Stress Test

**All other steps PASS**:
- Native Build/Compile ✅
- Native ABI Tests ✅
- Bootstrap ✅
- Blockchain/P2P Tests ✅
- Scope Tests (incl. scope_10) ✅
- (All other CI steps not related to Coroutine 100K) ✅

### 9.2 Causal Isolation: Coroutine 100K Failure ≠ B11 R1 Regression

**Formal evidence that the Coroutine 100K Stress Test failure has NO causal relationship with B11 R1 changes:**

| Evidence Item | Fact |
|---------------|------|
| **B11 R1 modification scope** | Only 3 files: `compiler/native_lower.tll`, `scripts/verify-builtin-registry.ps1`, `docs/...evidence.md` |
| **Coroutine/worker runtime files touched?** | **NO** — B11 R1 did not modify any coroutine, worker, scheduler, or VM runtime code |
| **`tests/coroutine_stress_test.tll` modified?** | **NO** — Not in B11 R1 diff (`8379bc4..2b1aff7`) |
| **Last modification of coroutine_stress_test.tll** | `e3ea92a` ("P0-15.15: Unified Runtime Scheduler...") — long before B11 R1 |
| **Pre-existing issue registration** | Issue #7: "Coroutine 100K Stress Test fails on Ubuntu 24.04 and macOS CI" — registered as independent GAP before B11 R1 |
| **CI workflow annotation** | ci.yml line 467: "No Runtime code modifications — if this fails, Runtime has a real bug." |
| **Test nature** | Pure Runtime/coroutine stability test (100K immediate-return + 10K x10 yield + 1K sleep coroutines). Tests VM scheduler/worker lifecycle, completely unrelated to Native lowering builtin classification. |

### 9.3 Conclusion on CI Gate

- **B11 R1 Semantic Classification**: PASS (all targeted/static verification)
- **Full CI**: FAIL due to pre-existing independent Coroutine 100K GAP (Issue #7)
- **Causal relationship**: NONE — Coroutine 100K failure is not introduced or affected by B11 R1
- **B11 SEAL status**: NOT SEALED (pending architect's final decision on CI gate acceptance)

**Per established engineering principle**: "开发阶段允许局部红；核心 Gate 必须有真实证据。不要为了 CI 的颜色牺牲开发进度，更不能为了绿色篡改工程真相。"

The Coroutine 100K failure is an **independently registered, pre-existing Runtime GAP** (Issue #7), not a B11 R1 regression. It should be tracked and fixed in its own independent track, not block B11 semantic classification closure.

---

## 10. Conclusion

**P2-01-B11-R1-R2-R3-FINAL-R1 Builtin Semantic Classification Closure: 施工完成。**

- 架构方案 B 确认：Native direct C-call surface，NO runtime dispatcher
- Three-tier semantic classification established:
  - Language-Callable Builtins: 36 (stable API)
  - Runtime-Internal/Lifecycle: 4 (compiler-generated)
  - Test-only Verification: 2 (instrumentation only)
- Runtime Header explicitly defined as Native ABI surface, NOT a builtin registry
- Validator upgraded to tier-aware bidirectional gate (no hardcoded classification)
- Validator PASS: 36↔36 language-callable, 4↔4 runtime-internal, 2↔2 test-only, 0 unclassified
- All B11 ownership fixes preserved
- Native 21/21, ASan 9/9, Bootstrap PASS, Scope 10/10
- CI: Full CI FAIL due to pre-existing independent Coroutine 100K GAP (Issue #7); causal isolation proven — NOT a B11 R1 regression

**施工完成，等待架构师独立审查与最终验收。**

**PASS / SEALED / CLOSED 只能由架构师独立验收后决定。**

施工执行：Agent A
架构审查：GPT-5.6 Luna
最终裁决：于秋鸿博士（待验收）
