# P1-03 HMAC-SHA256 - Evidence Document

**Status**: P1-03-R1 COMPLETE (RFC 4231 7/7, pending CI and总指挥 final SEAL验收)
**Date**: 2026-09-05
**Initial Commit**: d9b0412 (HMAC-SHA256 implementation)
**Initial CI Run ID**: 33905434201 (3-platform all green)
**P1-03-R1 Commit**: (pending - TLL Binary Bytes + RFC 4231 Full)
**P1-03-R1 CI Run ID**: (pending)

## P1-03-R1: TLL Binary Bytes Testability Closure

总指挥验收 P1-03 时发现：RFC 4231 只通过了 TC2（文本密钥），TC1/TC3/TC4/TC6/TC7（二进制密钥）因 TLL 不支持 `\xNN` 十六进制字节转义而未测试。总指挥要求：必须补全 TLL 语言的二进制字节表达能力，然后完成 RFC 4231 全部 7 个测试用例。

### 实现：TLL `\xNN` Hex Escape（Lexer）
- **文件**: `compiler/lexer.tll`
- **新增函数**: `hexDigitValue(ch)` - 将十六进制数字字符转换为整数值（0-15）
- **转义处理**: 在字符串字面量的 `\` 转义处理中添加 `\xNN` 支持
  - 读取 `\x` 后最多 2 个十六进制数字
  - 转换为 0-255 的字节值
  - 使用 `convert.toChar(value)` 转换为对应字符
  - 若没有有效十六进制数字，则输出字面量 `x`
- **不破坏现有语义**: 所有现有转义（`\n`, `\t`, `\r`, `\\`, `\"`, `\0`）保持不变

### 编译器 Bootstrap
- 旧编译器编译新编译器: `tllc_hex.tllbc` (663,530 bytes, Functions 172, Constants 3889)
- 新编译器自举: `tllc_hex2.tllbc` (663,530 bytes, Functions 172, Constants 3889)
- 两次编译结果一致（文件大小相同）
- 新编译器已替换 `tools/TLLC/tllc.tllbc` 作为标准 bootstrap seed

### `\xNN` 基础测试（`tests/crypto/test_hex_escape.tll`）
- Test 1: `\x41\x42\x43` = "ABC", length 3 ✅
- Test 2: `Hello\x20World` = "Hello World" ✅
- Test 3: 3x `\x0b` bytes, charCodeAt(0) = 11 ✅
- Test 4: 所有 255 个字节值（1-255）通过 `convert.toChar` 验证 ✅

### RFC 4231 全量测试（`tests/crypto/gate_rfc4231_full.tll`）
全部 7 个测试用例，8 个测试（TC5 包含 full 和 truncated）：

| TC | Key | Data | 结果 |
|----|-----|------|------|
| TC1 | 0x0b * 20 | "Hi There" | ✅ PASS |
| TC2 | "Jefe" | "what do ya want for nothing?" | ✅ PASS |
| TC3 | 0xaa * 20 | 0xdd * 50 | ✅ PASS |
| TC4 | 0x01-0x19 (25 bytes) | 0xcd * 50 | ✅ PASS |
| TC5 (full) | 0x0c * 20 | "Test With Truncation" | ✅ PASS |
| TC5 (truncated) | 0x0c * 20 | "Test With Truncation" (128-bit) | ✅ PASS |
| TC6 | 0xaa * 131 (>block size) | "Test Using Larger Than Block-Size Key..." | ✅ PASS |
| TC7 | 0xaa * 131 | long text (>block size, 152 bytes) | ✅ PASS |

**结果: 8/8 PASS (RFC 4231 7/7 Test Cases)**

所有期望值经 Python `hashlib`/`hmac` 独立验证（修正了初始复制时的笔误）。

### CI 配置更新
- 新增 "P1-03 RFC 4231 Full Test Vector Suite" 步骤（Linux/macOS + Windows）
- 使用 `tools/TLLC/tllc.tllbc`（已更新为支持 `\xNN` 的版本）编译和运行测试
- 验证输出包含 "ALL TESTS PASSED"

---

## 1. API Specification

### TLL Builtin Functions (idx 190-194)

