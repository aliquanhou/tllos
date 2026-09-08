/*
 * TLL Runtime Core - Basic IO & Lifecycle
 *
 * Shared Runtime Core 的基础 IO 和运行时生命周期实现。
 *
 * 注意：这是最基础的 IO（print/println），直接使用 C 标准库。
 * 更高级的 IO（文件、网络、异步 IO）属于后续阶段，不在第一阶段收敛范围。
 *
 * Phase 2-01-B.4 Shared Runtime Core Convergence
 */

#include "tll_runtime.h"

/* === Basic IO === */

void tll_io_print(TLLValue v) {
    char *s = tll_to_string(v);
    if (s) {
        printf("%s", s);
        free(s);
    }
}

void tll_io_println(TLLValue v) {
    char *s = tll_to_string(v);
    if (s) {
        printf("%s\n", s);
        free(s);
    } else {
        printf("\n");
    }
}

/* === Runtime Lifecycle === */

void tll_runtime_init(void) {
    /* First-stage: no global state needed for basic value system */
    /* Future: RNG seed, memory pool, module registry, etc. */
}

void tll_runtime_cleanup(void) {
    /* First-stage: no global state cleanup needed */
    /* Future: flush buffers, close resources, finalize memory pool, etc. */
}
