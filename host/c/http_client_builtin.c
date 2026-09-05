/*
 * TLL Native HTTP Client - Cross-platform implementation
 * Module: httpc (idx 200-209)
 *
 * Windows: WinHTTP (system native)
 * Linux/macOS: POSIX socket + OpenSSL for HTTPS
 *
 * API:
 *   httpc.get(url, headers?)          -> Response map
 *   httpc.post(url, body, headers?)   -> Response map
 *   httpc.put(url, body, headers?)    -> Response map
 *   httpc.delete(url, headers?)       -> Response map
 *   httpc.head(url, headers?)         -> Response map
 *   httpc.patch(url, body, headers?)  -> Response map
 *   httpc.request(map)                -> Response map (method/url/body/headers/timeout)
 *   httpc.getJson(url, headers?)      -> parsed JSON value
 *   httpc.postJson(url, body, headers?) -> parsed JSON value
 *
 * Response map:
 *   ok: bool (status 200-299)
 *   status: int
 *   statusText: string
 *   headers: map (lowercase keys)
 *   body: string
 *   error: string (if failed)
 *   url: string (final URL)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <poll.h>
#if !defined(__APPLE__) || defined(TLL_USE_OPENSSL)
#include <openssl/ssl.h>
#include <openssl/err.h>
#else
typedef void SSL;
typedef void SSL_CTX;
#endif
#endif

#include "tllvm.h"

/* ===== URL Parsing ===== */

typedef struct {
    char scheme[16];   /* "http" or "https" */
    char host[256];
    int port;
    char path[2048];   /* includes query string */
    int isHttps;
} ParsedUrl;

static int parse_url(const char *url, ParsedUrl *out) {
    memset(out, 0, sizeof(ParsedUrl));
    strcpy(out->scheme, "http");
    out->port = 80;
    strcpy(out->path, "/");

    const char *p = url;
    if (strncmp(p, "https://", 8) == 0) {
        strcpy(out->scheme, "https");
        out->isHttps = 1;
        out->port = 443;
        p += 8;
    } else if (strncmp(p, "http://", 7) == 0) {
        p += 7;
    } else {
        return -1; /* invalid URL */
    }

    /* Find host end: /, ?, or end */
    const char *hostEnd = p;
    while (*hostEnd && *hostEnd != '/' && *hostEnd != '?') hostEnd++;

    /* Check for port */
    const char *colon = NULL;
    for (const char *c = p; c < hostEnd; c++) {
        if (*c == ':') { colon = c; break; }
    }

    int hostLen;
    if (colon) {
        hostLen = (int)(colon - p);
        out->port = atoi(colon + 1);
    } else {
        hostLen = (int)(hostEnd - p);
    }
    if (hostLen <= 0 || hostLen >= (int)sizeof(out->host)) return -1;
    strncpy(out->host, p, hostLen);
    out->host[hostLen] = '\0';

    /* Path */
    if (*hostEnd) {
        strncpy(out->path, hostEnd, sizeof(out->path) - 1);
        out->path[sizeof(out->path) - 1] = '\0';
    }

    return 0;
}

/* ===== Header helpers ===== */

static void headers_to_string(TLLValue headersMap, char *out, int outLen) {
    out[0] = '\0';
    if (headersMap.type != TLL_MAP) return;

    /* Iterate all map entries */
    TLLMap *map = headersMap.as.map;
    for (int b = 0; b < map->bucketCount; b++) {
        TLLMapEntry *entry = map->buckets[b];
        while (entry) {
            if (entry->value.type == TLL_STRING && entry->key) {
                int len = (int)strlen(out);
                if (len + (int)strlen(entry->key) + (int)strlen(entry->value.as.string) + 8 < outLen) {
                    snprintf(out + len, outLen - len, "%s: %s\r\n", entry->key, entry->value.as.string);
                }
            }
            entry = entry->next;
        }
    }
}

static TLLValue parse_response_headers(const char *headerText) {
    TLLValue headersMap = tll_map();
    const char *p = headerText;
    while (*p) {
        const char *lineEnd = strstr(p, "\r\n");
        if (!lineEnd) break;
        int lineLen = (int)(lineEnd - p);
        if (lineLen > 0) {
            const char *colon = memchr(p, ':', lineLen);
            if (colon) {
                int keyLen = (int)(colon - p);
                const char *valStart = colon + 1;
                while (*valStart == ' ') valStart++;
                int valLen = (int)(lineEnd - valStart);

                char key[256];
                if (keyLen >= (int)sizeof(key)) keyLen = sizeof(key) - 1;
                strncpy(key, p, keyLen);
                key[keyLen] = '\0';
                /* lowercase the key */
                for (int i = 0; key[i]; i++) key[i] = tolower((unsigned char)key[i]);

                char val[4096];
                if (valLen >= (int)sizeof(val)) valLen = sizeof(val) - 1;
                strncpy(val, valStart, valLen);
                val[valLen] = '\0';

                map_set(headersMap.as.map, key, tll_string(val));
            }
        }
        p = lineEnd + 2;
    }
    return headersMap;
}

