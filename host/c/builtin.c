/* TLL Builtin functions - Host ABI + stdlib implementation for bootstrap VM.
 * Note: In the final architecture, json/math/strings/arrays/convert should be
 * implemented in TLL stdlib. This C implementation is for bootstrap only.
 */
#include "tllvm.h"
#include <time.h>
#include <sys/stat.h>
#include <errno.h>
#include <ctype.h>

#ifdef _WIN32
#include <windows.h>
/* WinINet is loaded dynamically to avoid compile-time dependency on wininet.h */
typedef void* HINTERNET_DYNA;
typedef HINTERNET_DYNA (__stdcall *InternetOpenA_t)(const char*, unsigned long, const char*, const char*, unsigned long);
typedef HINTERNET_DYNA (__stdcall *InternetOpenUrlA_t)(HINTERNET_DYNA, const char*, const char*, unsigned long, unsigned long, unsigned long);
typedef int (__stdcall *InternetReadFile_t)(HINTERNET_DYNA, void*, unsigned long, unsigned long*);
typedef int (__stdcall *InternetCloseHandle_t)(HINTERNET_DYNA);
typedef int (__stdcall *HttpQueryInfoA_t)(HINTERNET_DYNA, unsigned long, void*, unsigned long*, unsigned long*);
#ifndef INTERNET_OPEN_TYPE_PRECONFIG
#define INTERNET_OPEN_TYPE_PRECONFIG 0
#endif
#ifndef INTERNET_FLAG_RELOAD
#define INTERNET_FLAG_RELOAD 0x80000000
#endif
#ifndef INTERNET_FLAG_NO_CACHE_WRITE
#define INTERNET_FLAG_NO_CACHE_WRITE 0x04000000
#endif
#ifndef HTTP_QUERY_STATUS_CODE
#define HTTP_QUERY_STATUS_CODE 19
#endif
#else
#include <dirent.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <unistd.h>
#endif

/* === Helper: string operations === */
static char *str_dup(const char *s) { return s ? strdup(s) : strdup(""); }

static char *str_sub(const char *s, int start, int end) {
    int len = (int)strlen(s);
    if (start < 0) start = 0;
    if (end > len) end = len;
    if (start >= end) return strdup("");
    return tll_string_n(s + start, end - start).as.string;
}

