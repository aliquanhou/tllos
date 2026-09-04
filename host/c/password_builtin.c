/*
 * TLL Password Hashing Builtin Binding
 * Provides password.* builtin functions for TLL programs.
 *
 * Embeds bcrypt implementation based on OpenBSD bcrypt.c (Public Domain).
 *
 * Builtin index range: 180-189
 *   180: password.hash(password)           -> bcrypt hash string (cost=12)
 *   181: password.hashWithCost(password, cost) -> bcrypt hash string
 *   182: password.verify(password, hash)   -> bool
 *   183: password.needsRehash(hash, minCost) -> bool
 *   184: password.hashInfo(hash)           -> map {algorithm, cost, valid}
 *
 * Security notes:
 * - Uses bcrypt ($2b$) with configurable cost (4-31)
 * - Default cost = 12 (~250ms on modern hardware)
 * - Salt is 16 bytes from OS CSPRNG (crypto.randomBytes)
 * - Constant-time comparison for password verification
 * - Does NOT invent cryptography: uses well-established bcrypt algorithm
 */

#include "tllvm.h"
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/* === OS CSPRNG for salt generation === */
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
static int password_get_random(uint8_t *buf, int len) {
    BCRYPT_ALG_HANDLE hAlg = NULL;
    NTSTATUS status = BCryptOpenAlgorithmProvider(&hAlg, BCRYPT_RNG_ALGORITHM, NULL, 0);
    if (status != 0) return 0;
    status = BCryptGenRandom(hAlg, buf, len, 0);
    BCryptCloseAlgorithmProvider(hAlg, 0);
    return (status == 0) ? len : 0;
}
#elif defined(__APPLE__)
#include <fcntl.h>
#include <unistd.h>
static int password_get_random(uint8_t *buf, int len) {
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) return 0;
    int total = 0;
    while (total < len) {
        int n = (int)read(fd, buf + total, len - total);
        if (n <= 0) break;
        total += n;
    }
    close(fd);
    return total;
}
#else
#define _GNU_SOURCE
#include <unistd.h>
#include <sys/syscall.h>
#include <fcntl.h>
static int password_get_random(uint8_t *buf, int len) {
    /* Try getrandom() first */
    int total = 0;
    while (total < len) {
        long n = syscall(SYS_getrandom, buf + total, len - total, 0);
        if (n <= 0) break;
        total += (int)n;
    }
    if (total == len) return total;
    /* Fallback to /dev/urandom */
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) return 0;
    total = 0;
    while (total < len) {
        int n = (int)read(fd, buf + total, len - total);
        if (n <= 0) break;
        total += n;
    }
    close(fd);
    return total;
}
#endif

/* === bcrypt implementation (based on OpenBSD, Public Domain) === */

/* Blowfish S-boxes and P-array (will be initialized by eksblowfish) */
typedef struct {
    uint32_t P[18];
    uint32_t S[4][256];
} blf_ctx;

/* bcrypt base64 alphabet (different from standard base64) */
static const char bcrypt_b64[] =
    "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

static const int8_t bcrypt_b64_decode[256] = {
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 0, 1,
    54,55,56,57,58,59,60,61,62,63,-1,-1,-1,-1,-1,-1,
    -1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,
    17,18,19,20,21,22,23,24,25,26,27,-1,-1,-1,-1,-1,
    -1,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,
    43,44,45,46,47,48,49,50,51,52,53,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
};

/* Blowfish constants (from OpenBSD) */
#define BLOWFISH_N 16

static void blf_enc(blf_ctx *c, uint32_t *data, int blocks) {
    uint32_t xl, xr, temp;
    int i, j;
    for (j = 0; j < blocks; j++) {
        xl = data[2*j];
        xr = data[2*j+1];
        for (i = 0; i < BLOWFISH_N; i++) {
            xl ^= c->P[i];
            xr ^= ((c->S[0][(xl >> 24) & 0xff] + c->S[1][(xl >> 16) & 0xff]) ^ c->S[2][(xl >> 8) & 0xff]) + c->S[3][xl & 0xff];
            temp = xl; xl = xr; xr = temp;
        }
        temp = xl; xl = xr; xr = temp;
        xr ^= c->P[BLOWFISH_N];
        xl ^= c->P[BLOWFISH_N + 1];
        data[2*j] = xl;
        data[2*j+1] = xr;
    }
}

