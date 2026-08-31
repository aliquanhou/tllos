/* TLL Builtin functions - Host ABI + stdlib implementation for bootstrap VM.
 * Note: In the final architecture, json/math/strings/arrays/convert should be
 * implemented in TLL stdlib. This C implementation is for bootstrap only.
 */
#include "tllvm.h"
#include <time.h>
#include <sys/stat.h>
#include <errno.h>
#include <ctype.h>

#ifndef S_ISREG
#define S_ISREG(m) (((m) & 0170000) == 0100000)
#endif
#ifndef S_ISDIR
#define S_ISDIR(m) (((m) & 0170000) == 0040000)
#endif

#ifdef _WIN32
/* HttpTask type - shared by MSVC and TCC */
typedef struct {
    unsigned int client_fd;
    TLLVM *vm;
    TLLValue handler_fn;
} HttpTask;
static void http_process_task(HttpTask *task);
#ifdef _MSC_VER
/* MSVC: use system headers */
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <winhttp.h>
#include <direct.h>
#else
/* TCC: winsock2.h/winhttp.h not available, manual declarations below */

/* Global VM lock for concurrent HTTP requests - protects VM state during handler invocation */

/* Minimal WinHTTP declarations (TCC lacks winhttp.h) */
#ifndef _WINHTTP_H_
#define _WINHTTP_H_
#define WINHTTP_ACCESS_TYPE_DEFAULT_PROXY 0
#define WINHTTP_NO_PROXY_NAME NULL
#define WINHTTP_NO_PROXY_BYPASS NULL
#define WINHTTP_NO_ADDITIONAL_HEADERS NULL
#define WINHTTP_NO_REQUEST_DATA NULL
#define WINHTTP_NO_REFERER NULL
#define WINHTTP_DEFAULT_ACCEPT_TYPES NULL
#define WINHTTP_QUERY_STATUS_CODE 0x10000013
#define WINHTTP_QUERY_FLAG_NUMBER 0x20000000
#define WINHTTP_FLAG_SECURE 0x00800000
typedef void* HINTERNET;
typedef unsigned short INTERNET_PORT;
WINBOOL WINAPI WinHttpCloseHandle(HINTERNET);
HINTERNET WINAPI WinHttpOpen(LPCWSTR, DWORD, LPCWSTR, LPCWSTR, DWORD);
HINTERNET WINAPI WinHttpConnect(HINTERNET, LPCWSTR, INTERNET_PORT, DWORD);
HINTERNET WINAPI WinHttpOpenRequest(HINTERNET, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR*, DWORD);
WINBOOL WINAPI WinHttpSendRequest(HINTERNET, LPCWSTR, DWORD, LPVOID, DWORD, DWORD, DWORD_PTR);
WINBOOL WINAPI WinHttpReceiveResponse(HINTERNET, LPVOID);
WINBOOL WINAPI WinHttpQueryHeaders(HINTERNET, DWORD, LPCWSTR, LPVOID, LPDWORD, LPDWORD);
WINBOOL WINAPI WinHttpQueryDataAvailable(HINTERNET, LPDWORD);
WINBOOL WINAPI WinHttpReadData(HINTERNET, LPVOID, DWORD, LPDWORD);
#endif
/* Minimal Winsock2 declarations (TCC lacks winsock2.h) */
#ifndef _WINSOCK2_H_
#define _WINSOCK2_H_
typedef UINT_PTR SOCKET;
#define INVALID_SOCKET (SOCKET)(~0)
#define SOCKET_ERROR (-1)
#define SOL_SOCKET 0xffff
#define SO_REUSEADDR 0x0004
#define SO_RCVTIMEO 0x1006
#define SO_SNDTIMEO 0x1005
#define AF_INET 2
#define SOCK_STREAM 1
#define IPPROTO_TCP 6
typedef struct in_addr { unsigned long s_addr; } IN_ADDR;
typedef struct sockaddr_in { short sin_family; unsigned short sin_port; IN_ADDR sin_addr; char sin_zero[8]; } SOCKADDR_IN;
typedef struct sockaddr { unsigned short sa_family; char sa_data[14]; } SOCKADDR;
typedef int socklen_t;
typedef struct WSAData { WORD wVersion; WORD wHighVersion; char szDescription[257]; char szSystemStatus[129]; unsigned short iMaxSockets; unsigned short iMaxUdpDg; char *lpVendorInfo; } WSADATA;
int PASCAL WSAStartup(WORD, WSADATA*);
int PASCAL WSACleanup(void);
SOCKET PASCAL socket(int, int, int);
int PASCAL setsockopt(SOCKET, int, int, const char*, int);
int PASCAL bind(SOCKET, const SOCKADDR*, int);
int PASCAL listen(SOCKET, int);
int PASCAL connect(SOCKET, const SOCKADDR*, int);
SOCKET PASCAL accept(SOCKET, SOCKADDR*, int*);
int PASCAL recv(SOCKET, char*, int, int);
int PASCAL send(SOCKET, const char*, int, int);
int PASCAL closesocket(SOCKET);
unsigned long PASCAL inet_addr(const char*);
unsigned short PASCAL htons(unsigned short);
/* fd_set / select for non-blocking IO (P0-15.16) */
#ifndef FD_SETSIZE
#define FD_SETSIZE 64
#endif
#ifndef _FD_SET_DEFINED
#define _FD_SET_DEFINED
typedef struct fd_set { unsigned int fd_count; SOCKET fd_array[FD_SETSIZE]; } fd_set;
#endif
#define FD_ZERO(s) ((s)->fd_count = 0)
#define FD_SET(fd,s) do { if ((s)->fd_count < FD_SETSIZE) (s)->fd_array[(s)->fd_count++] = (SOCKET)(fd); } while(0)
static int builtin_fd_isset(SOCKET fd, fd_set *s) { int _i=0; while(_i<s->fd_count){if(s->fd_array[_i]==fd) return 1;_i++;} return 0; }
#define FD_ISSET(fd,s) builtin_fd_isset((SOCKET)(fd), s)
#ifndef _TIMEVAL_DEFINED
#define _TIMEVAL_DEFINED
struct timeval { long tv_sec; long tv_usec; };
#endif
int PASCAL select(int, fd_set*, fd_set*, fd_set*, const struct timeval*);
#endif
/* Libraries linked via build.bat (DLL paths for TCC) */
/* Minimal winnls declarations (TCC lacks winnls.h) */
#ifndef CP_UTF8
#define CP_UTF8 65001
#endif
int WINAPI MultiByteToWideChar(UINT, DWORD, LPCCH, int, LPWSTR, int);
#endif /* _MSC_VER */
#define CHDIR _chdir
#define GETCWD _getcwd