/* === Builtin dispatch === */
TLLValue tll_call_builtin(TLLVM *vm, int idx, TLLValue *args, int argCount) {
    (void)vm;
    /* io (0-2) */
    if (idx == 0) { /* println */
        if (argCount > 0) { char *s = tll_to_string(args[0]); puts(s); free(s); }
        else puts("");
        return tll_null();
    }
    if (idx == 1) { /* print */
        if (argCount > 0) { char *s = tll_to_string(args[0]); fputs(s, stdout); free(s); }
        return tll_null();
    }
    if (idx == 2) { /* readLine */
        char buf[4096];
        if (argCount > 0) { char *s = tll_to_string(args[0]); fputs(s, stdout); free(s); }
        if (fgets(buf, sizeof(buf), stdin)) {
            int len = (int)strlen(buf);
            while (len > 0 && (buf[len-1] == '\n' || buf[len-1] == '\r')) buf[--len] = '\0';
            return tll_string(buf);
        }
        return tll_string("");
    }

    /* json (3-4) */
    if (idx == 3) { /* parse */
        if (argCount > 0 && args[0].type == TLL_STRING) {
            const char *p = args[0].as.string;
            return tll_parse_json(&p);
        }
        return tll_null();
    }
    if (idx == 4) { /* stringify */
        if (argCount > 0) {
            char *s = tll_to_json(args[0]);
            TLLValue r = tll_string(s);
            free(s);
            return r;
        }
        return tll_string("");
    }

    /* math (5-23) */
    if (idx >= 5 && idx <= 23) {
        double x = (argCount > 0) ? ((args[0].type==TLL_INT)?(double)args[0].as.integer:args[0].as.floating) : 0;
        double y = (argCount > 1) ? ((args[1].type==TLL_INT)?(double)args[1].as.integer:args[1].as.floating) : 0;
        switch (idx) {
            case 5: return tll_float(sqrt(x));
            case 6: return tll_float(fabs(x));
            case 7: return tll_float(floor(x));
            case 8: return tll_float(ceil(x));
            case 9: return tll_float(round(x));
            case 10: return tll_float(x < y ? x : y);
            case 11: return tll_float(x > y ? x : y);
            case 12: return tll_float(pow(x, y));
            case 13: return tll_float(sin(x));
            case 14: return tll_float(cos(x));
            case 15: return tll_float(tan(x));
            case 16: return tll_float(log(x));
            case 17: return tll_float(log(x) / log(2.0));
            case 18: return tll_float(log10(x));
            case 19: return tll_float(exp(x));
            case 20: return tll_float(3.14159265358979323846);
            case 21: return tll_float(2.71828182845904523536);
            case 22: return tll_float((double)rand() / RAND_MAX);
            case 23: {
                int mn = (int)x, mx = (int)y;
                return tll_int(mn + rand() % (mx - mn + 1));
            }
        }
    }

    /* strings (24-48) */
    if (idx >= 24 && idx <= 48) {
        const char *s = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        int slen = (int)strlen(s);
        switch (idx) {
            case 24: return tll_int(slen); /* length */
            case 25: { /* toUpper */
                char *r = strdup(s);
                for (int i = 0; r[i]; i++) r[i] = toupper((unsigned char)r[i]);
                return tll_string(r);
            }
            case 26: { /* toLower */
                char *r = strdup(s);
                for (int i = 0; r[i]; i++) r[i] = tolower((unsigned char)r[i]);
                return tll_string(r);
            }
            case 27: { /* trim */
                int start = 0, end = slen;
                while (start < end && isspace((unsigned char)s[start])) start++;
                while (end > start && isspace((unsigned char)s[end-1])) end--;
                return tll_string_n(s + start, end - start);
            }
            case 28: { /* trimStart */
                int start = 0;
                while (start < slen && isspace((unsigned char)s[start])) start++;
                return tll_string(s + start);
            }
            case 29: { /* trimEnd */
                int end = slen;
                while (end > 0 && isspace((unsigned char)s[end-1])) end--;
                return tll_string_n(s, end);
            }
            case 30: { /* split */
                const char *sep = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
                TLLValue arr = tll_array();
                if (strlen(sep) == 0) {
                    for (int i = 0; i < slen; i++) array_push(arr.as.array, tll_string_n(s+i, 1));
                } else {
                    int seplen = (int)strlen(sep);
                    const char *p = s;
                    while (1) {
                        const char *found = strstr(p, sep);
                        if (!found) { array_push(arr.as.array, tll_string(p)); break; }
                        array_push(arr.as.array, tll_string_n(p, (int)(found - p)));
                        p = found + seplen;
                    }
                }
                return arr;
            }
            case 31: { /* join */
                TLLValue arr = (argCount > 0 && args[0].type == TLL_ARRAY) ? args[0] : tll_array();
                const char *sep = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
                char *result = strdup("");
                for (int i = 0; i < arr.as.array->length; i++) {
                    if (i > 0) { char *t = result; result = malloc(strlen(t)+strlen(sep)+1); strcpy(result,t); strcat(result,sep); free(t); }
                    char *elem = tll_to_string(arr.as.array->items[i]);
                    char *t = result;
                    result = (char*)malloc(strlen(result) + strlen(elem) + 1);
                    strcpy(result, t); strcat(result, elem);
                    free(t); free(elem);
                }
                TLLValue r = tll_string(result);
                free(result);
                return r;
            }
            case 32: return tll_bool(strstr(s, (argCount>1)?args[1].as.string:"") != NULL); /* contains */
            case 33: { /* startsWith */
                const char *p = (argCount>1)?args[1].as.string:"";
                return tll_bool(strncmp(s, p, strlen(p)) == 0);
            }
            case 34: { /* endsWith */
                const char *p = (argCount>1)?args[1].as.string:"";
                int plen = (int)strlen(p);
                return tll_bool(slen >= plen && strcmp(s + slen - plen, p) == 0);
            }
            case 35: { /* substring */
                int start = (argCount>1 && args[1].type==TLL_INT)?(int)args[1].as.integer:0;
                int end = (argCount>2 && args[2].type==TLL_INT)?(int)args[2].as.integer:slen;
                return tll_string(str_sub(s, start, end));
            }
            case 36: { /* replace */
                const char *from = (argCount>1)?args[1].as.string:"";
                const char *to = (argCount>2)?args[2].as.string:"";
                /* Replace first occurrence */
                const char *found = strstr(s, from);
                if (!found) return tll_string(s);
                int pos = (int)(found - s);
                char *r = (char*)malloc(pos + strlen(to) + strlen(found + strlen(from)) + 1);
                memcpy(r, s, pos);
                strcpy(r + pos, to);
                strcat(r, found + strlen(from));
                TLLValue result = tll_string(r);
                free(r);
                return result;
            }
            case 37: { /* replaceAll */
                const char *from = (argCount>1)?args[1].as.string:"";
                const char *to = (argCount>2)?args[2].as.string:"";
                if (strlen(from) == 0) return tll_string(s);
                char *result = strdup("");
                const char *p = s;
                while (1) {
                    const char *found = strstr(p, from);
                    if (!found) { char *t=result; result=malloc(strlen(t)+strlen(p)+1); strcpy(result,t); strcat(result,p); free(t); break; }
                    int pos = (int)(found - p);
                    char *tmp = (char*)malloc(strlen(result) + pos + strlen(to) + 1);
                    strcpy(tmp, result);
                    strncat(tmp, p, pos);
                    strcat(tmp, to);
                    free(result); result = tmp;
                    p = found + strlen(from);
                }
                TLLValue r = tll_string(result);
                free(result);
                return r;
            }
            case 38: { /* repeat */
                int n = (argCount>1)?(int)args[1].as.integer:0;
                char *r = strdup("");
                for (int i = 0; i < n; i++) { char *t=r; r=malloc(strlen(t)+slen+1); strcpy(r,t); strcat(r,s); free(t); }
                TLLValue result = tll_string(r); free(r); return result;
            }
            case 39: { /* padStart */
                int len = (argCount>1)?(int)args[1].as.integer:slen;
                const char *pad = (argCount>2)?args[2].as.string:" ";
                if (slen >= len) return tll_string(s);
                int padlen = len - slen;
                char *r = (char*)malloc(len + 1);
                int padcharlen = (int)strlen(pad);
                for (int i = 0; i < padlen; i++) r[i] = pad[i % padcharlen];
                strcpy(r + padlen, s);
                TLLValue result = tll_string(r); free(r); return result;
            }
            case 40: { /* padEnd */
                int len = (argCount>1)?(int)args[1].as.integer:slen;
                const char *pad = (argCount>2)?args[2].as.string:" ";
                if (slen >= len) return tll_string(s);
                char *r = (char*)malloc(len + 1);
                strcpy(r, s);
                int padcharlen = (int)strlen(pad);
                for (int i = slen; i < len; i++) r[i] = pad[(i-slen) % padcharlen];
                r[len] = '\0';
                TLLValue result = tll_string(r); free(r); return result;
            }
            case 41: { /* charAt */
                int i = (argCount>1)?(int)args[1].as.integer:0;
                if (i < 0 || i >= slen) return tll_string("");
                return tll_string_n(s + i, 1);
            }
            case 42: { /* charCodeAt */
                int i = (argCount>1)?(int)args[1].as.integer:0;
                if (i < 0 || i >= slen) return tll_int(0);
                return tll_int((unsigned char)s[i]);
            }
            case 43: { /* indexOf */
                const char *sub = (argCount>1)?args[1].as.string:"";
                const char *found = strstr(s, sub);
                return tll_int(found ? (int)(found - s) : -1);
            }
            case 44: { /* lastIndexOf */
                const char *sub = (argCount>1)?args[1].as.string:"";
                int sublen = (int)strlen(sub);
                if (sublen == 0) return tll_int(slen);
                for (int i = slen - sublen; i >= 0; i--) {
                    if (strncmp(s + i, sub, sublen) == 0) return tll_int(i);
                }
                return tll_int(-1);
            }
            case 45: return tll_bool(slen == 0); /* isEmpty */
            case 46: { /* reverse */
                char *r = strdup(s);
                for (int i = 0, j = slen-1; i < j; i++, j--) { char t=r[i]; r[i]=r[j]; r[j]=t; }
                TLLValue result = tll_string(r); free(r); return result;
            }
            case 47: { /* lines */
                TLLValue arr = tll_array();
                const char *p = s;
                while (*p) {
                    const char *nl = strchr(p, '\n');
                    if (!nl) { array_push(arr.as.array, tll_string(p)); break; }
                    int len = (int)(nl - p);
                    if (len > 0 && p[len-1] == '\r') len--;
                    array_push(arr.as.array, tll_string_n(p, len));
                    p = nl + 1;
                }
                return arr;
            }
            case 48: { /* words */
                TLLValue arr = tll_array();
                const char *p = s;
                while (*p) {
                    while (*p && isspace((unsigned char)*p)) p++;
                    if (!*p) break;
                    const char *start = p;
                    while (*p && !isspace((unsigned char)*p)) p++;
                    array_push(arr.as.array, tll_string_n(start, (int)(p - start)));
                }
                return arr;
            }
        }
    }

    /* arrays (49-71) */
    if (idx >= 49 && idx <= 71) {
        TLLArray *arr = (argCount > 0 && args[0].type == TLL_ARRAY) ? args[0].as.array : NULL;
        switch (idx) {
            case 49: return tll_int(arr ? arr->length : 0); /* length */
            case 50: { /* get */
                int i = (argCount>1)?(int)args[1].as.integer:0;
                TLLValue v = arr ? array_get(arr, i) : tll_null();
                tll_value_incref(v);
                return v;
            }
            case 51: { /* push */
                if (arr) { for (int i = 1; i < argCount; i++) array_push(arr, args[i]); }
                return tll_int(arr ? arr->length : 0);
            }
            case 52: { /* pop */
                if (!arr || arr->length == 0) return tll_null();
                return arr->items[--arr->length];
            }
            case 53: { /* shift */
                if (!arr || arr->length == 0) return tll_null();
                TLLValue v = arr->items[0];
                memmove(arr->items, arr->items + 1, (arr->length - 1) * sizeof(TLLValue));
                arr->length--;
                return v;
            }
            case 54: { /* unshift */
                if (arr) {
                    int n = argCount - 1;
                    while (arr->length + n > arr->capacity) { arr->capacity *= 2; arr->items = realloc(arr->items, arr->capacity * sizeof(TLLValue)); }
                    memmove(arr->items + n, arr->items, arr->length * sizeof(TLLValue));
                    for (int i = 0; i < n; i++) arr->items[i] = args[n - i];
                    arr->length += n;
                }
                return tll_int(arr ? arr->length : 0);
            }
            case 55: { /* concat */
                TLLValue result = tll_array();
                if (arr) for (int i = 0; i < arr->length; i++) { tll_value_incref(arr->items[i]); array_push(result.as.array, arr->items[i]); }
                if (argCount > 1 && args[1].type == TLL_ARRAY) {
                    TLLArray *a2 = args[1].as.array;
                    for (int i = 0; i < a2->length; i++) { tll_value_incref(a2->items[i]); array_push(result.as.array, a2->items[i]); }
                }
                return result;
            }
            case 56: { /* slice */
                int start = (argCount>1)?(int)args[1].as.integer:0;
                int end = (argCount>2)?(int)args[2].as.integer:(arr?arr->length:0);
                TLLValue result = tll_array();
                if (arr) {
                    if (start < 0) start += arr->length;
                    if (end < 0) end += arr->length;
                    for (int i = start; i < end && i < arr->length; i++) { tll_value_incref(arr->items[i]); array_push(result.as.array, arr->items[i]); }
                }
                return result;
            }
            case 57: { /* includes */
                if (!arr) return tll_bool(0);
                for (int i = 0; i < arr->length; i++) if (tll_equals(arr->items[i], args[1])) return tll_bool(1);
                return tll_bool(0);
            }
            case 58: { /* indexOf */
                if (!arr) return tll_int(-1);
                for (int i = 0; i < arr->length; i++) if (tll_equals(arr->items[i], args[1])) return tll_int(i);
                return tll_int(-1);
            }
            case 59: { /* join */
                const char *sep = (argCount>1)?args[1].as.string:",";
                char *result = strdup("");
                if (arr) {
                    for (int i = 0; i < arr->length; i++) {
                        if (i > 0) { char *t=result; result=malloc(strlen(t)+strlen(sep)+1); strcpy(result,t); strcat(result,sep); free(t); }
                        char *elem = tll_to_string(arr->items[i]);
                        char *t = result;
                        result = malloc(strlen(result)+strlen(elem)+1);
                        strcpy(result,t); strcat(result,elem);
                        free(t); free(elem);
                    }
                }
                TLLValue r = tll_string(result); free(result); return r;
            }
            case 60: { /* reverse */
                if (arr) for (int i=0,j=arr->length-1; i<j; i++,j--) { TLLValue t=arr->items[i]; arr->items[i]=arr->items[j]; arr->items[j]=t; }
                return args[0];
            }
            case 61: /* sort - simple bubble sort */
                if (arr) {
                    for (int i = 0; i < arr->length-1; i++)
                        for (int j = 0; j < arr->length-1-i; j++) {
                            double a = (arr->items[j].type==TLL_INT)?(double)arr->items[j].as.integer:arr->items[j].as.floating;
                            double b = (arr->items[j+1].type==TLL_INT)?(double)arr->items[j+1].as.integer:arr->items[j+1].as.floating;
                            if (a > b) { TLLValue t=arr->items[j]; arr->items[j]=arr->items[j+1]; arr->items[j+1]=t; }
                        }
                }
                return args[0];
            case 62: { /* filter */
                TLLValue result = tll_array();
                if (arr && argCount > 1) {
                    for (int i = 0; i < arr->length; i++) {
                        TLLValue cbArgs[1] = {arr->items[i]};
                        TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 1);
                        if (tll_truthy(r)) {
                            tll_value_incref(arr->items[i]);
                            array_push(result.as.array, arr->items[i]);
                        }
                        tll_value_free(r);
                    }
                }
                return result;
            }
            case 63: { /* map */
                TLLValue result = tll_array();
                if (arr && argCount > 1) {
                    for (int i = 0; i < arr->length; i++) {
                        TLLValue cbArgs[1] = {arr->items[i]};
                        TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 1);
                        array_push(result.as.array, r);
                    }
                }
                return result;
            }
            case 64: { /* reduce */
                if (!arr || arr->length == 0) {
                    if (argCount > 2) { tll_value_incref(args[2]); return args[2]; }
                    return tll_null();
                }
                TLLValue acc;
                int start;
                if (argCount > 2) { tll_value_incref(args[2]); acc = args[2]; start = 0; }
                else { tll_value_incref(arr->items[0]); acc = arr->items[0]; start = 1; }
                for (int i = start; i < arr->length; i++) {
                    TLLValue cbArgs[2] = {acc, arr->items[i]};
                    TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 2);
                    tll_value_free(acc);
                    acc = r;
                }
                return acc;
            }
            case 65: { /* forEach */
                if (arr && argCount > 1) {
                    for (int i = 0; i < arr->length; i++) {
                        TLLValue cbArgs[1] = {arr->items[i]};
                        TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 1);
                        tll_value_free(r);
                    }
                }
                return tll_null();
            }
            case 66: { /* find */
                if (arr && argCount > 1) {
                    for (int i = 0; i < arr->length; i++) {
                        TLLValue cbArgs[1] = {arr->items[i]};
                        TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 1);
                        int found = tll_truthy(r);
                        tll_value_free(r);
                        if (found) { tll_value_incref(arr->items[i]); return arr->items[i]; }
                    }
                }
                return tll_null();
            }
            case 67: { /* some */
                if (arr && argCount > 1) {
                    for (int i = 0; i < arr->length; i++) {
                        TLLValue cbArgs[1] = {arr->items[i]};
                        TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 1);
                        int found = tll_truthy(r);
                        tll_value_free(r);
                        if (found) return tll_bool(1);
                    }
                }
                return tll_bool(0);
            }
            case 68: { /* every */
                if (arr && argCount > 1) {
                    for (int i = 0; i < arr->length; i++) {
                        TLLValue cbArgs[1] = {arr->items[i]};
                        TLLValue r = tll_vm_invoke(vm, args[1], cbArgs, 1);
                        int ok = tll_truthy(r);
                        tll_value_free(r);
                        if (!ok) return tll_bool(0);
                    }
                }
                return tll_bool(1);
            }
            case 69: { /* flat */
                TLLValue result = tll_array();
                int depth = (argCount>1)?(int)args[1].as.integer:1;
                if (arr) {
                    for (int i = 0; i < arr->length; i++) {
                        if (depth > 0 && arr->items[i].type == TLL_ARRAY) {
                            TLLArray *inner = arr->items[i].as.array;
                            for (int j = 0; j < inner->length; j++) {
                                tll_value_incref(inner->items[j]);
                                array_push(result.as.array, inner->items[j]);
                            }
                        } else {
                            tll_value_incref(arr->items[i]);
                            array_push(result.as.array, arr->items[i]);
                        }
                    }
                }
                return result;
            }
            case 70: { /* fill */
                TLLValue val = (argCount>1)?args[1]:tll_null();
                int start = (argCount>2)?(int)args[2].as.integer:0;
                int end = (argCount>3)?(int)args[3].as.integer:(arr?arr->length:0);
                if (arr) for (int i = start; i < end && i < arr->length; i++) {
                    tll_value_free(arr->items[i]);
                    tll_value_incref(val);
                    arr->items[i] = val;
                }
                tll_value_free(val); /* release parameter ownership */
                return args[0];
            }
            case 71: { /* range */
                int start = (argCount>0)?(int)args[0].as.integer:0;
                int end = (argCount>1)?(int)args[1].as.integer:0;
                int step = (argCount>2)?(int)args[2].as.integer:1;
                TLLValue result = tll_array();
                if (step > 0) { for (int i = start; i < end; i += step) array_push(result.as.array, tll_int(i)); }
                else if (step < 0) { for (int i = start; i > end; i += step) array_push(result.as.array, tll_int(i)); }
                return result;
            }
        }
    }

    /* convert (72-78) */
    if (idx >= 72 && idx <= 78) {
        TLLValue v = argCount > 0 ? args[0] : tll_null();
        switch (idx) {
            case 72: { /* toInt */
                if (v.type == TLL_INT) return v;
                if (v.type == TLL_FLOAT) return tll_int((long long)v.as.floating);
                if (v.type == TLL_STRING) return tll_int(atoll(v.as.string));
                if (v.type == TLL_BOOL) return tll_int(v.as.boolean ? 1 : 0);
                return tll_int(0);
            }
            case 73: { /* toFloat */
                if (v.type == TLL_FLOAT) return v;
                if (v.type == TLL_INT) return tll_float((double)v.as.integer);
                if (v.type == TLL_STRING) return tll_float(atof(v.as.string));
                if (v.type == TLL_BOOL) return tll_float(v.as.boolean ? 1.0 : 0.0);
                return tll_float(0.0);
            }
            case 74: { /* toString */
                char *s = tll_to_string(v);
                TLLValue r = tll_string(s);
                free(s);
                return r;
            }
            case 75: /* toBool */
                return tll_bool(tll_truthy(v));
            case 76: { /* toChar */
                int c = (v.type==TLL_INT)?(int)v.as.integer:0;
                char buf[2] = {(char)c, 0};
                return tll_string(buf);
            }
            case 77: { /* charCode */
                if (v.type == TLL_STRING && strlen(v.as.string) > 0) return tll_int((unsigned char)v.as.string[0]);
                return tll_int(0);
            }
            case 78: { /* typeOf */
                switch (v.type) {
                    case TLL_NULL: return tll_string("null");
                    case TLL_BOOL: return tll_string("bool");
                    case TLL_INT: return tll_string("int");
                    case TLL_FLOAT: return tll_string("float");
                    case TLL_STRING: return tll_string("string");
                    case TLL_ARRAY: return tll_string("array");
                    case TLL_MAP: return tll_string("map");
                    case TLL_FUNCTION: return tll_string("function");
                    case TLL_BUILTIN: return tll_string("builtin");
                    default: return tll_string("unknown");
                }
            }
        }
    }

    /* fs (79-90) */
    if (idx >= 79 && idx <= 90) {
        const char *path = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        switch (idx) {
            case 79: { /* readFile */
                FILE *f = fopen(path, "rb");
                if (!f) return tll_string("");
                fseek(f, 0, SEEK_END);
                long sz = ftell(f);
                fseek(f, 0, SEEK_SET);
                char *buf = (char*)malloc(sz + 1);
                fread(buf, 1, sz, f);
                buf[sz] = '\0';
                fclose(f);
                TLLValue r = tll_string(buf);
                free(buf);
                return r;
            }
            case 80: { /* writeFile */
                const char *content = (argCount>1)?args[1].as.string:"";
                FILE *f = fopen(path, "wb");
                if (f) { fputs(content, f); fclose(f); }
                return tll_null();
            }
            case 81: { /* appendFile */
                const char *content = (argCount>1)?args[1].as.string:"";
                FILE *f = fopen(path, "ab");
                if (f) { fputs(content, f); fclose(f); }
                return tll_null();
            }
            case 82: { /* exists */
                struct stat st;
                return tll_bool(stat(path, &st) == 0);
            }
            case 83: /* mkdir */
#ifdef _WIN32
                mkdir(path);
#else
                mkdir(path, 0755);
#endif
                return tll_null();
            case 84: /* remove */
                remove(path);
                return tll_null();
            case 85: { /* listDir */
                TLLValue arr = tll_array();
#ifdef _WIN32
                WIN32_FIND_DATAA fd;
                char pattern[4096];
                snprintf(pattern, sizeof(pattern), "%s\\*", path);
                HANDLE h = FindFirstFileA(pattern, &fd);
                if (h != INVALID_HANDLE_VALUE) {
                    do {
                        if (strcmp(fd.cFileName, ".") != 0 && strcmp(fd.cFileName, "..") != 0)
                            array_push(arr.as.array, tll_string(fd.cFileName));
                    } while (FindNextFileA(h, &fd));
                    FindClose(h);
                }
#else
                DIR *d = opendir(path);
                if (d) {
                    struct dirent *e;
                    while ((e = readdir(d))) {
                        if (strcmp(e->d_name, ".") != 0 && strcmp(e->d_name, "..") != 0)
                            array_push(arr.as.array, tll_string(e->d_name));
                    }
                    closedir(d);
                }
#endif
                return arr;
            }
            case 86: { /* isFile */
                struct stat st;
                return tll_bool(stat(path, &st) == 0 && S_ISREG(st.st_mode));
            }
            case 87: { /* isDir */
                struct stat st;
                return tll_bool(stat(path, &st) == 0 && S_ISDIR(st.st_mode));
            }
            case 88: { /* fileSize */
                struct stat st;
                if (stat(path, &st) == 0) return tll_int(st.st_size);
                return tll_int(0);
            }
            case 89: { /* copyFile */
                const char *dst = (argCount>1)?args[1].as.string:"";
                FILE *src = fopen(path, "rb");
                if (!src) return tll_null();
                FILE *out = fopen(dst, "wb");
                if (!out) { fclose(src); return tll_null(); }
                char buf[4096]; size_t n;
                while ((n = fread(buf, 1, sizeof(buf), src)) > 0) fwrite(buf, 1, n, out);
                fclose(src); fclose(out);
                return tll_null();
            }
            case 90: { /* rename */
                const char *dst = (argCount>1)?args[1].as.string:"";
                rename(path, dst);
                return tll_null();
            }
        }
    }

    /* http (91-97) - real implementation */
    if (idx >= 91 && idx <= 97) {
        if (idx == 91) { /* http.get(url) -> map{status, body, ok} */
            const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
            TLLValue result = tll_map();
            if (strlen(url) == 0) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("empty url"));
                return result;
            }