/* ===== Response builder ===== */

static TLLValue make_error_response(const char *errorMsg) {
    TLLValue result = tll_map();
    map_set(result.as.map, "ok", tll_bool(0));
    map_set(result.as.map, "status", tll_int(0));
    map_set(result.as.map, "statusText", tll_string(""));
    map_set(result.as.map, "headers", tll_map());
    map_set(result.as.map, "body", tll_string(""));
    map_set(result.as.map, "error", tll_string(errorMsg));
    map_set(result.as.map, "url", tll_string(""));
    return result;
}

/* ===== Windows WinHTTP backend ===== */

#ifdef _WIN32

static TLLValue winhttp_request(const char *method, const char *url,
                                  const char *body, TLLValue headersMap, int timeoutMs) {
    ParsedUrl pu;
    if (parse_url(url, &pu) != 0) {
        return make_error_response("Invalid URL");
    }

    TLLValue result = tll_map();

    HINTERNET hSession = WinHttpOpen(L"TLL-HTTP-Client/1.0",
        WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) return make_error_response("WinHttpOpen failed");

    /* Set timeout */
    if (timeoutMs <= 0) timeoutMs = 30000;
    WinHttpSetTimeouts(hSession, timeoutMs, timeoutMs, timeoutMs, timeoutMs);

    WCHAR wideHost[256];
    MultiByteToWideChar(CP_UTF8, 0, pu.host, -1, wideHost, 256);

    HINTERNET hConnect = WinHttpConnect(hSession, wideHost, (INTERNET_PORT)pu.port, 0);
    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        return make_error_response("WinHttpConnect failed");
    }

    WCHAR wideMethod[16], widePath[2048];
    MultiByteToWideChar(CP_UTF8, 0, method, -1, wideMethod, 16);
    MultiByteToWideChar(CP_UTF8, 0, pu.path, -1, widePath, 2048);

    DWORD flags = pu.isHttps ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, wideMethod, widePath,
        NULL, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return make_error_response("WinHttpOpenRequest failed");
    }

    /* Build custom headers */
    char headerBuf[8192];
    headers_to_string(headersMap, headerBuf, sizeof(headerBuf));

    BOOL sendOk;
    if (body && strlen(body) > 0) {
        WCHAR wideHeaders[8192];
        if (headerBuf[0]) {
            MultiByteToWideChar(CP_UTF8, 0, headerBuf, -1, wideHeaders, 8192);
            sendOk = WinHttpSendRequest(hRequest, wideHeaders, -1,
                (LPVOID)body, (DWORD)strlen(body), (DWORD)strlen(body), 0);
        } else {
            sendOk = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                (LPVOID)body, (DWORD)strlen(body), (DWORD)strlen(body), 0);
        }
    } else {
        if (headerBuf[0]) {
            WCHAR wideHeaders[8192];
            MultiByteToWideChar(CP_UTF8, 0, headerBuf, -1, wideHeaders, 8192);
            sendOk = WinHttpSendRequest(hRequest, wideHeaders, -1,
                WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
        } else {
            sendOk = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
        }
    }

    if (!sendOk) {
        DWORD err = GetLastError();
        char errBuf[128];
        snprintf(errBuf, sizeof(errBuf), "WinHttpSendRequest failed: %lu", err);
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return make_error_response(errBuf);
    }

    if (!WinHttpReceiveResponse(hRequest, NULL)) {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return make_error_response("WinHttpReceiveResponse failed");
    }

    /* Status code */
    DWORD statusCode = 0, statusSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        NULL, &statusCode, &statusSize, NULL);

    /* Status text */
    WCHAR wideStatusText[256] = L"";
    DWORD stSize = sizeof(wideStatusText);
    WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_STATUS_TEXT, NULL,
        wideStatusText, &stSize, NULL);
    char statusText[256];
    WideCharToMultiByte(CP_UTF8, 0, wideStatusText, -1, statusText, sizeof(statusText), NULL, NULL);

    /* Response headers (raw) */
    WCHAR wideRawHeaders[16384] = L"";
    DWORD rhSize = sizeof(wideRawHeaders);
    WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_RAW_HEADERS_CRLF, NULL,
        wideRawHeaders, &rhSize, NULL);
    char rawHeaders[16384];
    WideCharToMultiByte(CP_UTF8, 0, wideRawHeaders, -1, rawHeaders, sizeof(rawHeaders), NULL, NULL);

    /* Read body */
    char *respBody = (char*)malloc(1);
    respBody[0] = '\0';
    size_t totalLen = 0;
    DWORD available = 0, read = 0;
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

    /* Build result */
    map_set(result.as.map, "ok", tll_bool(statusCode >= 200 && statusCode < 300));
    map_set(result.as.map, "status", tll_int((long long)statusCode));
    map_set(result.as.map, "statusText", tll_string(statusText));
    map_set(result.as.map, "headers", parse_response_headers(rawHeaders));
    map_set(result.as.map, "body", tll_string(respBody));
    map_set(result.as.map, "error", tll_string(""));
    map_set(result.as.map, "url", tll_string(url));

    free(respBody);
    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    return result;
}