/* Global VM lock */
static CRITICAL_SECTION g_vm_lock;
static int g_vm_lock_initialized = 0;

/* === Worker Pool === */
/* Fixed pool of worker threads + thread-safe task queue.
   Replaces thread-per-connection to avoid OS thread explosion at high connection counts. */
#define WORKER_POOL_SIZE 8


typedef struct TaskNode {
    HttpTask *task;
    struct TaskNode *next;
} TaskNode;

static TaskNode *g_task_head = NULL;
static TaskNode *g_task_tail = NULL;
static CRITICAL_SECTION g_queue_lock;
static HANDLE g_task_sem = NULL;
static int g_pool_initialized = 0;

/* Forward declarations */
static DWORD WINAPI worker_thread(LPVOID param);

static void init_worker_pool(void) {
    InitializeCriticalSection(&g_queue_lock);
    g_task_sem = CreateSemaphore(NULL, 0, 1000000, NULL);
    for (int i = 0; i < WORKER_POOL_SIZE; i++) {
        CreateThread(NULL, 0, worker_thread, NULL, 0, NULL);
    }
    g_pool_initialized = 1;
    fprintf(stderr, "tllvm: worker pool initialized with %d threads\n", WORKER_POOL_SIZE);
}

static void enqueue_task(HttpTask *task) {
    TaskNode *node = (TaskNode*)malloc(sizeof(TaskNode));
    node->task = task;
    node->next = NULL;
    EnterCriticalSection(&g_queue_lock);
    if (g_task_tail) {
        g_task_tail->next = node;
    } else {
        g_task_head = node;
    }
    g_task_tail = node;
    LeaveCriticalSection(&g_queue_lock);
    ReleaseSemaphore(g_task_sem, 1, NULL);
}

static DWORD WINAPI worker_thread(LPVOID param) {
    (void)param;
    while (1) {
        WaitForSingleObject(g_task_sem, INFINITE);
        EnterCriticalSection(&g_queue_lock);
        TaskNode *node = g_task_head;
        if (node) {
            g_task_head = node->next;
            if (!g_task_head) g_task_tail = NULL;
        }
        LeaveCriticalSection(&g_queue_lock);
        if (node) {
            http_process_task(node->task);
            free(node->task);
            free(node);
        }
    }
    return 0;
}
#else
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <dirent.h>
#include <unistd.h>
#include <alloca.h>
typedef int SOCKET;
#define INVALID_SOCKET (-1)
#define closesocket(s) close(s)
#define CHDIR chdir
#define GETCWD getcwd
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

#ifdef _WIN32
/* HTTP task processor - called by worker threads from the pool.
   VM invocation is protected by g_vm_lock. */