#ifdef _WIN32
            /* Dynamically load wininet.dll */
            HMODULE hWinInet = LoadLibraryA("wininet.dll");
            if (!hWinInet) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("wininet.dll not found"));
                return result;
            }
            InternetOpenA_t pInternetOpenA = (InternetOpenA_t)GetProcAddress(hWinInet, "InternetOpenA");
            InternetOpenUrlA_t pInternetOpenUrlA = (InternetOpenUrlA_t)GetProcAddress(hWinInet, "InternetOpenUrlA");
            InternetReadFile_t pInternetReadFile = (InternetReadFile_t)GetProcAddress(hWinInet, "InternetReadFile");
            InternetCloseHandle_t pInternetCloseHandle = (InternetCloseHandle_t)GetProcAddress(hWinInet, "InternetCloseHandle");
            HttpQueryInfoA_t pHttpQueryInfoA = (HttpQueryInfoA_t)GetProcAddress(hWinInet, "HttpQueryInfoA");
            if (!pInternetOpenA || !pInternetOpenUrlA || !pInternetReadFile || !pInternetCloseHandle || !pHttpQueryInfoA) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("wininet function lookup failed"));
                FreeLibrary(hWinInet);
                return result;
            }
            HINTERNET_DYNA hInternet = pInternetOpenA("tllvm/1.0", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
            if (!hInternet) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("InternetOpen failed"));
                FreeLibrary(hWinInet);
                return result;
            }
            HINTERNET_DYNA hUrl = pInternetOpenUrlA(hInternet, url, NULL, 0, INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_CACHE_WRITE, 0);
            if (!hUrl) {
                DWORD err = GetLastError();
                char errbuf[256];
                snprintf(errbuf, sizeof(errbuf), "InternetOpenUrl failed: %lu", err);
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string(errbuf));
                pInternetCloseHandle(hInternet);
                FreeLibrary(hWinInet);
                return result;
            }
            /* Get status code */
            char statusBuf[32] = {0};
            DWORD statusLen = sizeof(statusBuf);
            pHttpQueryInfoA(hUrl, HTTP_QUERY_STATUS_CODE, statusBuf, &statusLen, NULL);
            int statusCode = atoi(statusBuf);
            /* Read body */
            char *body = (char*)malloc(4096);
            int bodyCap = 4096, bodyLen = 0;
            char readBuf[4096];
            DWORD bytesRead = 0;
            while (pInternetReadFile(hUrl, readBuf, sizeof(readBuf), &bytesRead) && bytesRead > 0) {
                if (bodyLen + bytesRead > bodyCap) {
                    bodyCap = bodyCap * 2 + bytesRead;
                    body = (char*)realloc(body, bodyCap);
                }
                memcpy(body + bodyLen, readBuf, bytesRead);
                bodyLen += bytesRead;
            }
            body[bodyLen] = '\0';
            map_set(result.as.map, "ok", tll_bool(statusCode >= 200 && statusCode < 300));
            map_set(result.as.map, "status", tll_int(statusCode));
            map_set(result.as.map, "body", tll_string(body));
            free(body);
            pInternetCloseHandle(hUrl);
            pInternetCloseHandle(hInternet);
            FreeLibrary(hWinInet);
            return result;