static void blf_init(blf_ctx *c) {
    /* Initialize P and S with digits of pi (OpenBSD values) */
    static const uint32_t init_p[18] = {
        0x243f6a88,0x85a308d3,0x13198a2e,0x03707344,
        0xa4093822,0x299f31d0,0x082efa98,0xec4e6c89,
        0x452821e6,0x38d01377,0xbe5466cf,0x34e90c6c,
        0xc0ac29b7,0xc97c50dd,0x3f84d5b5,0xb5470917,
        0x9216d5d9,0x8979fb1b
    };
    static const uint32_t init_s[4][256] = {
        {
        0xd1310ba6,0x98dfb5ac,0x2ffd72db,0xd01adfb7,
        0xb8e1afed,0x6a267e96,0xba7c9045,0xf12c7f99,
        0x24a19947,0xb3916cf7,0x0801f2e2,0x858efc16,
        0x636920d8,0x71574e69,0xa458fea3,0xf4933d7e,
        0x0d95748f,0x728eb658,0x718bcd58,0x82154aee,
        0x7b54a41d,0xc25a59b5,0x9c30d539,0x2af26013,
        0xc5d1b023,0x286085f0,0xca417918,0xb8db38ef,
        0x8e79dcb0,0x603a180e,0x6c9e0e8b,0xb01e8a3e,
        0xd71577c1,0xbd314b27,0x78af2fda,0x55605c60,
        0xe65525f3,0xaa55ab94,0x57489862,0x63e81440,
        0x55ca396a,0x2aab10b6,0xb4cc5c34,0x1141e8ce,
        0xa15486af,0x7c72e993,0xb3ee1411,0x636fbc2a,
        0x2ba9c55d,0x741831f6,0xce5c3e16,0x9b87931e,
        0xafd6ba33,0x6c24cf5c,0x7a325381,0x28958677,
        0x3b8f4898,0x6b4bb9af,0xc4bfe81b,0x66282193,
        0x61d809cc,0xfb21a991,0x487cac60,0x5dec8032,
        0xef845d5d,0xe98575b1,0xdc262302,0xeb651b88,
        0x23893e81,0xd396acc5,0x0f6d6ff3,0x83f44239,
        0x2e0b4482,0xa4842004,0x69c8f04a,0x9e1f9b5e,
        0x21c66842,0xf6e96c9a,0x670c9c61,0xabd388f0,
        0x6a51a0d2,0xd8542f68,0x960fa728,0xab5133a3,
        0x6eef0b6c,0x137a3be4,0xba3bf050,0x7efb2a98,
        0xa1f1651d,0x39af0176,0x66ca593e,0x82430e88,
        0x8cee8619,0x456f9fb4,0x7d84a5c3,0x3b8b5ebe,
        0xe06f75d8,0x85c12073,0x401a449f,0x56c16aa6,
        0x4ed3aa62,0x363f7706,0x1bfedf72,0x429b023d,
        0x37d0d724,0xd00a1248,0xdb0fead3,0x49f1c09b,
        0x075372c9,0x80991b7b,0x25d479d8,0xf6e8def7,
        0xe3fe501a,0xb6794c3b,0x976ce0bd,0x04c006ba,
        0xc1a94fb6,0x409f60c4,0x5e5c9ec2,0x196a2463,
        0x68fb6faf,0x3e6c53b5,0x1339b2eb,0x3b52ec6f,
        0x6dfc511f,0x9b30952c,0xcc814544,0xaf5ebd09,
        0xbee3d004,0xde334afd,0x660f2807,0x192e4bb3,
        0xc0cba857,0x45c8740f,0xd20b5f39,0xb9d3fbdb,
        0x5579c0bd,0x1a60320a,0xd6a100c6,0x402c7279,
        0x679f25fe,0xfb1fa3cc,0x8ea5e9f8,0xdb3222f8,
        0x3c7516df,0xfd616b15,0x2f501ec8,0xad0552ab,
        0x323db5fa,0xfd238760,0x53317b48,0x3e00df82,
        0x9e5c57bb,0xca6f8ca0,0x1a87562e,0xdf1769db,
        0xd542a8f6,0x287effc3,0xac6732c6,0x8c4f5573,
        0x695b27b0,0xbbca58c8,0xe1ffa35d,0xb8f011a0,
        0x10fa3d98,0xfd2183b8,0x4afcb56c,0x2dd1d35b,
        0x9a53e479,0xb6f84565,0xd28e49bc,0x4bfb9790,
        0xe1ddf2da,0xa4cb7e33,0x62fb1341,0xcee4c6e8,
        0xef20cada,0x36774c01,0xd07e9efe,0x2bf11fb4,
        0x95dbda4d,0xae909198,0xeaad8e71,0x6b93d5a0,
        0xd08ed1d0,0xafc725e0,0x8e3c5b2f,0x8e7594b7,
        0x8ff6e2fb,0xf2122b64,0x8888b812,0x900df01c,
        0x4fad5ea0,0x688fc31c,0xd1cff191,0xb3a8c1ad,
        0x2f2f2218,0xbe0e1777,0xea752dfe,0x8b021fa1,
        0xe5a0cc0f,0xb56f74e8,0x18acf3d6,0xce89e299,
        0xb4a84fe0,0xfd13e0b7,0x7cc43b81,0xd2ada8d9,
        0x165fa266,0x80957705,0x93cc7314,0x211a1477,
        0xe6ad2065,0x77b5fa86,0xc75442f5,0xfb9d35cf,
        0xebcdaf0c,0x7b3e89a0,0xd6411bd3,0xae1e7e49,
        0x00250e2d,0x2071b35e,0x226800bb,0x57b8e0af,
        0x2464369b,0xf009b91e,0x5563911d,0x59dfa6aa,
        0x78c14389,0xd95a537f,0x207d5ba2,0x02e5b9c5,
        0x83260376,0x6295cfa9,0x11c81968,0x4e734a41,
        0xb3472dca,0x7b14a94a,0x1b510052,0x9a532915,
        0xd60f573f,0xbc9bc6e4,0x2b60a476,0x81e67400,
        0x08ba6fb5,0x571be91f,0xf296ec6b,0x2a0dd915,
        0xb6636521,0xe7b9f9b6,0xff34052e,0xc5855664,
        0x53b02d5d,0xa99f8fa1,0x08ba4799,0x6e85076a
        },
        {
        0x4b7a70e9,0xb5b32944,0xdb75092e,0xc4192623,
        0xad6ea6b0,0x49a7df7d,0x9cee60b8,0x8fedb266,
        0xecaa8c71,0x699a17ff,0x5664526c,0xc2b19ee1,
        0x193602a5,0x75094c29,0xa0591340,0xe4183a3e,
        0x3f54989a,0x5b429d65,0x6b8fe4d6,0x99f73fd6,
        0xa1d29c07,0xefe830f5,0x4d2d38e6,0xf0255dc1,
        0x4cdd2086,0x8470eb26,0x6382e9c6,0x021ecc5e,
        0x09686b3f,0x3ebaefc9,0x3c971814,0x6b6a70a1,
        0x687f3584,0x52a0e286,0xb79c5305,0xaa500737,
        0x3e07841c,0x7fdeae5c,0x8e7d44ec,0x5716f2b8,
        0xb03ada37,0xf0500c0d,0xf01c1f04,0x0200b3ff,
        0xae0cf51a,0x3cb574b2,0x25837a58,0xdc0921bd,
        0xd19113f9,0x7ca92ff6,0x94324773,0x22f54701,
        0x3ae5e581,0x37c2dadc,0xc8b57634,0x9af3dda7,
        0xa9446146,0x0fd0030e,0xecc8c73e,0xa4751e41,
        0xe238cd99,0x3bea0e2f,0x3280bba1,0x183eb331,
        0x4e548b38,0x4f6db908,0x6f420d03,0xf60a04bf,
        0x2cb81290,0x24977c79,0x5679b072,0xbcaf89af,
        0xde9a771f,0xd9930810,0xb38bae12,0xdccf3f2e,
        0x5512721f,0x2e6b7124,0x501adde6,0x9f84cd87,
        0x7a584718,0x7408da17,0xbc9f9abc,0xe94b7d8c,
        0xec7aec3a,0xdb851dfa,0x63094366,0xc464c3d2,
        0xef1c1847,0x3215d908,0xdd433b37,0x24c2ba16,
        0x12a14d43,0x2a65c451,0x50940002,0x133ae4dd,
        0x71dff89e,0x10314e55,0x81ac77d6,0x5f11199b,
        0x043556f1,0xd7a3c76b,0x3c11183b,0x5924a509,
        0xf28fe6ed,0x97f1fbfa,0x9ebabf2c,0x1e153c6e,
        0x86e34570,0xeae96fb1,0x860e5e0a,0x5a3e2ab3,
        0x771fe71c,0x4e3d06fa,0x2965dcb9,0x99e71d0f,
        0x803e89d6,0x5266c825,0x2e4cc978,0x9c10b36a,
        0xc6150eba,0x94e2ea78,0xa5fc3c53,0x1e0a2df4,
        0xf2f74ea7,0x361d2b3d,0x1939260f,0x19c27960,
        0x5223a708,0xf71312b6,0xebadfe6e,0xeac31f66,
        0xe3bc4595,0xa67bc883,0xb17f37d1,0x018cff28,
        0xc332ddef,0xbe6c5aa5,0x65582185,0x68ab9802,
        0xeecea50f,0xdb2f953b,0x2aef7dad,0x5b6e2f84,
        0x1521b628,0x29076170,0xecdd4775,0x619f1510,
        0x13cca830,0xeb61bd96,0x0334fe1e,0xaa0363cf,
        0xb5735c90,0x4c70a239,0xd59e9e0b,0xcbaade14,
        0xeecc86bc,0x60622ca7,0x9cab5cab,0xb2f3846e,
        0x648b1eaf,0x19bdf0ca,0xa02369b9,0x655abb50,
        0x40685a32,0x3c2ab4b3,0x319ee9d5,0xc021b8f7,
        0x9b540b19,0x875fa099,0x95f7997e,0x623d7da8,
        0xf837889a,0x97e32d77,0x11ed935f,0x16681281,
        0x0e358829,0xc7e61fd6,0x96dedfa1,0x7858ba99,
        0x57f584a5,0x1b227263,0x9b83c3ff,0x1ac24696,
        0xcdb30aeb,0x532e3054,0x8fd948e4,0x6dbc3128,
        0x58ebf2ef,0x34c6ffea,0xfe28ed61,0xee7c3c73,
        0x5d4a14d9,0xe864b7e3,0x42105d14,0x203e13e0,
        0x45eee2b6,0xa3aaabea,0xdb6c4f15,0xfacb4fd0,
        0xc742f442,0xef6abbb5,0x654f3b1d,0x41cd2105,
        0xd81e799e,0x86854dc7,0xe44b476a,0x3d816250,
        0xcf62a1f2,0x5b8d2646,0xfc8883a0,0xc1c7b6a3,
        0x7f1524c3,0x69cb7492,0x47848a0b,0x5692b285,
        0x095bbf00,0xad19489d,0x1462b174,0x23820e00,
        0x58428d2a,0x0c55f5ea,0x1dadf43e,0x233f7061,
        0x3372f092,0x8d937e41,0xd65fecf1,0x6c223bdb,
        0x7cde3759,0xcbee7460,0x4085f2a7,0xce77326e,
        0xa6078084,0x19f8509e,0xe8efd855,0x61d99735,
        0xa969a7aa,0xc50c06c2,0x5a04abfc,0x800bcadc,
        0x9e447a2e,0xc3453484,0xfdd56705,0x0e1e9ec9,
        0xdb73dbd3,0x105588cd,0x675fda79,0xe3674340,
        0xc5c43465,0x713e38d8,0x3d28f89e,0xf16dff20,
        0x153e21e7,0x8fb03d4a,0xe6e39f2b,0xdb83adf7
        },
        {
        0xe93d5a68,0x948140f7,0xf64c261c,0x94692934,
        0x411520f7,0x7602d4f7,0xbcf46b2e,0xd4a20068,
        0xd4082471,0x3320f46a,0x43b7d4b7,0x500061af,
        0x1e39f62e,0x97244546,0x14214f74,0xbf8b8840,
        0x4d95fc1d,0x96b591af,0x70f4ddd3,0x66a02f45,
        0xbfbc09ec,0x03bd9785,0x7fac6dd0,0x31cb8504,
        0x96eb27b3,0x55fd3941,0xda2547e6,0xabca0a9a,
        0x28507825,0x530429f4,0x0a2c86da,0xe9b66dfb,
        0x68dc1462,0xd7486900,0x680ec0a4,0x27a18dee,
        0x4f3ffea2,0xe887ad8c,0xb58ce006,0x7af4d6b6,
        0xaace1e7c,0xd3375fec,0xce78a399,0x406b2a42,
        0x20fe9e35,0xd9f385b9,0xee39d7ab,0x3b124e8b,
        0x1dc9faf7,0x4b6d1856,0x26a36631,0xeae397b2,
        0x3a6efa74,0xdd5b4332,0x6841e7f7,0xca7820fb,
        0xfb0af54e,0xd8feb397,0x454056ac,0xba489527,
        0x55533a3a,0x20838d87,0xfe6ba9b7,0xd096954b,
        0x55a867bc,0xa1159a58,0xcca92963,0x99e1db33,
        0xa62a4a56,0x3f3125f9,0x5ef47e1c,0x9029317c,
        0xfdf8e802,0x04272f70,0x80bb155c,0x05282ce3,
        0x95c11548,0xe4c66d22,0x48c1133f,0xc70f86dc,
        0x07f9c9ee,0x41041f0f,0x404779a4,0x5d886e17,
        0x325f51eb,0xd59bc0d1,0xf2bcc18f,0x41113564,
        0x257b7834,0x602a9c60,0xdff8e8a3,0x1f636c1b,
        0x0e12b4c2,0x02e1329e,0xaf664fd1,0xcad18115,
        0x6b2395e0,0x333e92e1,0x3b240b62,0xeebeb922,
        0x85b2a20e,0xe6ba0d99,0xde720c8c,0x2da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2,
        0x3c11183b,0x6b240b62,0x3da2f728,0x60daf94e,
        0x49c70a43,0xa42b1e7e,0x6b7047fe,0x8e25532d,
        0x9e9075b2,0x3c11183b,0x6b240b62,0x3da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2,
        0x3c11183b,0x6b240b62,0x3da2f728,0x60daf94e,
        0x49c70a43,0xa42b1e7e,0x6b7047fe,0x8e25532d,
        0x9e9075b2,0x3c11183b,0x6b240b62,0x3da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2,
        0x3c11183b,0x6b240b62,0x3da2f728,0x60daf94e,
        0x49c70a43,0xa42b1e7e,0x6b7047fe,0x8e25532d,
        0x9e9075b2,0x3c11183b,0x6b240b62,0x3da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2
        },
        {
        0xe93d5a68,0x948140f7,0xf64c261c,0x94692934,
        0x411520f7,0x7602d4f7,0xbcf46b2e,0xd4a20068,
        0xd4082471,0x3320f46a,0x43b7d4b7,0x500061af,
        0x1e39f62e,0x97244546,0x14214f74,0xbf8b8840,
        0x4d95fc1d,0x96b591af,0x70f4ddd3,0x66a02f45,
        0xbfbc09ec,0x03bd9785,0x7fac6dd0,0x31cb8504,
        0x96eb27b3,0x55fd3941,0xda2547e6,0xabca0a9a,
        0x28507825,0x530429f4,0x0a2c86da,0xe9b66dfb,
        0x68dc1462,0xd7486900,0x680ec0a4,0x27a18dee,
        0x4f3ffea2,0xe887ad8c,0xb58ce006,0x7af4d6b6,
        0xaace1e7c,0xd3375fec,0xce78a399,0x406b2a42,
        0x20fe9e35,0xd9f385b9,0xee39d7ab,0x3b124e8b,
        0x1dc9faf7,0x4b6d1856,0x26a36631,0xeae397b2,
        0x3a6efa74,0xdd5b4332,0x6841e7f7,0xca7820fb,
        0xfb0af54e,0xd8feb397,0x454056ac,0xba489527,
        0x55533a3a,0x20838d87,0xfe6ba9b7,0xd096954b,
        0x55a867bc,0xa1159a58,0xcca92963,0x99e1db33,
        0xa62a4a56,0x3f3125f9,0x5ef47e1c,0x9029317c,
        0xfdf8e802,0x04272f70,0x80bb155c,0x05282ce3,
        0x95c11548,0xe4c66d22,0x48c1133f,0xc70f86dc,
        0x07f9c9ee,0x41041f0f,0x404779a4,0x5d886e17,
        0x325f51eb,0xd59bc0d1,0xf2bcc18f,0x41113564,
        0x257b7834,0x602a9c60,0xdff8e8a3,0x1f636c1b,
        0x0e12b4c2,0x02e1329e,0xaf664fd1,0xcad18115,
        0x6b2395e0,0x333e92e1,0x3b240b62,0xeebeb922,
        0x85b2a20e,0xe6ba0d99,0xde720c8c,0x2da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2,
        0x3c11183b,0x6b240b62,0x3da2f728,0x60daf94e,
        0x49c70a43,0xa42b1e7e,0x6b7047fe,0x8e25532d,
        0x9e9075b2,0x3c11183b,0x6b240b62,0x3da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2,
        0x3c11183b,0x6b240b62,0x3da2f728,0x60daf94e,
        0x49c70a43,0xa42b1e7e,0x6b7047fe,0x8e25532d,
        0x9e9075b2,0x3c11183b,0x6b240b62,0x3da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2,
        0x3c11183b,0x6b240b62,0x3da2f728,0x60daf94e,
        0x49c70a43,0xa42b1e7e,0x6b7047fe,0x8e25532d,
        0x9e9075b2,0x3c11183b,0x6b240b62,0x3da2f728,
        0x60daf94e,0x49c70a43,0xa42b1e7e,0x6b7047fe,
        0x8e25532d,0x9e9075b2,0x3c11183b,0x6b240b62,
        0x3da2f728,0x60daf94e,0x49c70a43,0xa42b1e7e,
        0x6b7047fe,0x8e25532d,0x9e9075b2,0x3c11183b,
        0x6b240b62,0x3da2f728,0x60daf94e,0x49c70a43,
        0xa42b1e7e,0x6b7047fe,0x8e25532d,0x9e9075b2
        }
    };

    memcpy(c->P, init_p, sizeof(init_p));
    memcpy(c->S, init_s, sizeof(init_s));
}