static void http_process_task(HttpTask *data) {
    SOCKET client_fd = (SOCKET)data->client_fd;
    TLLVM *vm = data->vm;
    TLLValue handlerFn = data->handler_fn;

    /* Read request */
    char req_buf[65536];
    int total_read = 0;
    while (total_read < (int)sizeof(req_buf) - 1) {
        int n = recv(client_fd, req_buf + total_read, sizeof(req_buf) - 1 - total_read, 0);
        if (n <= 0) break;
        total_read += n;
        req_buf[total_read] = '\0';
        if (strstr(req_buf, "\r\n\r\n") != NULL) {
            char *cl = strstr(req_buf, "Content-Length:");
            if (cl) {
                int content_len = atoi(cl + 15);
                char *body_start = strstr(req_buf, "\r\n\r\n");
                if (body_start) {
                    body_start += 4;
                    int body_read = total_read - (int)(body_start - req_buf);
                    if (body_read >= content_len) break;
                }
            } else {
                break;
            }
        }
    }
    req_buf[total_read] = '\0';

    /* Parse request line */
    char method[16] = "GET";
    char rawPath[1024] = "/";
    char *line_end = strstr(req_buf, "\r\n");
    if (line_end) {
        *line_end = '\0';
        sscanf(req_buf, "%15s %1023s", method, rawPath);
    }
    /* Parse path and query */
    char path[1024] = "/";
    char query[1024] = "";
    char *qmark = strchr(rawPath, '?');
    if (qmark) {
        int plen = (int)(qmark - rawPath);
        if (plen > 1023) plen = 1023;
        strncpy(path, rawPath, plen); path[plen] = '\0';
        strncpy(query, qmark + 1, 1023); query[1023] = '\0';
    } else {
        strncpy(path, rawPath, 1023); path[1023] = '\0';
    }
    /* Parse headers into map */
    TLLValue headersMap = tll_map();
    char *header_start = line_end ? line_end + 2 : req_buf;
    char *header_end = strstr(header_start, "\r\n\r\n");
    if (header_end) {
        char *line = header_start;
        while (line < header_end) {
            char *next_line = strstr(line, "\r\n");
            if (!next_line || next_line > header_end) break;
            *next_line = '\0';
            char *colon = strchr(line, ':');
            if (colon) {
                *colon = '\0';
                char *val = colon + 1;
                while (*val == ' ') val++;
                map_set(headersMap.as.map, line, tll_string(val));
            }
            line = next_line + 2;
        }
    }
    /* Parse query into map */
    TLLValue queryMap = tll_map();
    if (strlen(query) > 0) {
        char *q = query;
        while (*q) {
            char *amp = strchr(q, '&');
            if (amp) *amp = '\0';
            char *eq = strchr(q, '=');
            if (eq) {
                *eq = '\0';
                map_set(queryMap.as.map, q, tll_string(eq + 1));
            } else {
                map_set(queryMap.as.map, q, tll_string(""));
            }
            if (!amp) break;
            q = amp + 1;
        }
    }
    /* Build request map */
    TLLValue reqMap = tll_map();
    map_set(reqMap.as.map, "method", tll_string(method));
    map_set(reqMap.as.map, "path", tll_string(path));
    map_set(reqMap.as.map, "rawPath", tll_string(rawPath));
    map_set(reqMap.as.map, "query", tll_string(query));
    map_set(reqMap.as.map, "queryMap", queryMap);
    map_set(reqMap.as.map, "headers", headersMap);
    if (header_end) {
        char *body_start = header_end + 4;
        map_set(reqMap.as.map, "body", tll_string(body_start));
    } else {
        map_set(reqMap.as.map, "body", tll_string(""));
    }

    /* Call TLL handler under VM lock */
    TLLValue handlerArgs[1] = { reqMap };
    EnterCriticalSection(&g_vm_lock);
    TLLValue resp = tll_vm_invoke(vm, handlerFn, handlerArgs, 1);
    LeaveCriticalSection(&g_vm_lock);

    /* Build response */
    char resp_buf[65536];
    int resp_len = 0;
    int status = 200;
    const char *body = "";
    const char *content_type = "text/html; charset=utf-8";
    TLLValue respHeaders = tll_null();
    if (resp.type == TLL_MAP) {
        TLLValue sv = map_get(resp.as.map, "status");
        if (sv.type == TLL_INT) status = (int)sv.as.integer;
        TLLValue bv = map_get(resp.as.map, "body");
        if (bv.type == TLL_STRING) body = bv.as.string;
        TLLValue cv = map_get(resp.as.map, "contentType");
        if (cv.type == TLL_STRING) content_type = cv.as.string;
        TLLValue hv = map_get(resp.as.map, "headers");
        if (hv.type == TLL_MAP) respHeaders = hv;
    } else if (resp.type == TLL_STRING) {
        body = resp.as.string;
    }
    const char *reason = "OK";
    if (status == 201) reason = "Created";
    else if (status == 204) reason = "No Content";
    else if (status == 301) reason = "Moved Permanently";
    else if (status == 302) reason = "Found";
    else if (status == 400) reason = "Bad Request";
    else if (status == 401) reason = "Unauthorized";
    else if (status == 403) reason = "Forbidden";
    else if (status == 404) reason = "Not Found";
    else if (status == 405) reason = "Method Not Allowed";
    else if (status == 500) reason = "Internal Server Error";
    else if (status == 502) reason = "Bad Gateway";
    else if (status == 503) reason = "Service Unavailable";
    int hdr_len = snprintf(resp_buf, sizeof(resp_buf),
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n",
        status, reason, content_type, (int)strlen(body));
    if (respHeaders.type == TLL_MAP) {
        for (int b = 0; b < respHeaders.as.map->bucketCount; b++) {
            TLLMapEntry *e = respHeaders.as.map->buckets[b];
            while (e) {
                if (e->value.type == TLL_STRING) {
                    hdr_len += snprintf(resp_buf + hdr_len, sizeof(resp_buf) - hdr_len,
                        "%s: %s\r\n", e->key, e->value.as.string);
                }
                e = e->next;
            }
        }
    }
    hdr_len += snprintf(resp_buf + hdr_len, sizeof(resp_buf) - hdr_len, "\r\n");
    resp_len = hdr_len + (int)strlen(body);
    if (resp_len < (int)sizeof(resp_buf)) {
        memcpy(resp_buf + hdr_len, body, strlen(body));
    }
    send(client_fd, resp_buf, resp_len, 0);
    closesocket(client_fd);
}
#endif /* _WIN32 */

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

    /* http (91-97) - WinHTTP client implementation (P0-3.1) */
    if (idx >= 91 && idx <= 97) {
#ifdef _WIN32
        if (idx == 91 || idx == 92 || idx == 93) {
            /* http.get / http.post / http.request */
            const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
            const char *body = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
            const char *method = (idx == 92) ? "POST" : "GET";
            if (idx == 93 && argCount > 0 && args[0].type == TLL_MAP) {
                TLLValue mv = map_get(args[0].as.map, "method");
                if (mv.type == TLL_STRING) method = mv.as.string;
                TLLValue uv = map_get(args[0].as.map, "url");
                if (uv.type == TLL_STRING) url = uv.as.string;
                TLLValue bv = map_get(args[0].as.map, "body");
                if (bv.type == TLL_STRING) body = bv.as.string;
            }

            /* Parse URL */
            char host[256] = "", path[1024] = "/";
            int port = 80, isHttps = 0;
            const char *p = url;
            if (strncmp(p, "https://", 8) == 0) { isHttps = 1; port = 443; p += 8; }
            else if (strncmp(p, "http://", 7) == 0) { p += 7; }
            const char *slash = strchr(p, '/');
            const char *colon = strchr(p, ':');
            int hostLen;
            if (colon && (!slash || colon < slash)) {
                hostLen = (int)(colon - p);
                port = atoi(colon + 1);
            } else {
                hostLen = slash ? (int)(slash - p) : (int)strlen(p);
            }
            if (hostLen > 255) hostLen = 255;
            strncpy(host, p, hostLen); host[hostLen] = '\0';
            if (slash) strncpy(path, slash, 1023); else strcpy(path, "/");

            /* WinHTTP request */
            TLLValue result = tll_map();
            HINTERNET hSession = WinHttpOpen(L"TLLOS/1.0", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
            if (!hSession) { map_set(result.as.map, "ok", tll_bool(0)); map_set(result.as.map, "error", tll_string("WinHttpOpen failed")); return result; }
            HINTERNET hConnect = WinHttpConnect(hSession, (WCHAR*)host, (INTERNET_PORT)port, 0);
            /* Note: host is ANSI; WinHttpConnect expects wide. Convert properly below. */
            /* Re-do with wide char conversion */
            if (hConnect) WinHttpCloseHandle(hConnect);
            WCHAR wideHost[256];
            MultiByteToWideChar(CP_UTF8, 0, host, -1, wideHost, 256);
            hConnect = WinHttpConnect(hSession, wideHost, (INTERNET_PORT)port, 0);
            if (!hConnect) { WinHttpCloseHandle(hSession); map_set(result.as.map, "ok", tll_bool(0)); map_set(result.as.map, "error", tll_string("WinHttpConnect failed")); return result; }
            DWORD flags = isHttps ? WINHTTP_FLAG_SECURE : 0;
            HINTERNET hRequest = WinHttpOpenRequest(hConnect, (WCHAR*)method, (WCHAR*)path, NULL, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
            /* Convert method and path to wide */
            if (hRequest) WinHttpCloseHandle(hRequest);
            WCHAR wideMethod[16], widePath[1024];
            MultiByteToWideChar(CP_UTF8, 0, method, -1, wideMethod, 16);
            MultiByteToWideChar(CP_UTF8, 0, path, -1, widePath, 1024);
            hRequest = WinHttpOpenRequest(hConnect, wideMethod, widePath, NULL, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
            if (!hRequest) { WinHttpCloseHandle(hConnect); WinHttpCloseHandle(hSession); map_set(result.as.map, "ok", tll_bool(0)); map_set(result.as.map, "error", tll_string("WinHttpOpenRequest failed")); return result; }

            BOOL sendOk;
            if (strcmp(method, "POST") == 0 && body && strlen(body) > 0) {
                sendOk = WinHttpSendRequest(hRequest, L"Content-Type: application/json\r\n", -1, (LPVOID)body, (DWORD)strlen(body), (DWORD)strlen(body), 0);
            } else {
                sendOk = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0, WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
            }
            if (!sendOk) {
                DWORD err = GetLastError();
                char errBuf[64]; snprintf(errBuf, sizeof(errBuf), "SendRequest failed: %lu", err);
                WinHttpCloseHandle(hRequest); WinHttpCloseHandle(hConnect); WinHttpCloseHandle(hSession);
                map_set(result.as.map, "ok", tll_bool(0)); map_set(result.as.map, "error", tll_string(errBuf));
                return result;
            }
            if (!WinHttpReceiveResponse(hRequest, NULL)) {
                WinHttpCloseHandle(hRequest); WinHttpCloseHandle(hConnect); WinHttpCloseHandle(hSession);
                map_set(result.as.map, "ok", tll_bool(0)); map_set(result.as.map, "error", tll_string("ReceiveResponse failed"));
                return result;
            }
            /* Status code */
            DWORD statusCode = 0, statusSize = sizeof(statusCode);
            WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER, NULL, &statusCode, &statusSize, NULL);
            map_set(result.as.map, "status", tll_int((long long)statusCode));
            map_set(result.as.map, "ok", tll_bool(statusCode >= 200 && statusCode < 300));
            /* Read body */
            char *respBody = (char*)malloc(1); respBody[0] = '\0';
            DWORD totalLen = 0, available = 0, read = 0;
            do {
                available = 0;
                WinHttpQueryDataAvailable(hRequest, &available);
                if (available == 0) break;
                char *chunk = (char*)malloc(available + 1);
                WinHttpReadData(hRequest, chunk, available, &read);
                chunk[read] = '\0';
                respBody = (char*)realloc(respBody, totalLen + read + 1);
                memcpy(respBody + totalLen, chunk, read);
                totalLen += read;
                respBody[totalLen] = '\0';
                free(chunk);
            } while (read > 0);
            map_set(result.as.map, "body", tll_string(respBody));
            free(respBody);
            WinHttpCloseHandle(hRequest); WinHttpCloseHandle(hConnect); WinHttpCloseHandle(hSession);
            return result;
        }
#ifdef _WIN32
        if (idx == 94) { /* http.serve(addr, handler) - basic HTTP server (P0-4 dogfood) */
            const char *addr = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "0.0.0.0:8080";
            if (argCount < 2 || (args[1].type != TLL_FUNCTION && args[1].type != TLL_MAP)) {
                fprintf(stderr, "tllvm: http.serve requires handler function\n");
                return tll_null();
            }
            /* Parse host:port */
            char host[256] = "0.0.0.0";
            int port = 8080;
            const char *colon = strrchr(addr, ':');
            if (colon) {
                int hlen = (int)(colon - addr);
                if (hlen > 0 && hlen < 256) { strncpy(host, addr, hlen); host[hlen] = '\0'; }
                port = atoi(colon + 1);
            }
#ifdef _WIN32
            WSADATA wsa;
            if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
                fprintf(stderr, "tllvm: WSAStartup failed\n");
                return tll_null();
            }
#endif
            SOCKET server_fd = socket(AF_INET, SOCK_STREAM, 0);
            if (server_fd == INVALID_SOCKET) {
                fprintf(stderr, "tllvm: socket failed\n");
                return tll_null();
            }
            int opt = 1;
            setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
            struct sockaddr_in address;
            address.sin_family = AF_INET;
            address.sin_addr.s_addr = inet_addr(host);
            address.sin_port = htons(port);
            if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
                fprintf(stderr, "tllvm: bind failed on %s:%d\n", host, port);
                closesocket(server_fd);
                return tll_null();
            }
            if (listen(server_fd, 10) < 0) {
                fprintf(stderr, "tllvm: listen failed\n");
                closesocket(server_fd);
                return tll_null();
            }
            fprintf(stderr, "tllvm: HTTP server listening on %s:%d (worker pool, %d threads)\n", host, port, WORKER_POOL_SIZE);
            /* Initialize VM lock and worker pool */
            if (!g_vm_lock_initialized) {
                InitializeCriticalSection(&g_vm_lock);
                g_vm_lock_initialized = 1;
            }
            if (!g_pool_initialized) {
                init_worker_pool();
            }
            /* Accept loop - enqueue task to worker pool.
               Worker pool has fixed WORKER_POOL_SIZE threads, avoiding OS thread explosion.
               VM invocation is serialized by g_vm_lock inside worker thread. */
            while (1) {
                struct sockaddr_in client_addr;
                int client_len = sizeof(client_addr);
                SOCKET client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
                if (client_fd == INVALID_SOCKET) continue;
                HttpTask *task = (HttpTask*)malloc(sizeof(HttpTask));
                task->client_fd = (unsigned int)client_fd;
                task->vm = vm;
                task->handler_fn = args[1];
                enqueue_task(task);
            }
            closesocket(server_fd);
            WSACleanup();
            return tll_null();
        }
#endif /* _WIN32 */
#ifndef _WIN32
        if (idx == 94) { /* http.serve - not supported on Linux/macOS */
            fprintf(stderr, "tllvm: http.serve is not supported on this platform\n");
            return tll_null();
        }
#endif
        if (idx == 95) { /* http.encodeURI */
            const char *s = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
            char *out = (char*)malloc(strlen(s) * 3 + 1);
            int oi = 0;
            for (int i = 0; s[i]; i++) {
                unsigned char c = (unsigned char)s[i];
                if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') {
                    out[oi++] = c;
                } else {
                    oi += snprintf(out + oi, 4, "%%%02X", c);
                }
            }
            out[oi] = '\0';
            TLLValue r = tll_string(out); free(out); return r;
        }
        if (idx == 96) { /* http.decodeURI */
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
            TLLValue r = tll_string(out); free(out); return r;
        }
        if (idx == 97) { /* http.parseJSON */
            const char *s = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
            return tll_parse_json((const char**)&s);
        }
