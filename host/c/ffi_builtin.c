/*
 * ffi_builtin.c - TLL FFI (Foreign Function Interface) builtin functions
 *
 * Phase 5: TLL Native Interop Foundation / FFI v0
 *
 * Supports:
 *   - ffi.load(path) -> library handle
 *   - ffi.symbol(handle, name) -> function pointer
 *   - ffi.call(ptr, retType, argTypes, args) -> result
 *
 * Type support (v0):
 *   Return: void, int32, int64, pointer, cstring
 *   Args:   int32, int64, pointer, cstring (max 4 args)
 *
 * Known GAP: float64 args/return require XMM register handling (future)
 * Known GAP: struct/union/callback (future)
 *
 * Platform abstraction:
 *   Windows: LoadLibraryA / GetProcAddress / FreeLibrary
 *   Linux/macOS: dlopen / dlsym / dlclose
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "tllvm.h"

#ifdef _WIN32
#include <windows.h>
typedef HMODULE native_lib_t;
typedef FARPROC native_sym_t;
#else
#include <dlfcn.h>
typedef void* native_lib_t;
typedef void* native_sym_t;
#endif

/* === Type constants (must match TLL side) === */
#define FFI_VOID     0
#define FFI_INT32    1
#define FFI_INT64    2
#define FFI_UINT32   3
#define FFI_UINT64   4
#define FFI_FLOAT64  5
#define FFI_POINTER  6
#define FFI_CSTRING  7

/* === Platform abstraction === */

static native_lib_t ffi_platform_load(const char *path, char *errbuf, size_t errlen) {
#ifdef _WIN32
    HMODULE h = LoadLibraryA(path);
    if (!h) {
        snprintf(errbuf, errlen, "LoadLibrary failed: error %lu", GetLastError());
    }
    return h;
#else
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        snprintf(errbuf, errlen, "dlopen failed: %s", dlerror());
    }
    return h;
#endif
}

static native_sym_t ffi_platform_symbol(native_lib_t lib, const char *name, char *errbuf, size_t errlen) {
#ifdef _WIN32
    FARPROC p = GetProcAddress(lib, name);
    if (!p) {
        snprintf(errbuf, errlen, "GetProcAddress failed: error %lu", GetLastError());
    }
    return p;
#else
    void *p = dlsym(lib, name);
    if (!p) {
        snprintf(errbuf, errlen, "dlsym failed: %s", dlerror());
    }
    return p;
#endif
}

/* === Function call thunks (integer-class args only, v0) === */
/* All integer-class types (int32, int64, uint32, uint64, pointer, cstring)
 * are passed in general-purpose registers on x64, so we can use int64_t
 * as a universal carrier. */

typedef int64_t (*ffi_fn_0)(void);
typedef int64_t (*ffi_fn_1)(int64_t);
typedef int64_t (*ffi_fn_2)(int64_t, int64_t);
typedef int64_t (*ffi_fn_3)(int64_t, int64_t, int64_t);
typedef int64_t (*ffi_fn_4)(int64_t, int64_t, int64_t, int64_t);

/* Convert TLL value to int64 arg based on type tag */
static int64_t ffi_value_to_int(TLLValue v, int type) {
    switch (type) {
        case FFI_INT32:
        case FFI_UINT32:
            return (int64_t)(int32_t)v.as.integer;
        case FFI_INT64:
        case FFI_UINT64:
        case FFI_POINTER:
            return v.as.integer;
        case FFI_CSTRING:
            return (int64_t)(intptr_t)v.as.string;
        case FFI_FLOAT64:
            /* GAP: float64 arg not supported in v0 */
            return 0;
        default:
            return 0;
    }
}

/* Convert int64 result to TLL value based on return type */
static TLLValue ffi_int_to_value(int64_t result, int retType) {
    switch (retType) {
        case FFI_VOID:
            return tll_null();
        case FFI_INT32:
            return tll_int((int32_t)result);
        case FFI_UINT32:
            return tll_int((uint32_t)result);
        case FFI_INT64:
        case FFI_UINT64:
        case FFI_POINTER:
            return tll_int(result);
        case FFI_CSTRING:
            if ((void*)(intptr_t)result == NULL) {
                return tll_null();
            }
            return tll_string((const char*)(intptr_t)result);
        case FFI_FLOAT64:
            /* GAP: float64 return not supported in v0 */
            return tll_int(0);
        default:
            return tll_null();
    }
}

/* === Builtin implementations === */

/* ffi.load(path) -> handle (int64) or null on failure */
TLLValue builtin_ffi_load(TLLVM *vm, TLLValue *args, int argCount) {
    (void)vm;
    if (argCount < 1 || args[0].type != TLL_STRING) {
        return tll_null();
    }
    const char *path = args[0].as.string;
    char errbuf[512] = {0};
    native_lib_t lib = ffi_platform_load(path, errbuf, sizeof(errbuf));
    if (!lib) {
        /* Store error in a global for ffi.error() - simple approach: print to stderr */
        fprintf(stderr, "ffi.load error: %s\n", errbuf);
        return tll_int(0);
    }
    return tll_int((int64_t)(intptr_t)lib);
}