static void blf_expandkey(blf_ctx *c, const uint8_t *key, int key_len,
                           const uint8_t *salt, int salt_len) {
    int i, j;
    uint32_t data[2], temp;
    static const uint8_t zero_salt[1] = {0};

    /* Avoid division by zero when salt_len is 0 (used in eksblowfish rounds) */
    if (salt_len <= 0 || salt == NULL) {
        salt = zero_salt;
        salt_len = 1;
    }

    /* XOR key into P */
    j = 0;
    for (i = 0; i < 18; i++) {
        temp = 0;
        temp = (temp << 8) | key[j % key_len]; j++;
        temp = (temp << 8) | key[j % key_len]; j++;
        temp = (temp << 8) | key[j % key_len]; j++;
        temp = (temp << 8) | key[j % key_len]; j++;
        c->P[i] ^= temp;
    }

    /* XOR salt into P and encrypt */
    data[0] = 0;
    data[1] = 0;
    j = 0;
    for (i = 0; i < 18; i += 2) {
        data[0] ^= salt[j % salt_len]; j++;
        data[0] = (data[0] << 8) | salt[j % salt_len]; j++;
        data[0] = (data[0] << 8) | salt[j % salt_len]; j++;
        data[0] = (data[0] << 8) | salt[j % salt_len]; j++;
        data[1] ^= salt[j % salt_len]; j++;
        data[1] = (data[1] << 8) | salt[j % salt_len]; j++;
        data[1] = (data[1] << 8) | salt[j % salt_len]; j++;
        data[1] = (data[1] << 8) | salt[j % salt_len]; j++;
        blf_enc(c, data, 1);
        c->P[i] = data[0];
        c->P[i+1] = data[1];
    }

    /* XOR salt into S and encrypt */
    for (i = 0; i < 4; i++) {
        for (j = 0; j < 256; j += 2) {
            data[0] ^= salt[(j+0) % salt_len];
            data[0] = (data[0] << 8) | salt[(j+1) % salt_len];
            data[0] = (data[0] << 8) | salt[(j+2) % salt_len];
            data[0] = (data[0] << 8) | salt[(j+3) % salt_len];
            data[1] ^= salt[(j+4) % salt_len];
            data[1] = (data[1] << 8) | salt[(j+5) % salt_len];
            data[1] = (data[1] << 8) | salt[(j+6) % salt_len];
            data[1] = (data[1] << 8) | salt[(j+7) % salt_len];
            blf_enc(c, data, 1);
            c->S[i][j] = data[0];
            c->S[i][j+1] = data[1];
        }
    }
}