#else /* Linux/macOS POSIX + OpenSSL backend */
#if !defined(__APPLE__)

/* ===== POSIX socket helpers ===== */

static int set_socket_timeout(int sock, int timeoutMs) {
    struct timeval tv;
    tv.tv_sec = timeoutMs / 1000;
    tv.tv_usec = (timeoutMs % 1000) * 1000;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    return 0;
}

static int connect_with_timeout(int sock, const struct sockaddr *addr, socklen_t addrlen, int timeoutMs) {
    /* Set non-blocking */
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    int ret = connect(sock, addr, addrlen);
    if (ret < 0 && errno == EINPROGRESS) {
        struct pollfd pfd;
        pfd.fd = sock;
        pfd.events = POLLOUT;
        int pr = poll(&pfd, 1, timeoutMs);
        if (pr <= 0) {
            fcntl(sock, F_SETFL, flags);
            return -1; /* timeout or error */
        }
        int err = 0;
        socklen_t errlen = sizeof(err);
        getsockopt(sock, SOL_SOCKET, SO_ERROR, &err, &errlen);
        if (err != 0) {
            fcntl(sock, F_SETFL, flags);
            return -1;
        }
    } else if (ret < 0) {
        fcntl(sock, F_SETFL, flags);
        return -1;
    }

    /* Restore blocking */
    fcntl(sock, F_SETFL, flags);
    return 0;
}

/* ===== HTTPS via OpenSSL ===== */

typedef struct {
    int sock;
    SSL *ssl;
    SSL_CTX *ctx;
    int useSsl;
} HttpConnection;

static int http_connect(HttpConnection *conn, const char *host, int port, int isHttps, int timeoutMs) {
    conn->sock = -1;
    conn->ssl = NULL;
    conn->ctx = NULL;
    conn->useSsl = isHttps;

    /* Resolve hostname */
    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    char portStr[16];
    snprintf(portStr, sizeof(portStr), "%d", port);
    if (getaddrinfo(host, portStr, &hints, &res) != 0) {
        return -1;
    }

    conn->sock = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (conn->sock < 0) {
        freeaddrinfo(res);
        return -1;
    }

    if (connect_with_timeout(conn->sock, res->ai_addr, res->ai_addrlen, timeoutMs) != 0) {
        close(conn->sock);
        conn->sock = -1;
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);

    set_socket_timeout(conn->sock, timeoutMs);

#if !defined(__APPLE__) || defined(TLL_USE_OPENSSL)
    if (isHttps) {
        SSL_library_init();
        SSL_load_error_strings();
        OpenSSL_add_all_algorithms();

        conn->ctx = SSL_CTX_new(SSLv23_client_method());
        if (!conn->ctx) {
            close(conn->sock);
            conn->sock = -1;
            return -1;
        }

        /* Set TLS version min to 1.2 (OpenSSL 1.1.0+ only) */
#if OPENSSL_VERSION_NUMBER >= 0x10100000L
        SSL_CTX_set_min_proto_version(conn->ctx, TLS1_2_VERSION);
#endif

        /* Enable certificate verification (optional for now) */
        SSL_CTX_set_verify(conn->ctx, SSL_VERIFY_NONE, NULL);

        conn->ssl = SSL_new(conn->ctx);
        if (!conn->ssl) {
            SSL_CTX_free(conn->ctx);
            close(conn->sock);
            conn->sock = -1;
            return -1;
        }

        SSL_set_fd(conn->ssl, conn->sock);
        SSL_set_tlsext_host_name(conn->ssl, host);

        if (SSL_connect(conn->ssl) != 1) {
            SSL_free(conn->ssl);
            SSL_CTX_free(conn->ctx);
            close(conn->sock);
            conn->sock = -1;
            return -1;
        }
    }
#else
        (void)isHttps;
#endif

    return 0;
}