/* ffi.symbol(handle, name) -> pointer (int64) or null on failure */
TLLValue builtin_ffi_symbol(TLLVM *vm, TLLValue *args, int argCount) {
    (void)vm;
    if (argCount < 2 || args[0].type != TLL_INT || args[1].type != TLL_STRING) {
        return tll_null();
    }
    native_lib_t lib = (native_lib_t)(intptr_t)args[0].as.integer;
    const char *name = args[1].as.string;
    char errbuf[512] = {0};
    native_sym_t sym = ffi_platform_symbol(lib, name, errbuf, sizeof(errbuf));
    if (!sym) {
        fprintf(stderr, "ffi.symbol error: %s\n", errbuf);
        return tll_int(0);
    }
    return tll_int((int64_t)(intptr_t)sym);
}

/* ffi.call(pointer, retType, argTypes_array, args_array) -> result */
TLLValue builtin_ffi_call(TLLVM *vm, TLLValue *args, int argCount) {
    (void)vm;
    if (argCount < 4) {
        return tll_null();
    }
    if (args[0].type != TLL_INT) return tll_null();
    if (args[1].type != TLL_INT) return tll_null();
    if (args[2].type != TLL_ARRAY) return tll_null();
    if (args[3].type != TLL_ARRAY) return tll_null();

    void *fnPtr = (void*)(intptr_t)args[0].as.integer;
    int retType = (int)args[1].as.integer;
    TLLArray *argTypes = args[2].as.array;
    TLLArray *argVals = args[3].as.array;

    int nArgs = argTypes->length;
    if (nArgs > 4) {
        fprintf(stderr, "ffi.call error: max 4 args supported in v0\n");
        return tll_null();
    }
    if (argVals->length < nArgs) {
        fprintf(stderr, "ffi.call error: arg count mismatch\n");
        return tll_null();
    }

    /* Convert args to int64 */
    int64_t iargs[4] = {0, 0, 0, 0};
    for (int i = 0; i < nArgs; i++) {
        int atype = (int)argTypes->items[i].as.integer;
        iargs[i] = ffi_value_to_int(argVals->items[i], atype);
    }

    /* Call based on arg count */
    int64_t result = 0;
    switch (nArgs) {
        case 0:
            result = ((ffi_fn_0)fnPtr)();
            break;
        case 1:
            result = ((ffi_fn_1)fnPtr)(iargs[0]);
            break;
        case 2:
            result = ((ffi_fn_2)fnPtr)(iargs[0], iargs[1]);
            break;
        case 3:
            result = ((ffi_fn_3)fnPtr)(iargs[0], iargs[1], iargs[2]);
            break;
        case 4:
            result = ((ffi_fn_4)fnPtr)(iargs[0], iargs[1], iargs[2], iargs[3]);
            break;
    }

    return ffi_int_to_value(result, retType);
}

/* ffi.cstring(string) -> pointer (int64) - returns pointer to TLL string's internal buffer */
TLLValue builtin_ffi_cstring(TLLVM *vm, TLLValue *args, int argCount) {
    (void)vm;
    if (argCount < 1 || args[0].type != TLL_STRING) {
        return tll_null();
    }
    /* WARNING: pointer is to TLL-managed memory; must not be freed by C code,
     * and must not be used after the TLL string is garbage collected. */
    return tll_int((int64_t)(intptr_t)args[0].as.string);
}

/* ffi.string(pointer) -> TLL string - copies C string into TLL-managed memory */
TLLValue builtin_ffi_string(TLLVM *vm, TLLValue *args, int argCount) {
    (void)vm;
    if (argCount < 1 || args[0].type != TLL_INT) {
        return tll_null();
    }
    const char *cstr = (const char*)(intptr_t)args[0].as.integer;
    if (cstr == NULL) {
        return tll_null();
    }
    return tll_string(cstr);
}


/* === FFI builtin dispatcher (index range 210-219) === */

TLLValue ffi_builtin_invoke(TLLVM *vm, int idx, TLLValue *args, int argCount) {
    switch (idx) {
        case 210: return builtin_ffi_load(vm, args, argCount);
        case 211: return builtin_ffi_symbol(vm, args, argCount);
        case 212: return builtin_ffi_call(vm, args, argCount);
        case 213: return builtin_ffi_cstring(vm, args, argCount);
        case 214: return builtin_ffi_string(vm, args, argCount);
        default:
            fprintf(stderr, "ffi_builtin_invoke: unknown idx %d\n", idx);
            return tll_null();
    }
}


