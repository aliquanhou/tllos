/*
 * TLL Crypto Builtin Binding
 * Provides crypto.* builtin functions for TLL programs.
 *
 * Builtin index range: 160-179
 *   160: crypto.secureRandomHex(length)     -> string (hex)
 *   161: crypto.secureRandomBase64(length)  -> string (base64)
 *   162: crypto.secureRandomInt(min, max)    -> int
 *   163: crypto.uuid4()                       -> string
 *   164: crypto.randomHex(length)             -> string (non-secure, for non-security use only)
 *   165: crypto.secureRandomBytes(length)     -> array of ints (0-255)
 *   166: crypto.randomBytes(length)            -> array of ints (0-255) [formal API, secure]
 *
 * Security:
 *   - Windows: BCryptGenRandom (CNG)
 *   - Linux: getrandom() with GRND_NONBLOCK, fallback to /dev/urandom
 *   - NOT counter, NOT timestamp, NOT pseudo-random
 */

#include "tllvm.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#pragma comment(lib, "bcrypt.lib")

static int secure_random_bytes(unsigned char *buf, size_t len) {
    BCRYPT_ALG_HANDLE hAlg = NULL;
    NTSTATUS status = BCryptOpenAlgorithmProvider(&hAlg, BCRYPT_RNG_ALGORITHM, NULL, 0);
    if (status != 0) return -1;
    status = BCryptGenRandom(hAlg, buf, (ULONG)len, 0);
    BCryptCloseAlgorithmProvider(hAlg, 0);
    return (status == 0) ? 0 : -1;
}
#else
#include <unistd.h>
#include <fcntl.h>
#include <sys/syscall.h>
#include <errno.h>

#if defined(__linux__) && defined(SYS_getrandom)
static int secure_random_bytes(unsigned char *buf, size_t len) {
    size_t total = 0;
    while (total < len) {
        ssize_t n = syscall(SYS_getrandom, buf + total, len - total, 0);
        if (n < 0) {
            if (errno == EINTR) continue;
            /* fallback to /dev/urandom */
            break;
        }
        total += (size_t)n;
    }
    if (total == len) return 0;

    /* fallback: /dev/urandom */
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) return -1;
    size_t got = 0;
    while (got < len) {
        ssize_t n = read(fd, buf + got, len - got);
        if (n < 0) {
            if (errno == EINTR) continue;
            close(fd);
            return -1;
        }
        if (n == 0) { close(fd); return -1; }
        got += (size_t)n;
    }
    close(fd);
    return 0;
}
#else
static int secure_random_bytes(unsigned char *buf, size_t len) {
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) return -1;
    size_t got = 0;
    while (got < len) {
        ssize_t n = read(fd, buf + got, len - got);
        if (n < 0) {
            if (errno == EINTR) continue;
            close(fd);
            return -1;
        }
        if (n == 0) { close(fd); return -1; }
        got += (size_t)n;
    }
    close(fd);
    return 0;
}
#endif
#endif

/* Base64 encoding */
static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static char *base64_encode(const unsigned char *data, size_t len) {
    size_t out_len = 4 * ((len + 2) / 3);
    char *out = (char *)malloc(out_len + 1);
    if (!out) return NULL;
    size_t i, j;
    for (i = 0, j = 0; i < len; ) {
        uint32_t octet_a = i < len ? data[i++] : 0;
        uint32_t octet_b = i < len ? data[i++] : 0;
        uint32_t octet_c = i < len ? data[i++] : 0;
        uint32_t triple = (octet_a << 0x10) + (octet_b << 0x08) + octet_c;
        out[j++] = b64_table[(triple >> 3 * 6) & 0x3F];
        out[j++] = b64_table[(triple >> 2 * 6) & 0x3F];
        out[j++] = b64_table[(triple >> 1 * 6) & 0x3F];
        out[j++] = b64_table[(triple >> 0 * 6) & 0x3F];
    }
    for (i = 0; i < (3 - len % 3) % 3; i++) out[out_len - 1 - i] = '=';
    out[out_len] = '\0';
    return out;
}

/* Hex encoding */
static char *hex_encode(const unsigned char *data, size_t len) {
    char *out = (char *)malloc(len * 2 + 1);
    if (!out) return NULL;
    static const char hex[] = "0123456789abcdef";
    for (size_t i = 0; i < len; i++) {
        out[i * 2] = hex[(data[i] >> 4) & 0xF];
        out[i * 2 + 1] = hex[data[i] & 0xF];
    }
    out[len * 2] = '\0';
    return out;
}

/* Non-secure random (for non-security use only) */
static int g_prng_inited = 0;
static void prng_init(void) {
    if (!g_prng_inited) {
        unsigned char seed[8];
        if (secure_random_bytes(seed, 8) == 0) {
            uint64_t s = 0;
            for (int i = 0; i < 8; i++) s = (s << 8) | seed[i];
            srand((unsigned int)(s ^ (uint64_t)time(NULL)));
        } else {
            srand((unsigned int)time(NULL));
        }
        g_prng_inited = 1;
    }
}