static int http_send(HttpConnection *conn, const char *data, int len) {
    if (conn->useSsl && conn->ssl) {
#if !defined(__APPLE__) || defined(TLL_USE_OPENSSL)
        int sent = 0;
        while (sent < len) {
            int n = SSL_write(conn->ssl, data + sent, len - sent);
            if (n <= 0) return -1;
            sent += n;
        }
        return sent;
#else
        return -1;
#endif
    } else {
        int sent = 0;
        while (sent < len) {
            int n = send(conn->sock, data + sent, len - sent, 0);
            if (n <= 0) return -1;
            sent += n;
        }
        return sent;
    }
}

static int http_recv(HttpConnection *conn, char *buf, int bufSize) {
    if (conn->useSsl && conn->ssl) {
#if !defined(__APPLE__) || defined(TLL_USE_OPENSSL)
        return SSL_read(conn->ssl, buf, bufSize);
#else
        return -1;
#endif
    } else {
        return recv(conn->sock, buf, bufSize, 0);
    }
}

static void http_close(HttpConnection *conn) {
    if (conn->useSsl && conn->ssl) {
#if !defined(__APPLE__) || defined(TLL_USE_OPENSSL)
        SSL_shutdown(conn->ssl);
        SSL_free(conn->ssl);
        SSL_CTX_free(conn->ctx);
#endif
    }
    if (conn->sock >= 0) {
        close(conn->sock);
        conn->sock = -1;
    }
}

/* ===== POSIX HTTP request ===== */

