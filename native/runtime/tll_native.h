/*
 * TLL Native Runtime - Native Target Entry Point
 *
 * 这是 TLL Native Target 的运行时入口头文件。
 * Native Target 生成的 C 代码包含此头文件，链接 Shared Runtime Core。
 *
 * *** Architecture Decision (P2-01-B.4) ***
 * Native Runtime 不再是独立的第二套 Runtime。
 * 它现在是 Shared Runtime Core 的 Native 执行入口。
 *
 *   TLL Source
 *       ↓ TLL Compiler (Native Target: native_lower.tll)
 *   C Source (calls Shared Runtime Core functions)
 *       ↓ MSVC / GCC / Clang
 *   Native Executable
 *       ↓ links
 *   Shared TLL Runtime Core (runtime/tll_runtime.h + value.c + arithmetic.c + io.c)
 *       ↓
 *   OS / Hardware
 *
 * 所有值语义、引用计数、算术、比较、IO 都由 Shared Runtime Core 统一定义，
 * 确保 Bytecode VM 和 Native Target 行为完全一致。
 *
 * Phase 2-01-B.4 Shared Runtime Core Convergence
 */

#ifndef TLL_NATIVE_H
#define TLL_NATIVE_H

/* Include Shared Runtime Core - the single source of truth for TLL value semantics */
#include "../../runtime/tll_runtime.h"

/*
 * 注意：此文件不再重复定义 TLLValue、TLLArray、TLLMap 等数据结构，
 * 也不再重复声明值创建、引用计数、算术、比较、IO 等函数。
 * 所有这些都来自 Shared Runtime Core (runtime/tll_runtime.h)。
 *
 * 此文件保留为 Native Target 的入口头文件，未来可在此添加
 * Native Target 特有的声明（如平台特定的初始化、Native ABI 等）。
 */

/* === Native Runtime Lifecycle (compatibility wrappers) ===
 * 为了保持与现有 native_lower.tll 生成代码的兼容性，
 * 保留 tll_native_init/tll_native_cleanup 作为 tll_runtime_init/tll_runtime_cleanup 的别名。
 */
void tll_native_init(void);
void tll_native_cleanup(void);

#endif /* TLL_NATIVE_H */