| idx | Function | Description |
|-----|----------|-------------|
| 190 | `hmac.sha256(key, message)` | Compute HMAC-SHA256, return lowercase hex string |
| 191 | `hmac.sha256Raw(key, message)` | Compute HMAC-SHA256, return hex (raw bytes placeholder for future bytes type) |
| 192 | `sha256.hash(message)` | Compute SHA-256, return lowercase hex string |
| 193 | `sha256.hashRaw(message)` | Compute SHA-256, return hex (raw bytes placeholder) |
| 194 | `hmac.verify(key, message, expectedHex)` | Verify HMAC in constant time, return bool |

### Output Format
- SHA-256: 64 lowercase hex characters (32 bytes)
- HMAC-SHA256: 64 lowercase hex characters (32 bytes)
- All outputs verified to be exactly 64 characters, all lowercase hex

## 2. Implementation Details

### Source Files
- `host/c/hmac_builtin.c` (~10.8KB) - SHA-256 + HMAC-SHA256 implementation + TLL builtin binding
- `host/c/tllvm.h` - Added `hmac_builtin_invoke` declaration
- `host/c/builtin.c` - Added idx 190-199 dispatch to `hmac_builtin_invoke`
- `compiler/codegen.tll` - Added hmac module (idx 190-191, 194) and sha256 module (idx 192-193) function mapping
- `compiler/linker.tll` - Added "hmac", "sha256" to stdlibs list
- `host/c/Makefile` - Added hmac_builtin.c to SRCS
- `.github/workflows/ci.yml` - Added hmac_builtin.c to Linux/macOS/Windows build commands + HMAC gate test steps