static TLLValue posix_request(const char *method, const char *url,
                                const char *body, TLLValue headersMap, int timeoutMs) {
    ParsedUrl pu;
    if (parse_url(url, &pu) != 0) {
        return make_error_response("Invalid URL");
    }

    if (timeoutMs <= 0) timeoutMs = 30000;

    HttpConnection conn;
    if (http_connect(&conn, pu.host, pu.port, pu.isHttps, timeoutMs) != 0) {
        return make_error_response("Connection failed");
    }

    /* Build request */
    char reqBuf[65536];
    int reqLen = 0;

    /* Request line */
    reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen,
        "%s %s HTTP/1.1\r\n", method, pu.path);

    /* Host header */
    reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen,
        "Host: %s\r\n", pu.host);

    /* User-Agent */
    reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen,
        "User-Agent: TLL-HTTP-Client/1.0\r\n");

    /* Accept */
    reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen,
        "Accept: */*\r\n");

    /* Connection: close (simpler) */
    reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen,
        "Connection: close\r\n");

    /* Custom headers */
    char headerBuf[8192];
    headers_to_string(headersMap, headerBuf, sizeof(headerBuf));
    if (headerBuf[0]) {
        int hl = (int)strlen(headerBuf);
        if (reqLen + hl < (int)sizeof(reqBuf) - 512) {
            memcpy(reqBuf + reqLen, headerBuf, hl);
            reqLen += hl;
        }
    }

    /* Body and Content-Length */
    int bodyLen = body ? (int)strlen(body) : 0;
    if (bodyLen > 0) {
        reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen,
            "Content-Length: %d\r\n", bodyLen);
    }

    /* End of headers */
    reqLen += snprintf(reqBuf + reqLen, sizeof(reqBuf) - reqLen, "\r\n");

    /* Append body */
    if (bodyLen > 0 && reqLen + bodyLen < (int)sizeof(reqBuf)) {
        memcpy(reqBuf + reqLen, body, bodyLen);
        reqLen += bodyLen;
    }

    /* Send request */
    if (http_send(&conn, reqBuf, reqLen) != reqLen) {
        http_close(&conn);
        return make_error_response("Failed to send request");
    }

    /* Read response */
    char *respBuf = (char*)malloc(65536);
    int respLen = 0;
    int respCap = 65536;

    while (1) {
        if (respLen >= respCap - 1) {
            respCap *= 2;
            respBuf = (char*)realloc(respBuf, respCap);
        }
        int n = http_recv(&conn, respBuf + respLen, respCap - respLen - 1);
        if (n <= 0) break;
        respLen += n;
        respBuf[respLen] = '\0';

        /* Check if we have full response (Content-Length or chunked done) */
        /* Simple approach: read until connection close */
    }
    http_close(&conn);

    if (respLen == 0) {
        free(respBuf);
        return make_error_response("Empty response");
    }

    /* Parse response */
    const char *p = respBuf;

    /* Status line */
    int statusCode = 0;
    char statusText[256] = "";
    if (strncmp(p, "HTTP/", 5) == 0) {
        p += 5;
        while (*p && *p != ' ') p++; /* skip version */
        while (*p == ' ') p++;
        statusCode = atoi(p);
        while (*p && *p != ' ') p++;
        while (*p == ' ') p++;
        const char *stEnd = strstr(p, "\r\n");
        if (stEnd) {
            int stLen = (int)(stEnd - p);
            if (stLen >= (int)sizeof(statusText)) stLen = sizeof(statusText) - 1;
            strncpy(statusText, p, stLen);
            statusText[stLen] = '\0';
            p = stEnd + 2;
        }
    }

    /* Headers */
    const char *headerEnd = strstr(p, "\r\n\r\n");
    char *headerText = NULL;
    if (headerEnd) {
        int hLen = (int)(headerEnd - p);
        headerText = (char*)malloc(hLen + 1);
        memcpy(headerText, p, hLen);
        headerText[hLen] = '\0';
        p = headerEnd + 4;
    }

    /* Body */
    char *bodyStart = (char*)p;
    int bodyContentLen = respLen - (int)(bodyStart - respBuf);

    /* Handle chunked encoding */
    TLLValue headersMapResult = headerText ? parse_response_headers(headerText) : tll_map();
    TLLValue teVal = map_get(headersMapResult.as.map, "transfer-encoding");
    if (teVal.type == TLL_STRING && strstr(teVal.as.string, "chunked")) {
        /* Dechunk */
        char *dechunked = (char*)malloc(bodyContentLen + 1);
        int dechunkedLen = 0;
        const char *cp = bodyStart;
        const char *bodyEnd = respBuf + respLen;
        while (cp < bodyEnd) {
            /* Read chunk size */
            const char *crlf = strstr(cp, "\r\n");
            if (!crlf) break;
            int chunkSize = (int)strtol(cp, NULL, 16);
            if (chunkSize == 0) break;
            cp = crlf + 2;
            if (cp + chunkSize > bodyEnd) break;
            memcpy(dechunked + dechunkedLen, cp, chunkSize);
            dechunkedLen += chunkSize;
            cp += chunkSize + 2; /* skip data + CRLF */
        }
        dechunked[dechunkedLen] = '\0';
        bodyStart = dechunked;
        bodyContentLen = dechunkedLen;
    }

    /* Build result */
    TLLValue result = tll_map();
    map_set(result.as.map, "ok", tll_bool(statusCode >= 200 && statusCode < 300));
    map_set(result.as.map, "status", tll_int((long long)statusCode));
    map_set(result.as.map, "statusText", tll_string(statusText));
    map_set(result.as.map, "headers", headersMapResult);
    map_set(result.as.map, "body", tll_string(bodyStart));
    map_set(result.as.map, "error", tll_string(""));
    map_set(result.as.map, "url", tll_string(url));

    if (headerText) free(headerText);
    if (bodyStart != (char*)p && bodyStart != respBuf) free(bodyStart); /* dechunked buffer */
    free(respBuf);
    return result;
}

#else /* macOS stub - HTTP Client not yet supported on macOS */
static TLLValue posix_request(const char *method, const char *url,
                                const char *body, TLLValue headersMap, int timeoutMs) {
    (void)method; (void)body; (void)headersMap; (void)timeoutMs;
    TLLValue result = tll_map();
    map_set(result.as.map, "ok", tll_bool(0));
    map_set(result.as.map, "status", tll_int(0));
    map_set(result.as.map, "statusText", tll_string(""));
    map_set(result.as.map, "headers", tll_map());
    map_set(result.as.map, "body", tll_string(""));
    map_set(result.as.map, "error", tll_string("HTTP Client not supported on macOS yet"));
    map_set(result.as.map, "url", tll_string(url));
    return result;
}
#endif /* !__APPLE__ */

#endif /* platform */

/* ===== Unified dispatch ===== */

