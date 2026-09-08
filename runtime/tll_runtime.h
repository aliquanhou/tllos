/*
 * TLL Runtime Core - Shared Runtime Foundation
 *
 * 这是 TLL Bytecode VM 和 Native Target 共享的运行时核心。
 * 所有语言基础语义（值表示、引用计数、真值判断、算术、比较、IO）
 * 必须在此处统一定义，确保 Bytecode 和 Native 行为完全一致。
 *
 * 原则：不建立第二套 Runtime。Shared Runtime Core 是唯一的语义地基。
 *
 * *** Binary Compatibility Guarantee ***
 * 此文件中的 TLLValue/TLLArray/TLLMap/TLLClosureEnv/TLLUpvalue 定义
 * 必须与 host/c/tllvm.h 中的定义完全一致（字段顺序、类型、大小）。
 * 这是 Bytecode VM 和 Native Target 共享值表示的基础。
 * 任何修改必须同时更新两处。
 *
 * Phase 2-01-B.4 Shared Runtime Core Convergence
 * 第一阶段收敛范围：
 *   - TLLValue (null/bool/int/float/string/array/map/function/builtin/upvalue)
 *   - 值创建函数
 *   - 引用计数 (incref/free)
 *   - 真值判断 (truthy)
 *   - 相等判断 (equals)
 *   - 字符串转换 (to_string/to_json)
 *   - 算术运算 (add/sub/mul/div/mod)
 *   - 比较运算 (eq/neq/lt/gt/le/ge) - 返回 TLLValue(TLL_BOOL)
 *   - Array/Map 基本操作
 *   - 基础 IO (print/println)
 *   - 生命周期 (init/cleanup)
 *
 * 后续阶段收敛：完整内置函数、JSON 解析、协程、异常、模块系统等。
 */

#ifndef TLL_RUNTIME_H
#define TLL_RUNTIME_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* === TLL Value Types ===
 * 与 host/c/tllvm.h 完全一致
 */
typedef enum {
    TLL_NULL,
    TLL_BOOL,
    TLL_INT,
    TLL_FLOAT,
    TLL_STRING,
    TLL_ARRAY,
    TLL_MAP,
    TLL_FUNCTION,  /* {__fn:true, fnIdx, env} */
    TLL_BUILTIN,   /* {__builtin:true, idx} */
    TLL_UPVALUE    /* {value: TLLValue} */
} TLLType;

typedef struct TLLValue TLLValue;
typedef struct TLLArray TLLArray;
typedef struct TLLMap TLLMap;
typedef struct TLLMapEntry TLLMapEntry;
typedef struct TLLClosureEnv TLLClosureEnv;
typedef struct TLLUpvalue TLLUpvalue;

/* === TLLValue (tagged union) ===
 * 与 host/c/tllvm.h 完全一致（Binary Compatible）
 *
 * 注意：string 字段是 char*，指向 refCount header 后的数据部分。
 * refCount header 布局: [int refCount][char data...]
 * 通过 str_rc(s) = (int*)(s - sizeof(int)) 访问 refcount。
 */
struct TLLValue {
    TLLType type;
    union {
        int boolean;
        long long integer;
        double floating;
        char *string;
        TLLArray *array;
        TLLMap *map;
        struct { int fnIdx; TLLClosureEnv *env; } func;
        struct { int idx; } builtin;
        TLLUpvalue *upvalue;
    } as;
};

/* === TLLArray ===
 * 与 host/c/tllvm.h 完全一致
 */
struct TLLArray {
    TLLValue *items;
    int length;
    int capacity;
    int refCount;
};

/* === TLLMap (hash table with chaining) ===
 * 与 host/c/tllvm.h 完全一致
 */
struct TLLMapEntry {
    char *key;
    TLLValue value;
    TLLMapEntry *next;
};

struct TLLMap {
    TLLMapEntry **buckets;
    int bucketCount;
    int size;
    int refCount;
};