#else
        fprintf(stderr, "tllvm: http builtin %d not available on this platform\n", idx);
        return tll_null();
#endif
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

    /* time (123-126) - P0-3.1 */
    if (idx == 123) { /* time.now() -> int (unix seconds) */
        return tll_int((long long)time(NULL));
    }
    if (idx == 124) { /* time.nowMs() -> int (unix milliseconds) */
        struct timespec ts;
#ifdef _WIN32
        /* Windows: use GetSystemTimeAsFileTime for ms precision */
        FILETIME ft;
        GetSystemTimeAsFileTime(&ft);
        ULARGE_INTEGER uli;
        uli.LowPart = ft.dwLowDateTime;
        uli.HighPart = ft.dwHighDateTime;
        /* FILETIME is 100-ns intervals since 1601-01-01; convert to unix ms */
        long long ms = (long long)(uli.QuadPart / 10000LL) - 11644473600000LL;
        return tll_int(ms);
#else
        clock_gettime(CLOCK_REALTIME, &ts);
        return tll_int((long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
#endif
    }
    if (idx == 125) { /* time.sleep(ms) -> void */
        int ms = (argCount > 0 && args[0].type == TLL_INT) ? (int)args[0].as.integer : 0;
        if (ms > 0) {
#ifdef _WIN32
            Sleep(ms);
#else
            usleep(ms * 1000);
#endif
        }
        return tll_null();
    }
    if (idx == 126) { /* time.date() -> string (YYYY-MM-DD HH:MM:SS) */
        time_t now = time(NULL);
        struct tm *t = localtime(&now);
        char buf[32];
        snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d",
                 t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
                 t->tm_hour, t->tm_min, t->tm_sec);
        return tll_string(buf);
    }

    /* process extensions (127-128, 131) - P0-3.1 */
    if (idx == 127) { /* process.cwd() -> string */
        char buf[4096];
        if (GETCWD(buf, sizeof(buf))) return tll_string(buf);
        return tll_string("");
    }
    if (idx == 128) { /* process.chdir(path) -> void */
        const char *path = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        CHDIR(path);
        return tll_null();
    }
    if (idx == 131) { /* process.platform() -> string */
#ifdef _WIN32
        return tll_string("windows");
#elif __APPLE__
        return tll_string("darwin");
#else
        return tll_string("linux");
#endif
    }

    /* io stderr (129-130) - P0-3.1 */
    if (idx == 129) { /* io.eprint(value) -> void (stderr) */
        if (argCount > 0) { char *s = tll_to_string(args[0]); fputs(s, stderr); free(s); }
        return tll_null();
    }
    if (idx == 130) { /* io.eprintln(value) -> void (stderr) */
        if (argCount > 0) { char *s = tll_to_string(args[0]); fputs(s, stderr); free(s); }
        fputc('\n', stderr);
        return tll_null();
    }

    /* strings.concatMany (132) - P0-15.8-C fix: true O(n) multi-string concat */
    if (idx == 132) { /* strings.concatMany(list_of_strings) -> string */
        if (argCount > 0 && args[0].type == TLL_ARRAY) {
            TLLArray *arr = args[0].as.array;
            int totalLen = 0;
            int i;
            for (i = 0; i < arr->length; i++) {
                if (arr->items[i].type == TLL_STRING) {
                    totalLen += (int)strlen(arr->items[i].as.string);
                }
            }
            char *buf = (char*)malloc(sizeof(int) + totalLen + 1);
            *(int*)buf = 1;
            char *pos = buf + sizeof(int);
            for (i = 0; i < arr->length; i++) {
                if (arr->items[i].type == TLL_STRING) {
                    int len = (int)strlen(arr->items[i].as.string);
                    memcpy(pos, arr->items[i].as.string, len);
                    pos += len;
                }
            }
            *pos = '\0';
            TLLValue v;
            v.type = TLL_STRING;
            v.as.string = buf + sizeof(int);
            return v;
        }
        return tll_string("");
    }

    /* TCP socket API (133-138) - P0-15.10 Multi-Node Blockchain P2P */
    if (idx == 133) { /* tcp.listen(host, port) -> server_fd (int) */
        const char *host = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "0.0.0.0";
        int port = (argCount > 1 && args[1].type == TLL_INT) ? (int)args[1].as.integer : 9000;
#ifdef _WIN32
        static int wsa_init = 0;
        if (!wsa_init) { WSADATA wsa; WSAStartup(MAKEWORD(2,2), &wsa); wsa_init = 1; }
#endif
        SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
        if (s == INVALID_SOCKET) return tll_int(-1);
        int opt = 1;
        setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
        struct sockaddr_in addr;
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = inet_addr(host);
        addr.sin_port = htons((unsigned short)port);
        if (bind(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) { closesocket(s); return tll_int(-1); }
        if (listen(s, 16) < 0) { closesocket(s); return tll_int(-1); }
        return tll_int((long long)s);
    }
    if (idx == 134) { /* tcp.accept(server_fd) -> client_fd (int), blocking */
        if (argCount > 0 && args[0].type == TLL_INT) {
            SOCKET server = (SOCKET)args[0].as.integer;
            struct sockaddr_in client_addr;
            int client_len = sizeof(client_addr);
            SOCKET client = accept(server, (struct sockaddr*)&client_addr, &client_len);
            if (client == INVALID_SOCKET) return tll_int(-1);
            return tll_int((long long)client);
        }
        return tll_int(-1);
    }
    if (idx == 135) { /* tcp.connect(host, port) -> socket_fd (int) */
        const char *host = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "127.0.0.1";
        int port = (argCount > 1 && args[1].type == TLL_INT) ? (int)args[1].as.integer : 9000;
#ifdef _WIN32
        static int wsa_init2 = 0;
        if (!wsa_init2) { WSADATA wsa; WSAStartup(MAKEWORD(2,2), &wsa); wsa_init2 = 1; }
#endif
        SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
        if (s == INVALID_SOCKET) return tll_int(-1);
        struct sockaddr_in addr;
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = inet_addr(host);
        addr.sin_port = htons((unsigned short)port);
        if (connect(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) { closesocket(s); return tll_int(-1); }
        return tll_int((long long)s);
    }
    if (idx == 136) { /* tcp.send(socket_fd, data) -> bytes sent (int) */
        if (argCount > 1 && args[0].type == TLL_INT && args[1].type == TLL_STRING) {
            SOCKET s = (SOCKET)args[0].as.integer;
            const char *data = args[1].as.string;
            int len = (int)strlen(data);
            int sent = send(s, data, len, 0);
            return tll_int(sent);
        }
        return tll_int(-1);
    }
    if (idx == 137) { /* tcp.recv(socket_fd, max_bytes) -> data (string), blocking */
        if (argCount > 0 && args[0].type == TLL_INT) {
            SOCKET s = (SOCKET)args[0].as.integer;
            int maxBytes = (argCount > 1 && args[1].type == TLL_INT) ? (int)args[1].as.integer : 65536;
            char *buf = (char*)malloc(maxBytes + 1);
            int received = recv(s, buf, maxBytes, 0);
            if (received <= 0) { free(buf); return tll_string(""); }
            buf[received] = '\0';
            TLLValue v = tll_string(buf);
            free(buf);
            return v;
        }
        return tll_string("");
    }
    if (idx == 138) { /* tcp.close(socket_fd) -> void */
        if (argCount > 0 && args[0].type == TLL_INT) {
            SOCKET s = (SOCKET)args[0].as.integer;
            closesocket(s);
        }
        return tll_null();
    }
    if (idx == 139) { /* tcp.setTimeout(socket_fd, ms) -> bool */
        if (argCount > 1 && args[0].type == TLL_INT && args[1].type == TLL_INT) {
            SOCKET s = (SOCKET)args[0].as.integer;
            int ms = (int)args[1].as.integer;
#ifdef _WIN32
            DWORD timeout = (DWORD)ms;
            int r1 = setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
            int r2 = setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof(timeout));
            return tll_bool(r1 == 0 && r2 == 0);
#else
            struct timeval tv;
            tv.tv_sec = ms / 1000;
            tv.tv_usec = (ms % 1000) * 1000;
            int r1 = setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
            int r2 = setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
            return tll_bool(r1 == 0 && r2 == 0);
#endif
        }
        return tll_bool(0);
    }
    if (idx == 140) { /* tcp.tryAccept(server_fd, timeout_ms) -> client_fd or -1 */
        if (argCount > 0 && args[0].type == TLL_INT) {
            SOCKET server = (SOCKET)args[0].as.integer;
            int timeoutMs = (argCount > 1 && args[1].type == TLL_INT) ? (int)args[1].as.integer : 0;
            fd_set readfds;
            FD_ZERO(&readfds);
            FD_SET(server, &readfds);
            struct timeval tv;
            tv.tv_sec = timeoutMs / 1000;
            tv.tv_usec = (timeoutMs % 1000) * 1000;
            int ready = select((int)server + 1, &readfds, NULL, NULL, &tv);
            if (ready > 0 && FD_ISSET(server, &readfds)) {
                struct sockaddr_in client_addr;
                int client_len = sizeof(client_addr);
                SOCKET client = accept(server, (struct sockaddr*)&client_addr, &client_len);
                if (client == INVALID_SOCKET) return tll_int(-1);
                return tll_int((long long)client);
            }
            return tll_int(-1);
        }
        return tll_int(-1);
    }
    if (idx == 141) { /* tcp.select(fd_list, timeout_ms) -> list of ready fds */
        if (argCount > 0 && args[0].type == TLL_ARRAY) {
            TLLArray *arr = args[0].as.array;
            int timeoutMs = (argCount > 1 && args[1].type == TLL_INT) ? (int)args[1].as.integer : 100;
            fd_set readfds;
            FD_ZERO(&readfds);
            int maxFd = 0;
            int i;
            int validCount = 0;
            for (i = 0; i < arr->length; i++) {
                if (arr->items[i].type == TLL_INT) {
                    SOCKET s = (SOCKET)arr->items[i].as.integer;
                    if (s > 0) {
                        FD_SET(s, &readfds);
                        if ((int)s > maxFd) maxFd = (int)s;
                        validCount++;
                    }
                }
            }
            TLLValue result = tll_array();
            if (validCount == 0) return result;
            struct timeval tv;
            tv.tv_sec = timeoutMs / 1000;
            tv.tv_usec = (timeoutMs % 1000) * 1000;
            int ready = select(maxFd + 1, &readfds, NULL, NULL, &tv);
            if (ready <= 0) return result;
            for (i = 0; i < arr->length; i++) {
                if (arr->items[i].type == TLL_INT) {
                    SOCKET s = (SOCKET)arr->items[i].as.integer;
                    if (s > 0 && FD_ISSET(s, &readfds)) {
                        TLLValue v;
                        v.type = TLL_INT;
                        v.as.integer = (long long)s;
                        array_push(result.as.array, v);
                    }
                }
            }
            return result;
        }
        return tll_array();
    }

    /* P0-15.16 IO-aware scheduler: non-blocking TCP + channel wake */
    if (idx == 142) { /* tcp.tryRecv(fd, max_bytes) -> string, non-blocking ("" if would block) */
        if (argCount > 0 && args[0].type == TLL_INT) {
            SOCKET s = (SOCKET)args[0].as.integer;
            int maxBytes = (argCount > 1 && args[1].type == TLL_INT) ? (int)args[1].as.integer : 65536;
            /* Check if data is available without blocking */
            fd_set readfds;
            FD_ZERO(&readfds);
            FD_SET(s, &readfds);
            struct timeval tv0;
            tv0.tv_sec = 0;
            tv0.tv_usec = 0;
            int ready = select((int)s + 1, &readfds, NULL, NULL, &tv0);
            if (ready <= 0 || !FD_ISSET(s, &readfds)) {
                return tll_string("");  /* would block or error */
            }
            char *buf = (char*)malloc(maxBytes + 1);
            int received = recv(s, buf, maxBytes, 0);
            if (received <= 0) { free(buf); return tll_string(""); }
            buf[received] = '\0';
            TLLValue v = tll_string(buf);
            free(buf);
            return v;
        }
        return tll_string("");
    }
    if (idx == 143) { /* tcp.trySend(fd, data) -> int bytes sent, -1 if would block */
        if (argCount > 1 && args[0].type == TLL_INT && args[1].type == TLL_STRING) {
            SOCKET s = (SOCKET)args[0].as.integer;
            const char *data = args[1].as.string;
            int len = (int)strlen(data);
            /* Check if socket is writable without blocking */
            fd_set writefds;
            FD_ZERO(&writefds);
            FD_SET(s, &writefds);
            struct timeval tv0;
            tv0.tv_sec = 0;
            tv0.tv_usec = 0;
            int ready = select((int)s + 1, NULL, &writefds, NULL, &tv0);
            if (ready <= 0 || !FD_ISSET(s, &writefds)) {
                return tll_int(-1);  /* would block */
            }
            int sent = send(s, data, len, 0);
            return tll_int(sent);
        }
        return tll_int(-1);
    }
    if (idx == 144) { /* coroutine.wakeChannel(channelMap) -> int number woken */
        if (argCount > 0 && args[0].type == TLL_MAP) {
            void *chPtr = (void*)args[0].as.map;
            int woken = coroutine_wake_channel(vm, chPtr);
            return tll_int(woken);
        }
        return tll_int(0);
    }

    fprintf(stderr, "tllvm: unknown builtin index %d\n", idx);
    return tll_null();
}