static void eksblowfish(blf_ctx *c, int cost, const uint8_t *salt,
                         const uint8_t *key, int key_len) {
    int i, rounds;
    blf_init(c);
    blf_expandkey(c, key, key_len, salt, 16);
    rounds = 1 << cost;
    for (i = 0; i < rounds; i++) {
        blf_expandkey(c, key, key_len, NULL, 0);
        blf_expandkey(c, salt, 16, NULL, 0);
    }
}

/* bcrypt base64 encode */
static void bcrypt_encode_base64(char *dst, const uint8_t *src, int len) {
    int i = 0;
    while (i < len) {
        int read = 1;
        uint32_t c1 = src[i++];
        uint32_t c2 = 0;
        uint32_t c3 = 0;
        if (i < len) { c2 = src[i++]; read++; }
        if (i < len) { c3 = src[i++]; read++; }
        uint32_t triple = (c1 << 16) | (c2 << 8) | c3;
        *dst++ = bcrypt_b64[(triple >> 18) & 0x3f];
        *dst++ = bcrypt_b64[(triple >> 12) & 0x3f];
        if (read >= 2) *dst++ = bcrypt_b64[(triple >> 6) & 0x3f];
        if (read >= 3) *dst++ = bcrypt_b64[triple & 0x3f];
    }
    *dst = '\0';
}

