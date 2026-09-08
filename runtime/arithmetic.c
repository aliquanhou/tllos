/*
 * TLL Runtime Core - Arithmetic & Comparison
 *
 * Shared Runtime Core 的算术和比较运算实现。
 * 这些是语言基础语义，Bytecode VM 和 Native Target 必须行为完全一致。
 *
 * 语义规则（与 TLL Bytecode VM 操作码行为一致）：
 *   - int + int = int
 *   - 任一操作数为 float = float
 *   - 字符串 + 字符串 = 字符串拼接
 *   - 除法始终返回 float（即使两个 int 相除）
 *   - 取模仅支持 int
 *   - 比较返回 TLL_BOOL
 *   - int/float 可跨类型比较
 *   - 字符串按字典序比较
 *
 * Phase 2-01-B.4 Shared Runtime Core Convergence
 */

#include "tll_runtime.h"

/* === Arithmetic Operations === */

TLLValue tll_add(TLLValue a, TLLValue b) {
    /* String concatenation */
    if (a.type == TLL_STRING && b.type == TLL_STRING) {
        int lenA = (int)strlen(a.as.string);
        int lenB = (int)strlen(b.as.string);
        char *result = (char*)malloc(lenA + lenB + 1);
        memcpy(result, a.as.string, lenA);
        memcpy(result + lenA, b.as.string, lenB);
        result[lenA + lenB] = '\0';
        TLLValue v = tll_string(result);
        free(result);
        return v;
    }
    /* Float promotion */
    if (a.type == TLL_FLOAT || b.type == TLL_FLOAT) {
        double da = (a.type == TLL_INT) ? (double)a.as.integer : a.as.floating;
        double db = (b.type == TLL_INT) ? (double)b.as.integer : b.as.floating;
        return tll_float(da + db);
    }
    /* Int addition */
    if (a.type == TLL_INT && b.type == TLL_INT) {
        return tll_int(a.as.integer + b.as.integer);
    }
    /* Fallback: return null (type error) */
    return tll_null();
}

TLLValue tll_sub(TLLValue a, TLLValue b) {
    if (a.type == TLL_FLOAT || b.type == TLL_FLOAT) {
        double da = (a.type == TLL_INT) ? (double)a.as.integer : a.as.floating;
        double db = (b.type == TLL_INT) ? (double)b.as.integer : b.as.floating;
        return tll_float(da - db);
    }
    if (a.type == TLL_INT && b.type == TLL_INT) {
        return tll_int(a.as.integer - b.as.integer);
    }
    return tll_null();
}

TLLValue tll_mul(TLLValue a, TLLValue b) {
    if (a.type == TLL_FLOAT || b.type == TLL_FLOAT) {
        double da = (a.type == TLL_INT) ? (double)a.as.integer : a.as.floating;
        double db = (b.type == TLL_INT) ? (double)b.as.integer : b.as.floating;
        return tll_float(da * db);
    }
    if (a.type == TLL_INT && b.type == TLL_INT) {
        return tll_int(a.as.integer * b.as.integer);
    }
    return tll_null();
}

TLLValue tll_div(TLLValue a, TLLValue b) {
    /* Division always returns float (TLL semantic) */
    double da = (a.type == TLL_INT) ? (double)a.as.integer : a.as.floating;
    double db = (b.type == TLL_INT) ? (double)b.as.integer : b.as.floating;
    if (db == 0.0) return tll_null(); /* division by zero -> null */
    return tll_float(da / db);
}

TLLValue tll_mod(TLLValue a, TLLValue b) {
    /* Modulo only supports int */
    if (a.type == TLL_INT && b.type == TLL_INT) {
        if (b.as.integer == 0) return tll_null();
        return tll_int(a.as.integer % b.as.integer);
    }
    return tll_null();
}

/* === Comparison Operations === */

TLLValue tll_eq(TLLValue a, TLLValue b) {
    return tll_bool(tll_equals(a, b));
}

TLLValue tll_neq(TLLValue a, TLLValue b) {
    return tll_bool(!tll_equals(a, b));
}

static int compare_numeric(TLLValue a, TLLValue b) {
    double da = (a.type == TLL_INT) ? (double)a.as.integer : a.as.floating;
    double db = (b.type == TLL_INT) ? (double)b.as.integer : b.as.floating;
    if (da < db) return -1;
    if (da > db) return 1;
    return 0;
}

TLLValue tll_lt(TLLValue a, TLLValue b) {
    /* Numeric comparison (int/float cross-type) */
    if ((a.type == TLL_INT || a.type == TLL_FLOAT) &&
        (b.type == TLL_INT || b.type == TLL_FLOAT)) {
        return tll_bool(compare_numeric(a, b) < 0);
    }
    /* String comparison */
    if (a.type == TLL_STRING && b.type == TLL_STRING) {
        return tll_bool(strcmp(a.as.string, b.as.string) < 0);
    }
    return tll_bool(0);
}

TLLValue tll_gt(TLLValue a, TLLValue b) {
    if ((a.type == TLL_INT || a.type == TLL_FLOAT) &&
        (b.type == TLL_INT || b.type == TLL_FLOAT)) {
        return tll_bool(compare_numeric(a, b) > 0);
    }
    if (a.type == TLL_STRING && b.type == TLL_STRING) {
        return tll_bool(strcmp(a.as.string, b.as.string) > 0);
    }
    return tll_bool(0);
}

TLLValue tll_le(TLLValue a, TLLValue b) {
    if ((a.type == TLL_INT || a.type == TLL_FLOAT) &&
        (b.type == TLL_INT || b.type == TLL_FLOAT)) {
        return tll_bool(compare_numeric(a, b) <= 0);
    }
    if (a.type == TLL_STRING && b.type == TLL_STRING) {
        return tll_bool(strcmp(a.as.string, b.as.string) <= 0);
    }
    return tll_bool(0);
}

TLLValue tll_ge(TLLValue a, TLLValue b) {
    if ((a.type == TLL_INT || a.type == TLL_FLOAT) &&
        (b.type == TLL_INT || b.type == TLL_FLOAT)) {
        return tll_bool(compare_numeric(a, b) >= 0);
    }
    if (a.type == TLL_STRING && b.type == TLL_STRING) {
        return tll_bool(strcmp(a.as.string, b.as.string) >= 0);
    }
    return tll_bool(0);
}