### SHA-256 Implementation (FIPS 180-4)
- Complete SHA-256 algorithm per FIPS 180-4 specification
- SHA256_CTX structure: state[8], bitlen (uint64), data[64], datalen
- 64 K constants (first 64 primes' cube root fractions)
- Message schedule: W[0-15] from input, W[16-63] via SIG0/SIG1
- Compression function: 64 rounds with CH, MAJ, EP0, EP1
- Padding: 0x80 + zeros + 64-bit big-endian bit length
- Supports multi-block messages (tested with 1000-byte message)

### HMAC-SHA256 Implementation (RFC 2104)
- Complete HMAC algorithm per RFC 2104
- Key > 64 bytes: hash key first with SHA-256
- Key <= 64 bytes: zero-pad to 64 bytes
- Inner hash: H((key XOR 0x36) || message)
- Outer hash: H((key XOR 0x5c) || inner_hash)
- Tested with 70-byte key (> block size)

### Security Features
- Constant-time hex string comparison in `hmac.verify` (XOR all bytes, check result == 0)
- No timing side-channel in verification
- All intermediate buffers zeroed where applicable

## 3. Important Finding: Test Vector Correction

### Initial Test Failure (11 PASS / 6 FAIL)
The initial gate test showed 6 failures. Investigation revealed **all failures were due to incorrect expected values in the test program**, NOT bugs in the SHA-256/HMAC implementation.

### Errors Found in Test Expected Values
1. **SHA-256('abc')**: Expected value had byte 20 as `0xa9`, correct value is `0xa3`
   - Incorrect: `...b00361a96177a9c...`
   - Correct:   `...b00361a396177a9c...`

2. **SHA-256(56-byte)**: Expected value was 63 hex chars (missing final `c1`)
   - Incorrect: `...19db06` (63 chars)
   - Correct:   `...19db06c1` (64 chars)

3. **SHA-256(fox dog)**: Expected value was 63 hex chars (missing final `2`)
   - Incorrect: `...c9e59` (63 chars)
   - Correct:   `...c9e592` (64 chars)

4. **RFC4231 TC2**: Expected value was 63 hex chars (missing final `3`)
   - Incorrect: `...ec384` (63 chars)
   - Correct:   `...ec3843` (64 chars)

5. **RFC4231 TC5**: Expected value was 63 hex chars (missing final `5`)
   - Incorrect: `...cd20c` (63 chars)
   - Correct:   `...cd20c5` (64 chars)

6. **hmac.verify correct**: Used 63-char expected value, should be 64 chars

### Independent Verification of Correct Values
All corrected expected values were independently verified against three separate implementations:
1. **Linux `sha256sum`** command
2. **Python `hashlib` / `hmac`** module
3. **Windows .NET `SHA256.Create()`** cryptography API

All three implementations produced identical results, confirming the TLL implementation is correct.

### Sign Extension Fix (defensive)
During debugging, the message schedule code was updated to explicitly cast `uint8_t` to `uint32_t` before left-shifting:
```c
// Before:
m[i] = (data[j] << 24) | (data[j+1] << 16) | ...
// After:
m[i] = ((uint32_t)data[j] << 24) | ((uint32_t)data[j+1] << 16) | ...
```
This prevents potential sign-extension issues on platforms where `uint8_t` is promoted to signed `int` before shifting. The fix is defensive and does not change behavior on tested platforms.

## 4. Gate Test Results

### Test Suite: `tests/crypto/gate_hmac_sha256.tll`
- **Total tests**: 20
- **PASS**: 20
- **FAIL**: 0
- **Result**: ALL TESTS PASSED

### Test Sections
1. **SHA-256 Known Vectors (FIPS 180-4)** (4 tests)
   - SHA-256('abc') = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
   - SHA-256('') = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
   - SHA-256(56-byte) = 248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1
   - SHA-256(fox dog) = d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592

2. **HMAC-SHA256 RFC 4231 / Known Vectors** (4 tests)
   - RFC4231 TC2: HMAC('Jefe', 'what do ya want for nothing?') = 5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843
   - HMAC('key', fox dog) = f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8
   - HMAC('key', '') = 5d5d139563c95b5967b9bd9a8c9b233a9dedb45072794cd232dc1b74832607d0
   - HMAC('', '') = b613679a0814d9ec772f95d778c35fc5ff1697c493715653c6c712144292c5ad

3. **hmac.verify Constant-Time Verification** (3 tests)
   - verify correct HMAC returns true
   - verify wrong HMAC returns false
   - verify wrong key returns false

4. **Output Format Validation** (3 tests)
   - HMAC output length is 64 (hex)
   - SHA-256 output length is 64 (hex)
   - HMAC output is all lowercase hex

5. **Determinism** (2 tests)
   - HMAC is deterministic (same input = same output)
   - SHA-256 is deterministic (same input = same output)

6. **Different Inputs** (2 tests)
   - Different keys produce different HMAC
   - Different data produce different HMAC

7. **Long Key (>64 bytes) Hashing** (2 tests)
   - HMAC with 70-byte key produces 64-char output
   - Long key produces different HMAC than short key

## 5. Concurrency / Multi-thread Test Results

### Test Suite: `tests/crypto/gate_hmac_sha256_concurrent.tll`
- **Total tests**: 9
- **PASS**: 9
- **FAIL**: 0
- **Result**: ALL TESTS PASSED

### Test Sections
1. **Single-thread Baseline** (reference values established)
2. **Repeated Call Consistency** (2 tests) - 100 iterations of SHA-256 and HMAC, all consistent
3. **Sequential Different Messages** (4 tests) - No state leakage between calls, different messages produce different results
4. **Interleaved SHA-256 and HMAC Calls** (1 test) - 50 interleaved iterations, all consistent
5. **Multi-block Message Hashing** (2 tests) - 1000-byte message, deterministic SHA-256 and HMAC

## 6. Compiler Bootstrap

- **Old compiler**: tools/TLLC/tllc.tllbc (pre-P1-03)
- **New compiler**: tools/TLLC/tllc_hmac.tllbc (with hmac/sha256 module mapping)
- **New compiler size**: 659,295 bytes
- **Functions**: 171
- **Constants**: 3,864
- **Bootstrap**: New compiler compiled with old compiler, then verified by recompiling itself
- **Status**: Bootstrap successful

## 7. Three-Platform CI

**Status**: ALL GREEN ✅ (CI Run 33905434201, 47m 11s)

| Platform | OS | Compiler | Build | Gate Test | Concurrency Test |
|----------|-----|----------|-------|-----------|------------------|
| Linux | Ubuntu latest | gcc | ✅ PASS | ✅ 20/20 | ✅ 9/9 |
| macOS | macOS latest | clang/gcc | ✅ PASS | ✅ 20/20 | ✅ 9/9 |
| Windows | Windows latest | MSVC | ✅ PASS | ✅ 20/20 | N/A (no concurrency step on Windows) |

**CI Job IDs**:
- Linux: 101129130897
- macOS: 101129131246
- Windows: (completed, 3/3 jobs total)

### CI Build Commands
**Linux/macOS**:
```bash
gcc -O2 -std=gnu99 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE -D_DARWIN_C_SOURCE -o tllvm \
  main.c vm.c value.c json.c builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c sqlite3.c \
  -lm -lpthread -ldl
```

**Windows (MSVC)**:
```cmd
cl /O2 /D_CRT_SECURE_NO_WARNINGS /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c sqlite3.c ws2_32.lib winhttp.lib bcrypt.lib
```

### CI Test Steps Added
1. P1-03 HMAC-SHA256 Gate Test (Linux/macOS + Windows)
2. P1-03 HMAC-SHA256 Concurrency Test (Linux/macOS)

## 8. RFC 4231 Test Vector Coverage

### Currently Tested
- **TC2** (text key "Jefe", text data): PASS - full 256-bit output verified
- Additional known vectors (key="key", empty key/data, long key): PASS

### Not Yet Tested (binary key test cases)
RFC 4231 TC1, TC3, TC4, TC6, TC7 use binary keys (0x0b*20, 0xaa*20, 0x01-0x19, 0xaa*131) that require representation of arbitrary byte sequences in TLL strings. TLL currently does not support `\xNN` hex escapes or `\uNNNN` Unicode escapes for control characters. This is a known TLL language limitation that does not affect the correctness of the SHA-256/HMAC implementation.

**Plan**: Add binary string literal support to TLL (e.g., `\x0b` escape) in a future phase, then add complete RFC 4231 TC1/3/4/6/7 test cases.

## 9. Sign-off Checklist

| Item | Status | Evidence |
|------|--------|----------|
| SHA-256 implementation (FIPS 180-4) | PASS | 4 known vectors match sha256sum/Python/.NET |
| HMAC-SHA256 implementation (RFC 2104) | PASS | RFC4231 TC2 + 3 additional vectors verified |
| hmac.verify constant-time | PASS | 3 verification tests pass |
| Output format (64 hex, lowercase) | PASS | 3 format validation tests pass |
| Determinism | PASS | 2 determinism tests pass |
| Multi-block messages | PASS | 1000-byte message test pass |
| Long key (>64 bytes) | PASS | 70-byte key test pass |
| Concurrency / no state leakage | PASS | 9/9 concurrency tests pass |
| Compiler bootstrap | PASS | tllc_hmac.tllbc self-compiles |
| Linux build | ✅ PASS | CI Run 33905434201, job 101129130897 |
| macOS build | ✅ PASS | CI Run 33905434201, job 101129131246 |
| Windows build | ✅ PASS | CI Run 33905434201, 3/3 jobs completed |
| Git commit | ✅ DONE | commit d9b0412 (10 files, +974 lines) |
| CI Run ID | ✅ 33905434201 | 47m 11s, 3/3 jobs all green |
| Final SEAL | PENDING | Awaiting总指挥验收 |

## 10. Files Modified in This Phase

### TLL Compiler / Runtime
1. `host/c/hmac_builtin.c` (NEW) - SHA-256 + HMAC-SHA256 implementation
2. `host/c/tllvm.h` - Added hmac_builtin_invoke declaration
3. `host/c/builtin.c` - Added idx 190-199 dispatch
4. `compiler/codegen.tll` - Added hmac/sha256 module function mapping
5. `compiler/linker.tll` - Added "hmac", "sha256" to stdlibs
6. `host/c/Makefile` - Added hmac_builtin.c to SRCS

### CI
7. `.github/workflows/ci.yml` - Added hmac_builtin.c to build commands + HMAC test steps

### Tests
8. `tests/crypto/gate_hmac_sha256.tll` (NEW) - 20-test gate suite
9. `tests/crypto/gate_hmac_sha256_concurrent.tll` (NEW) - 9-test concurrency suite

### Documentation
10. `docs/P1-03-HMAC-SHA256-EVIDENCE.md` (NEW) - This document

---

**Current Status**: Implementation complete, 20/20 Gate tests PASS, 9/9 concurrency tests PASS, compiler bootstrap successful, three-platform CI ALL GREEN (Run 33905434201, commit d9b0412).

**Next Step**: Submit to总指挥 for final SEAL验收. After SEAL, proceed to P1-04 HTTP Client.