/* === TLLUpvalue (closure upvalue) ===
 * 与 host/c/tllvm.h 完全一致
 */
struct TLLUpvalue {
    TLLValue value;
    int refCount;
};

/* === TLLClosureEnv (closure environment) ===
 * 与 host/c/tllvm.h 完全一致
 */
struct TLLClosureEnv {
    TLLUpvalue **upvalues;
    int count;
    int capacity;
    int refCount;
};

/* === Value Creation === */
TLLValue tll_null(void);
TLLValue tll_bool(int b);
TLLValue tll_int(long long v);
TLLValue tll_float(double v);
TLLValue tll_string(const char *s);
TLLValue tll_string_n(const char *s, int len);
TLLValue tll_array(void);
TLLValue tll_map(void);
TLLValue tll_function(int fnIdx, TLLClosureEnv *env);
TLLValue tll_builtin(int idx);

/* === Reference Counting === */
void tll_value_incref(TLLValue v);
void tll_value_free(TLLValue v);

/* === Truth & Equality === */
int tll_truthy(TLLValue v);
int tll_equals(TLLValue a, TLLValue b);

/* === Assignment Ownership (P2-01-B11-R1-R2) ===
 * Ownership-safe assignment: retain new, release old, store.
 * Order: incref(new) FIRST, then free(old), to avoid use-after-free when x=x.
 * RHS is evaluated exactly once by the caller (passed as new_value).
 * Returns new_value for expression-context use.
 */
TLLValue tll_assign(TLLValue *target, TLLValue new_value);

/* === String Conversion === */
char *tll_to_string(TLLValue v);
char *tll_to_json(TLLValue v);

/* === Arithmetic Operations ===
 * 语义规则（与 TLL Bytecode VM 操作码行为一致）：
 *   - int + int = int
 *   - 任一操作数为 float = float
 *   - 字符串 + 字符串 = 字符串拼接
 *   - 除法始终返回 float
 *   - 取模仅支持 int
 *   - 类型错误返回 tll_null()
 */
TLLValue tll_add(TLLValue a, TLLValue b);
TLLValue tll_sub(TLLValue a, TLLValue b);
TLLValue tll_mul(TLLValue a, TLLValue b);
TLLValue tll_div(TLLValue a, TLLValue b);
TLLValue tll_mod(TLLValue a, TLLValue b);

/* === Comparison Operations ===
 * 返回 TLLValue(TLL_BOOL 类型)。
 * 注意：返回 TLLValue 而非 int，因为比较表达式的结果在 TLL 中是 bool 值，
 * 需要被 tll_truthy() 等函数正确处理。
 *
 * 语义规则：
 *   - int/float 可跨类型比较
 *   - 字符串按字典序比较
 *   - 其他类型仅支持 ==/!=（引用相等）
 *   - 不支持的比较返回 false
 */
TLLValue tll_eq(TLLValue a, TLLValue b);
TLLValue tll_neq(TLLValue a, TLLValue b);
TLLValue tll_lt(TLLValue a, TLLValue b);
TLLValue tll_gt(TLLValue a, TLLValue b);
TLLValue tll_le(TLLValue a, TLLValue b);
TLLValue tll_ge(TLLValue a, TLLValue b);

/* === Array/Map Operations (basic) === */
void array_push(TLLArray *arr, TLLValue v);
TLLValue array_get(TLLArray *arr, int idx);
void array_set(TLLArray *arr, int idx, TLLValue v);
void map_set(TLLMap *map, const char *key, TLLValue value);
TLLValue map_get(TLLMap *map, const char *key);
int map_has(TLLMap *map, const char *key);

/* === Basic IO === */
void tll_io_print(TLLValue v);
void tll_io_println(TLLValue v);

/* === Runtime Lifecycle === */
void tll_runtime_init(void);
void tll_runtime_cleanup(void);

#endif /* TLL_RUNTIME_H */