TLLValue crypto_builtin_invoke(TLLVM *vm, int idx, TLLValue *args, int argCount) {
    (void)vm;
    TLLValue result = tll_null();

    switch (idx) {
        case 160: { /* crypto.secureRandomHex(length) -> hex string */
            int length = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 32;
            if (length < 1) length = 1;
            if (length > 65536) length = 65536;
            unsigned char *buf = (unsigned char *)malloc(length);
            if (!buf) { result = tll_string(""); break; }
            if (secure_random_bytes(buf, length) != 0) {
                free(buf);
                result = tll_string("");
                break;
            }
            char *hex = hex_encode(buf, length);
            free(buf);
            if (hex) {
                result = tll_string(hex);
                free(hex);
            } else {
                result = tll_string("");
            }
            break;
        }
        case 161: { /* crypto.secureRandomBase64(length) -> base64 string */
            int length = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 32;
            if (length < 1) length = 1;
            if (length > 65536) length = 65536;
            unsigned char *buf = (unsigned char *)malloc(length);
            if (!buf) { result = tll_string(""); break; }
            if (secure_random_bytes(buf, length) != 0) {
                free(buf);
                result = tll_string("");
                break;
            }
            char *b64 = base64_encode(buf, length);
            free(buf);
            if (b64) {
                result = tll_string(b64);
                free(b64);
            } else {
                result = tll_string("");
            }
            break;
        }
        case 162: { /* crypto.secureRandomInt(min, max) -> int [min, max] */
            long long minVal = (argCount > 0 && args[0].type == TLL_INT) ? args[0].as.integer : 0;
            long long maxVal = (argCount > 1 && args[1].type == TLL_INT) ? args[1].as.integer : 100;
            if (maxVal < minVal) { long long t = minVal; minVal = maxVal; maxVal = t; }
            unsigned long long range = (unsigned long long)(maxVal - minVal + 1);
            if (range == 0) { result = tll_int(minVal); break; }
            /* Rejection sampling to avoid modulo bias */
            unsigned long long limit = 0xFFFFFFFFFFFFFFFFULL - (0xFFFFFFFFFFFFFFFFULL % range);
            unsigned long long r;
            int attempts = 0;
            do {
                unsigned char buf[8];
                if (secure_random_bytes(buf, 8) != 0) {
                    /* CSPRNG failed - return 0 as error indicator, NEVER fallback to rand() */
                    result = tll_int(0);
                    goto done_int;
                }
                r = 0;
                for (int i = 0; i < 8; i++) r = (r << 8) | buf[i];
                attempts++;
            } while (r >= limit && attempts < 100);
            result = tll_int(minVal + (long long)(r % range));
            done_int:
            break;
        }
        case 163: { /* crypto.uuid4() -> UUID v4 string */
            unsigned char buf[16];
            if (secure_random_bytes(buf, 16) != 0) {
                result = tll_string("");
                break;
            }
            /* Set version 4 and variant 1 */
            buf[6] = (buf[6] & 0x0F) | 0x40;
            buf[8] = (buf[8] & 0x3F) | 0x80;
            char uuid[37];
            snprintf(uuid, sizeof(uuid),
                "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
                buf[0], buf[1], buf[2], buf[3],
                buf[4], buf[5], buf[6], buf[7],
                buf[8], buf[9], buf[10], buf[11],
                buf[12], buf[13], buf[14], buf[15]);
            result = tll_string(uuid);
            break;
        }
        case 164: { /* crypto.randomHex(length) -> non-secure random hex */
            int length = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 32;
            if (length < 1) length = 1;
            if (length > 65536) length = 65536;
            prng_init();
            unsigned char *buf = (unsigned char *)malloc(length);
            if (!buf) { result = tll_string(""); break; }
            for (int i = 0; i < length; i++) buf[i] = (unsigned char)(rand() & 0xFF);
            char *hex = hex_encode(buf, length);
            free(buf);
            if (hex) {
                result = tll_string(hex);
                free(hex);
            } else {
                result = tll_string("");
            }
            break;
        }
        case 165: { /* crypto.secureRandomBytes(length) -> array of ints (0-255) */
            int length = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 32;
            if (length < 1) length = 1;
            if (length > 65536) length = 65536;
            unsigned char *buf = (unsigned char *)malloc(length);
            TLLValue arr = tll_array();
            if (!buf) { result = arr; break; }
            if (secure_random_bytes(buf, length) != 0) {
                free(buf);
                result = arr;
                break;
            }
            for (int i = 0; i < length; i++) {
                array_push(arr.as.array, tll_int(buf[i]));
            }
            free(buf);
            result = arr;
            break;
        }
        case 166: { /* crypto.randomBytes(length) -> array of ints (0-255) [formal secure API] */
            int length = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 32;
            if (length < 0) length = 0;
            if (length > 65536) length = 65536;
            if (length == 0) { result = tll_array(); break; }
            unsigned char *buf = (unsigned char *)malloc(length);
            TLLValue arr = tll_array();
            if (!buf) { result = arr; break; }
            if (secure_random_bytes(buf, length) != 0) {
                free(buf);
                result = arr;
                break;
            }
            for (int i = 0; i < length; i++) {
                array_push(arr.as.array, tll_int(buf[i]));
            }
            free(buf);
            result = arr;
            break;
        }
        default:
            fprintf(stderr, "tll crypto: unknown builtin index %d\n", idx);
            result = tll_null();
            break;
    }
    return result;
}