#else
            /* Linux: simple HTTP/1.0 GET via raw socket */
            /* Parse URL: http://host:port/path */
            const char *p = url;
            if (strncmp(p, "http://", 7) == 0) p += 7;
            else if (strncmp(p, "https://", 8) == 0) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("https not supported on Linux (use http)"));
                return result;
            }
            char host[256] = {0};
            int port = 80;
            const char *pathStart = strchr(p, '/');
            const char *portStart = strchr(p, ':');
            if (portStart && (!pathStart || portStart < pathStart)) {
                int hostLen = (int)(portStart - p);
                if (hostLen > 255) hostLen = 255;
                memcpy(host, p, hostLen);
                port = atoi(portStart + 1);
            } else {
                int hostLen = pathStart ? (int)(pathStart - p) : (int)strlen(p);
                if (hostLen > 255) hostLen = 255;
                memcpy(host, p, hostLen);
            }
            const char *path = pathStart ? pathStart : "/";
            /* Resolve host */
            struct hostent *he = gethostbyname(host);
            if (!he) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("DNS resolution failed"));
                return result;
            }
            int sock = socket(AF_INET, SOCK_STREAM, 0);
            if (sock < 0) {
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("socket creation failed"));
                return result;
            }
            struct sockaddr_in serv_addr;
            memset(&serv_addr, 0, sizeof(serv_addr));
            serv_addr.sin_family = AF_INET;
            serv_addr.sin_port = htons(port);
            memcpy(&serv_addr.sin_addr.s_addr, he->h_addr_list[0], he->h_length);
            if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
                close(sock);
                map_set(result.as.map, "ok", tll_bool(0));
                map_set(result.as.map, "status", tll_int(0));
                map_set(result.as.map, "body", tll_string(""));
                map_set(result.as.map, "error", tll_string("connection failed"));
                return result;
            }
            char request[1024];
            snprintf(request, sizeof(request),
                "GET %s HTTP/1.0\r\nHost: %s\r\nUser-Agent: tllvm/1.0\r\nConnection: close\r\n\r\n",
                path, host);
            send(sock, request, strlen(request), 0);
            /* Read response */
            char *resp = (char*)malloc(65536);
            int respCap = 65536, respLen = 0;
            char rbuf[4096];
            int n;
            while ((n = recv(sock, rbuf, sizeof(rbuf), 0)) > 0) {
                if (respLen + n > respCap) {
                    respCap = respCap * 2 + n;
                    resp = (char*)realloc(resp, respCap);
                }
                memcpy(resp + respLen, rbuf, n);
                respLen += n;
            }
            resp[respLen] = '\0';
            close(sock);
            /* Parse status code */
            int statusCode = 0;
            const char *sp = strchr(resp, ' ');
            if (sp) statusCode = atoi(sp + 1);
            /* Find body (after \r\n\r\n) */
            const char *bodyStart = strstr(resp, "\r\n\r\n");
            char *bodyStr = bodyStart ? (char*)(bodyStart + 4) : resp;
            map_set(result.as.map, "ok", tll_bool(statusCode >= 200 && statusCode < 300));
            map_set(result.as.map, "status", tll_int(statusCode));
            map_set(result.as.map, "body", tll_string(bodyStr));
            free(resp);
            return result;
