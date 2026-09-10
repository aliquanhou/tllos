# P2-01-B11-R1-R2-R3-FINAL: Builtin Registry Bidirectional Consistency Gate

**施工对象**: `feature/P2-01-B11-R1-ownership-closure`
**基线**: `b670be7` (R3 initial)
**本阶段**: R3-FINAL Builtin Registry Gate Closure
**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）

---

## 1. Reality Audit 结论

### 1.1 现有架构事实

- Native Target 没有运行时 builtin 注册/分发机制，所有 builtin 函数都是直接生成 C 函数调用。
- `nl_builtinFunctions` 列表是 lowering 侧的 builtin 分类注册表，用于 `nl_isBuiltinFunction()` 判断一个函数调用是否是 builtin 调用。
- Runtime header (`runtime/tll_runtime.h` + `native/runtime/tll_native.h`) 声明了所有 C 函数，包括 language-callable builtins 和 runtime-internal/lifecycle API。

### 1.2 R3 初始状态发现的问题

1. **`nl_builtinFunctions` 包含 44 项，但混入了 runtime-internal API**:
   - `tll_runtime_init`, `tll_runtime_cleanup`, `tll_native_init`, `tll_native_cleanup`
   - 这些是编译器生成的生命周期调用，不是 language-callable builtin。

2. **包含不存在的函数**:
   - `tll_array_from`, `tll_array_push`, `tll_array_get`, `tll_array_set`
   - `tll_map_get`, `tll_map_set`
   - 实际函数名是 `array_push`, `array_get`, `array_set`, `map_get`, `map_set`（没有 `tll_` 前缀）。

3. **包含未使用的函数**:
   - `tll_neg`, `tll_not`
   - 实际生成代码中使用 `tll_int(-...)` 和 `tll_bool(!...)`，不调用这两个函数。

4. **Validator 只有单向检查** (header → lowering)，没有反向检查 (lowering → header)。

5. **没有明确区分 language-callable builtin 和 runtime-internal API**。

---

## 2. Canonical Registry Contract

### 2.1 语义分类

**Language-Callable Builtin Registry** (`nl_builtinFunctions`):
- 可以在 TLL 源代码中直接调用的 builtin 函数（直接或通过运算符/方法 lowering）。
- 这是 `nl_isBuiltinFunction()` 的唯一 canonical 来源。

**Runtime-Internal / Lifecycle API** (`nl_runtimeInternalFunctions`):
- 编译器内部生成的生命周期调用，不是用户可调用的 language builtin。
- 仅用于 validator 排除，不参与 `nl_isBuiltinFunction()` 判断。

### 2.2 Canonical Registry 内容（38 项）

**值创建 (6)**: `tll_null`, `tll_bool`, `tll_int`, `tll_float`, `tll_string`, `tll_string_n`
**容器创建 (2)**: `tll_array`, `tll_map`
**函数/builtin 创建 (2)**: `tll_function`, `tll_builtin`
**引用计数 (2)**: `tll_value_incref`, `tll_value_free`
**Test-only 调试 (2)**: `tll_debug_refcount`, `tll_debug_print_refcount`
**真值/相等 (2)**: `tll_truthy`, `tll_equals`
**赋值 (1)**: `tll_assign`
**转换 (2)**: `tll_to_string`, `tll_to_json`
**算术 (5)**: `tll_add`, `tll_sub`, `tll_mul`, `tll_div`, `tll_mod`
**比较 (6)**: `tll_eq`, `tll_neq`, `tll_lt`, `tll_gt`, `tll_le`, `tll_ge`
**数组操作 (3)**: `array_push`, `array_get`, `array_set`
**Map 操作 (3)**: `map_set`, `map_get`, `map_has`
**IO (2)**: `tll_io_print`, `tll_io_println`

### 2.3 Runtime-Internal API（4 项，排除）

`tll_runtime_init`, `tll_runtime_cleanup`, `tll_native_init`, `tll_native_cleanup`

---

## 3. Bidirectional Validator

### 3.1 Validator 升级内容

`scripts/verify-builtin-registry.ps1` 升级为双向 Gate:

**Direction A (Canonical registry → actual native binding)**:
- Registry 中存在但 runtime header 中不存在的函数 → FAIL

**Direction B (Actual language-callable native binding → canonical registry)**:
- Runtime header 中存在的 language-callable 函数但 registry 缺失 → FAIL

**Additional checks**:
- Registry 出现重复 builtin → FAIL
- Runtime-internal / non-language-callable API 错误进入 builtin registry → FAIL
- 失败返回 non-zero exit code
- 失败打印明确的 missing / extra / duplicate / misclassified diff
- PASS 打印 canonical source 与双方计数

### 3.2 Validator 输出

```
=== TLL Native Builtin Registry Verification (Bidirectional) ===

Canonical registry (nl_builtinFunctions): 38 entries
Runtime-internal API (nl_runtimeInternalFunctions): 4 entries

Runtime header all functions: 42 entries
Runtime header language-callable: 38 entries
Runtime header runtime-internal: 4 entries

=== Verification Results ===

Canonical source: compiler/native_lower.tll (nl_builtinFunctions)
Binding source: runtime/tll_runtime.h + native/runtime/tll_native.h
Registry count: 38
Language-callable binding count: 38
Runtime-internal binding count: 4
Duplicates: 0
Misclassified: 0
Direction A (registry -> binding): ALL PRESENT
Direction B (binding -> registry): ALL PRESENT

=== BUILTIN REGISTRY VERIFICATION: PASS ===
```

**Exit code: 0**

---

## 4. Final Validation Gates

