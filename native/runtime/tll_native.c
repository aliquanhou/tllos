/*
 * TLL Native Runtime - Native Target Entry Point
 *
 * *** Architecture Decision (P2-01-B.4) ***
 * 此文件不再包含独立的 TLL Runtime 实现。
 * 所有值语义、引用计数、算术、比较、IO 都由 Shared Runtime Core 统一实现：
 *   - runtime/value.c      (值创建、引用计数、truthy、equals、to_string、Array/Map)
 *   - runtime/arithmetic.c (算术运算、比较运算)
 *   - runtime/io.c         (基础 IO、运行时生命周期)
 *
 * 此文件仅保留 Native Target 特有的生命周期包装函数，
 * 作为与现有 native_lower.tll 生成代码的兼容层。
 *
 * 原则：不建立第二套 Runtime。Shared Runtime Core 是唯一的语义地基。
 *
 * Phase 2-01-B.4 Shared Runtime Core Convergence
 */

#include "tll_native.h"

/* === Native Runtime Lifecycle (compatibility wrappers) ===
 * 委托给 Shared Runtime Core 的 tll_runtime_init/tll_runtime_cleanup。
 * 保留 tll_native_init/tll_native_cleanup 名称是为了与
 * 现有 native_lower.tll 生成的 C 代码保持兼容。
 */

void tll_native_init(void) {
    tll_runtime_init();
}

void tll_native_cleanup(void) {
    tll_runtime_cleanup();
}