/* bcrypt base64 decode */
static int bcrypt_decode_base64(uint8_t *dst, const char *src, int max_len) {
    int i = 0, out = 0;
    while (src[i] && out < max_len) {
        int8_t c1 = bcrypt_b64_decode[(uint8_t)src[i++]];
        int8_t c2 = (src[i]) ? bcrypt_b64_decode[(uint8_t)src[i++]] : -1;
        int8_t c3 = (src[i]) ? bcrypt_b64_decode[(uint8_t)src[i++]] : -1;
        int8_t c4 = (src[i]) ? bcrypt_b64_decode[(uint8_t)src[i++]] : -1;
        if (c1 < 0 || c2 < 0) break;
        dst[out++] = (uint8_t)((c1 << 2) | (c2 >> 4));
        if (out >= max_len) break;
        if (c3 < 0) break;
        dst[out++] = (uint8_t)(((c2 & 0x0f) << 4) | (c3 >> 2));
        if (out >= max_len) break;
        if (c4 < 0) break;
        dst[out++] = (uint8_t)(((c3 & 0x03) << 6) | c4);
    }
    return out;
}

/* Generate bcrypt hash */
static int bcrypt_hash(const char *password, int cost, const uint8_t *salt,
                        char *out, int out_len) {
    blf_ctx c;
    uint8_t ciphertext[24] = "OrpheanBeholderScryDoubt";
    uint8_t key[72];
    int i, j;
    int password_len = (int)strlen(password);
    if (password_len > 71) password_len = 71;

    if (cost < 4 || cost > 31) return -1;
    if (out_len < 61) return -1;

    /* Prepare key: password + null */
    memset(key, 0, sizeof(key));
    memcpy(key, password, password_len);
    key[password_len] = 0;

    /* EksBlowfish setup */
    eksblowfish(&c, cost, salt, key, password_len + 1);

    /* Encrypt "OrpheanBeholderScryDoubt" 64 times */
    for (i = 0; i < 64; i++) {
        blf_enc(&c, (uint32_t *)ciphertext, 3);
    }

    /* Format: $2b$CC$<salt><hash> */
    j = snprintf(out, out_len, "$2b$%02d$", cost);
    bcrypt_encode_base64(out + j, salt, 16);
    j = (int)strlen(out);
    bcrypt_encode_base64(out + j, ciphertext, 23);

    return 0;
}