### 4.1 Builtin Registry Gate
- **Result**: PASS
- **Direction A**: 38/38 registry entries present in runtime header
- **Direction B**: 38/38 language-callable header functions present in registry
- **Duplicates**: 0
- **Misclassified**: 0
- **Runtime-internal exclusion**: 4/4 correctly excluded

### 4.2 Native Conformance
- **Result**: 21/21 PASS
- **Tests**: 01_basic through 20_assignment_return_consumer + cross_target_minimal
- **Command**: `tllvm.exe native_compile_driver.tllbc <input.tll> <output.c>` + `cl /O2 /utf-8 ...`

### 4.3 Bytecode / Native Parity
- **Result**: 13/14 PASS (B11-related tests)
- **Note**: Test 19 (`19_refcount_machine_evidence`) uses Native-only test-only function `tll_debug_print_refcount()`, which does not exist in Bytecode VM. This is expected test design, not a parity failure.
- **All other 13 B11-related tests**: Bytecode output == Native output, exit codes match

### 4.4 Assignment-scope ASan
- **Result**: 9/9 PASS
- **Tests**: 08, 13, 14, 15, 16, 17, 18, 19, 20
- **Command**: `cl /fsanitize=address ...`
- **No UAF / double-free / heap-overflow detected**

### 4.5 Bootstrap Regression
- **Result**: PASS
- **Command**: `scripts/bootstrap-tllc.bat`
- **Output**: `tllc.tllbc built, Size: 856851 bytes`

### 4.6 MSVC Baseline
- **Result**: Compile SUCCESS (Exit 0)
- **Command**: `cl /nologo /O2 /utf-8 /W4 /I native\runtime /I runtime ...`
- **Warnings**: All pre-existing (C4996 strdup/strcpy/strcat deprecation, C4100 unused argc/argv), none introduced by this change

### 4.7 Scope Regression
- **Result**: 10/10 PASS
- **Tests**: scope_01 through scope_10
- **Includes**: scope_10_complete_chain (previously fixed regression)

### 4.8 Git Diff Audit
- **Modified files**: `compiler/native_lower.tll`, `scripts/verify-builtin-registry.ps1`
- **No temporary files / build artifacts / backup files in commit**
- **No out-of-scope changes**

---

## 5. Preserved B11 Fixes (No Regression)

以下 R3 已发现/修复的内容全部保留，未回退：

1. ✅ Ownership Contract v2.0 (canonical)
2. ✅ Test 19 refcount machine instrumentation (`tll_debug_refcount`, `tll_debug_print_refcount`)
3. ✅ Test 20 assignment-as-return consumer with explicit machine assertions
4. ✅ `let b = a` Ident-RHS ownership/incref fix (prevents use-after-free on reassignment)
5. ✅ Assignment ownership correct order: `incref(new) → free(old) → store → return borrow`
6. ✅ `nl_exprHasTemporaryRef()` recursive temporary ref detection
7. ✅ Nested assignment closure: `y = (x = "a")`, `let y = (x = "a")`
8. ✅ RHS exactly once observable proof (test 17)

---

## 6. Known Limitations / Deferred GAPs

1. **Function Return Ownership GAP** (test 09 ASan UAF): Pre-existing, deferred to P2-01-B12 or later. Not in scope of B11-R3.
2. **MSVC ASan leak detection**: Windows platform does not support ASan leak detection. UAF/double-free/heap-overflow detection works.
3. **Linux/macOS native target**: Not yet validated. Windows/MSVC is the primary target for Phase 2-01.
4. **Test 19 Bytecode parity**: Uses Native-only test-only function. Expected design, not a failure.

---

## 7. Exact Commands

```powershell
# Builtin Registry Verification
powershell -ExecutionPolicy Bypass -File scripts\verify-builtin-registry.ps1

# Native Conformance (per test)
& host\c\tllvm.exe compiler\native_compile_driver.tllbc tests\native\<test>.tll tests\native\<test>.c
cmd /c "vcvarsall.bat x64 && cl /nologo /O2 /utf-8 /I native\runtime /I runtime <test>.c native\runtime\tll_native.c runtime\value.c runtime\arithmetic.c runtime\io.c /Fe:<test>.exe"

# Bytecode/Native Parity
& host\c\tllvm.exe tools\TLLC\tllc.tllbc compile tests\native\<test>.tll tests\native\<test>.tllbc
& host\c\tllvm.exe tests\native\<test>.tllbc  # Bytecode
# Native as above, compare stdout + exit code

# Assignment-scope ASan
cl /nologo /O2 /utf-8 /fsanitize=address /I native\runtime /I runtime <test>.c native\runtime\tll_native.c runtime\value.c runtime\arithmetic.c runtime\io.c /Fe:<test>_asan.exe

# Bootstrap
cmd /c scripts\bootstrap-tllc.bat

# Scope Regression
& host\c\tllvm.exe tools\TLLC\tllc.tllbc compile tests\scope\<test>.tll tests\scope\<test>.tllbc
& host\c\tllvm.exe tests\scope\<test>.tllbc
```

---

## 8. Conclusion

**P2-01-B11-R1-R2-R3-FINAL Builtin Registry Bidirectional Consistency Gate: 施工完成。**

- Canonical Language-Callable Builtin Registry established (38 entries)
- Runtime-Internal API explicitly separated and excluded (4 entries)
- Bidirectional validator PASS (Direction A + Direction B + duplicates + misclassification)
- All existing B11 ownership fixes preserved
- Native 21/21, Bytecode/Native parity 13/14 (1 expected design exception), ASan 9/9, Bootstrap PASS, MSVC baseline SUCCESS, Scope 10/10

**施工完成，等待架构师独立审查与最终验收。**

**PASS / SEALED / CLOSED 只能由架构师独立验收后决定。**