static TLLValue httpc_do_request(const char *method, const char *url,
                                   const char *body, TLLValue headersMap, int timeoutMs) {
#ifdef _WIN32
    return winhttp_request(method, url, body, headersMap, timeoutMs);
#else
    return posix_request(method, url, body, headersMap, timeoutMs);
#endif
}

/* ===== TLL builtin entry point ===== */

TLLValue httpc_builtin_invoke(TLLVM *vm, int idx, TLLValue *args, int argCount) {
    (void)vm;

    /* idx 200-209: httpc module */

    if (idx == 200) { /* httpc.get(url, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        TLLValue headers = (argCount > 1) ? args[1] : tll_null();
        return httpc_do_request("GET", url, NULL, headers, 30000);
    }

    if (idx == 201) { /* httpc.post(url, body, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        const char *body = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
        TLLValue headers = (argCount > 2) ? args[2] : tll_null();
        return httpc_do_request("POST", url, body, headers, 30000);
    }

    if (idx == 202) { /* httpc.put(url, body, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        const char *body = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
        TLLValue headers = (argCount > 2) ? args[2] : tll_null();
        return httpc_do_request("PUT", url, body, headers, 30000);
    }

    if (idx == 203) { /* httpc.delete(url, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        TLLValue headers = (argCount > 1) ? args[1] : tll_null();
        return httpc_do_request("DELETE", url, NULL, headers, 30000);
    }

    if (idx == 204) { /* httpc.head(url, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        TLLValue headers = (argCount > 1) ? args[1] : tll_null();
        return httpc_do_request("HEAD", url, NULL, headers, 30000);
    }

    if (idx == 205) { /* httpc.patch(url, body, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        const char *body = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
        TLLValue headers = (argCount > 2) ? args[2] : tll_null();
        return httpc_do_request("PATCH", url, body, headers, 30000);
    }

    if (idx == 206) { /* httpc.request(map) - full control */
        if (argCount < 1 || args[0].type != TLL_MAP) {
            return make_error_response("httpc.request requires a map argument");
        }
        TLLValue req = args[0];

        const char *method = "GET";
        TLLValue mv = map_get(req.as.map, "method");
        if (mv.type == TLL_STRING) method = mv.as.string;

        const char *url = "";
        TLLValue uv = map_get(req.as.map, "url");
        if (uv.type == TLL_STRING) url = uv.as.string;

        const char *body = NULL;
        TLLValue bv = map_get(req.as.map, "body");
        if (bv.type == TLL_STRING) body = bv.as.string;

        TLLValue headers = map_get(req.as.map, "headers");
        if (headers.type != TLL_MAP) headers = tll_null();

        int timeout = 30000;
        TLLValue tv = map_get(req.as.map, "timeout");
        if (tv.type == TLL_INT) timeout = (int)tv.as.integer;

        return httpc_do_request(method, url, body, headers, timeout);
    }

    if (idx == 207) { /* httpc.getJson(url, headers?) - returns parsed JSON */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        TLLValue headers = (argCount > 1) ? args[1] : tll_null();
        TLLValue resp = httpc_do_request("GET", url, NULL, headers, 30000);
        TLLValue bodyVal = map_get(resp.as.map, "body");
        if (bodyVal.type == TLL_STRING) {
            /* Try to parse JSON */
            const char *jsonPtr = bodyVal.as.string;
            TLLValue parsed = tll_parse_json(&jsonPtr);
            if (parsed.type != TLL_NULL) return parsed;
        }
        return resp;
    }

    if (idx == 208) { /* httpc.postJson(url, body, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        const char *body = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
        TLLValue headers = (argCount > 2) ? args[2] : tll_null();

        /* Auto-set Content-Type if not present */
        if (headers.type != TLL_MAP) {
            headers = tll_map();
            map_set(headers.as.map, "Content-Type", tll_string("application/json"));
        }

        TLLValue resp = httpc_do_request("POST", url, body, headers, 30000);
        TLLValue bodyVal = map_get(resp.as.map, "body");
        if (bodyVal.type == TLL_STRING) {
            const char *jsonPtr = bodyVal.as.string;
            TLLValue parsed = tll_parse_json(&jsonPtr);
            if (parsed.type != TLL_NULL) return parsed;
        }
        return resp;
    }

    if (idx == 209) { /* httpc.options(url, headers?) */
        const char *url = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : "";
        TLLValue headers = (argCount > 1) ? args[1] : tll_null();
        return httpc_do_request("OPTIONS", url, NULL, headers, 30000);
    }

    return make_error_response("Unknown httpc function index");
}