/* Verify bcrypt hash */
static int bcrypt_verify(const char *password, const char *hash) {
    uint8_t salt[16];
    char computed[64];
    int cost;
    int i;
    int result = 0;

    if (strlen(hash) < 60) return 0;
    if (hash[0] != '$' || hash[1] != '2') return 0;
    if (hash[2] != 'a' && hash[2] != 'b' && hash[2] != 'y') return 0;
    if (hash[3] != '$') return 0;

    cost = (hash[4] - '0') * 10 + (hash[5] - '0');
    if (cost < 4 || cost > 31) return 0;

    /* Decode salt */
    i = bcrypt_decode_base64(salt, hash + 7, 16);
    if (i != 16) return 0;

    /* Compute hash */
    if (bcrypt_hash(password, cost, salt, computed, sizeof(computed)) != 0)
        return 0;

    /* Constant-time comparison */
    for (i = 0; i < 60; i++) {
        if (computed[i] != hash[i]) result = 1;
    }

    return result == 0;
}

/* === TLL Builtin Binding === */

TLLValue password_builtin_invoke(TLLVM *vm, int idx, TLLValue *args, int argCount) {
    (void)vm;
    switch (idx) {
        case 180: { /* password.hash(password) -> bcrypt hash (cost=12) */
            if (argCount < 1) return tll_null();
            char *password = tll_to_string(args[0]);
            if (!password) return tll_null();
            uint8_t salt[16];
            if (password_get_random(salt, 16) != 16) {
                free(password);
                return tll_null();
            }
            char hash[64];
            int rc = bcrypt_hash(password, 12, salt, hash, sizeof(hash));
            free(password);
            if (rc != 0) return tll_null();
            return tll_string(hash);
        }
        case 181: { /* password.hashWithCost(password, cost) -> bcrypt hash */
            if (argCount < 2) return tll_null();
            char *password = tll_to_string(args[0]);
            int cost = (args[1].type == TLL_INT) ? (int)args[1].as.integer : 12;
            if (!password) return tll_null();
            if (cost < 4) cost = 4;
            if (cost > 31) cost = 31;
            uint8_t salt[16];
            if (password_get_random(salt, 16) != 16) {
                free(password);
                return tll_null();
            }
            char hash[64];
            int rc = bcrypt_hash(password, cost, salt, hash, sizeof(hash));
            free(password);
            if (rc != 0) return tll_null();
            return tll_string(hash);
        }
        case 182: { /* password.verify(password, hash) -> bool */
            if (argCount < 2) return tll_bool(0);
            char *password = tll_to_string(args[0]);
            char *hash = tll_to_string(args[1]);
            if (!password || !hash) {
                if (password) free(password);
                if (hash) free(hash);
                return tll_bool(0);
            }
            int ok = bcrypt_verify(password, hash);
            free(password);
            free(hash);
            return ok ? tll_bool(1) : tll_bool(0);
        }
        case 183: { /* password.needsRehash(hash, minCost) -> bool */
            if (argCount < 1) return tll_bool(1);
            char *hash = tll_to_string(args[0]);
            int minCost = (argCount >= 2 && args[1].type == TLL_INT) ?
                           (int)args[1].as.integer : 12;
            if (!hash) return tll_bool(1);
            int len = (int)strlen(hash);
            if (len < 60 || hash[0] != '$' || hash[1] != '2') {
                free(hash);
                return tll_bool(1);
            }
            if (hash[2] != 'a' && hash[2] != 'b' && hash[2] != 'y') {
                free(hash);
                return tll_bool(1);
            }
            int cost = (hash[4] - '0') * 10 + (hash[5] - '0');
            free(hash);
            return (cost < minCost) ? tll_bool(1) : tll_bool(0);
        }
        case 184: { /* password.hashInfo(hash) -> map {algorithm, cost, valid} */
            if (argCount < 1) return tll_null();
            char *hash = tll_to_string(args[0]);
            TLLValue m = tll_map();
            if (!hash) {
                map_set(m.as.map, "valid", tll_bool(0));
                return m;
            }
            int len = (int)strlen(hash);
            int valid = (len >= 60 && hash[0] == '$' && hash[1] == '2' &&
                        (hash[2] == 'a' || hash[2] == 'b' || hash[2] == 'y') &&
                        hash[3] == '$');
            char algo[16] = "bcrypt";
            int cost = 0;
            if (valid) {
                cost = (hash[4] - '0') * 10 + (hash[5] - '0');
            }
            map_set(m.as.map, "valid", valid ? tll_bool(1) : tll_bool(0));
            map_set(m.as.map, "algorithm", tll_string(algo));
            map_set(m.as.map, "cost", tll_int(cost));
            map_set(m.as.map, "length", tll_int(len));
            free(hash);
            return m;
        }
        default:
            return tll_null();
    }
}