#endif
        }
        /* http.post / http.request / http.serve / http.encodeURI / http.decodeURI / http.parseJSON */
        if (idx == 92) { /* http.post(url, body) -> map */
            /* Simplified: reuse GET infrastructure not available; return stub with error */
            TLLValue r = tll_map();
            map_set(r.as.map, "ok", tll_bool(0));
            map_set(r.as.map, "status", tll_int(0));
            map_set(r.as.map, "body", tll_string(""));
            map_set(r.as.map, "error", tll_string("http.post not yet implemented"));
            return r;
        }
        if (idx == 93) { /* http.request(options) -> map */
            TLLValue r = tll_map();
            map_set(r.as.map, "ok", tll_bool(0));
            map_set(r.as.map, "status", tll_int(0));
            map_set(r.as.map, "body", tll_string(""));
            map_set(r.as.map, "error", tll_string("http.request not yet implemented"));
            return r;
        }
        if (idx == 94) { /* http.serve(addr, handler) */
            fprintf(stderr, "tllvm: http.serve not yet implemented\n");
            return tll_null();
        }
        if (idx == 95) { /* http.encodeURI(s) */
            const char *s = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
            char *out = (char*)malloc(strlen(s) * 3 + 1);
            int oi = 0;
            for (int i = 0; s[i]; i++) {
                unsigned char c = (unsigned char)s[i];
                if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                    (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') {
                    out[oi++] = c;
                } else {
                    oi += snprintf(out + oi, 4, "%%%02X", c);
                }
            }
            out[oi] = '\0';
            TLLValue r = tll_string(out);
            free(out);
            return r;
        }
        if (idx == 96) { /* http.decodeURI(s) */
            const char *s = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
            char *out = (char*)malloc(strlen(s) + 1);
            int oi = 0;
            for (int i = 0; s[i]; i++) {
                if (s[i] == '%' && s[i+1] && s[i+2]) {
                    char hex[3] = {s[i+1], s[i+2], 0};
                    out[oi++] = (char)strtol(hex, NULL, 16);
                    i += 2;
                } else if (s[i] == '+') {
                    out[oi++] = ' ';
                } else {
                    out[oi++] = s[i];
                }
            }
            out[oi] = '\0';
            TLLValue r = tll_string(out);
            free(out);
            return r;
        }
        if (idx == 97) { /* http.parseJSON(s) -> map */
            if (argCount > 0 && args[0].type == TLL_STRING) {
                const char *p = args[0].as.string;
                return tll_parse_json(&p);
            }
            return tll_null();
        }
    }

    /* agent/workflow (98-119) - deferred */
    if (idx >= 98 && idx <= 119) {
        fprintf(stderr, "tllvm: agent/workflow builtin %d not available\n", idx);
        return tll_null();
    }

    /* process (120+) - P0-2.2 */
    if (idx == 120) { /* process.exit(code) */
        int code = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 0;
        tll_exit_code = code;
        tll_should_exit = 1;
        return tll_null();
    }
    if (idx == 121) { /* process.argv -> array of strings */
        TLLValue arr = tll_array();
        for (int i = 0; i < tll_argc; i++) {
            array_push(arr.as.array, tll_string(tll_argv[i]));
        }
        return arr;
    }
    if (idx == 122) { /* process.env -> map of environment variables */
        TLLValue envMap = tll_map();
        extern char **environ;
        for (int i = 0; environ && environ[i]; i++) {
            const char *eq = strchr(environ[i], '=');
            if (eq && eq != environ[i]) {
                int klen = (int)(eq - environ[i]);
                char *key = (char*)malloc(klen + 1);
                memcpy(key, environ[i], klen);
                key[klen] = '\0';
#ifdef _WIN32
                /* Windows env vars are case-insensitive; normalize to uppercase */
                for (int j = 0; j < klen; j++) key[j] = (char)toupper((unsigned char)key[j]);
#endif
                map_set(envMap.as.map, key, tll_string(eq + 1));
                free(key);
            }
        }
        return envMap;
    }

    /* time (123-124) - P0-3 extension */
    if (idx == 123) { /* time.now() -> int (unix timestamp seconds) */
        return tll_int((long long)time(NULL));
    }
    if (idx == 124) { /* time.format(ts, fmt) -> string */
        long long ts = (argCount > 0 && args[0].type == TLL_INT) ? args[0].as.integer : 0;
        const char *fmt = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "%Y-%m-%d %H:%M:%S";
        time_t t = (time_t)ts;
        struct tm *tm_info = localtime(&t);
        if (!tm_info) return tll_string("");
        char buf[256];
        strftime(buf, sizeof(buf), fmt, tm_info);
        return tll_string(buf);
    }

    /* fs extensions (125) - P0-3 */
    if (idx == 125) { /* fs.mkdirAll(path) -> void (recursive mkdir) */
        const char *path = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        if (strlen(path) == 0) return tll_null();
        char *tmp = strdup(path);
        int len = (int)strlen(tmp);
        for (int i = 1; i < len; i++) {
            if (tmp[i] == '/' || tmp[i] == '\\') {
                tmp[i] = '\0';
#ifdef _WIN32
                mkdir(tmp);
#else
                mkdir(tmp, 0755);
#endif
                tmp[i] = (path[i] == '/') ? '/' : '\\';
            }
        }
#ifdef _WIN32
        mkdir(tmp);
#else
        mkdir(tmp, 0755);
#endif
        free(tmp);
        return tll_null();
    }

    fprintf(stderr, "tllvm: unknown builtin index %d\n", idx);
    return tll_null();
}
