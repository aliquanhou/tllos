/*
 * TLL SQLite Builtin Binding
 * Provides sqlite.* builtin functions for TLL programs.
 *
 * Builtin index range: 100-119
 *   100: sqlite.open(path)       -> db handle (map)
 *   101: sqlite.close(db)         -> null
 *   102: sqlite.exec(db, sql)     -> int (changes count)
 *   103: sqlite.query(db, sql)    -> array of maps (rows)
 *   104: sqlite.lastInsertRowid(db) -> int
 *   105: sqlite.changes(db)       -> int
 *   106: sqlite.version()         -> string
 *   107: sqlite.tableExists(db, name) -> bool
 *   108: sqlite.columns(db, table) -> array of strings
 */

#include "tllvm.h"
#include "sqlite3.h"
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
/* Global mutex to serialize all SQLite access across HTTP worker threads */
static CRITICAL_SECTION g_sqlite_mutex;
static int g_sqlite_mutex_inited = 0;

static void sqlite_lock(void) {
    if (!g_sqlite_mutex_inited) {
        InitializeCriticalSection(&g_sqlite_mutex);
        g_sqlite_mutex_inited = 1;
    }
    EnterCriticalSection(&g_sqlite_mutex);
}

static void sqlite_unlock(void) {
    if (g_sqlite_mutex_inited) {
        LeaveCriticalSection(&g_sqlite_mutex);
    }
}
#else
#include <pthread.h>
/* Global mutex to serialize all SQLite access across HTTP worker threads */
static pthread_mutex_t g_sqlite_mutex = PTHREAD_MUTEX_INITIALIZER;

static void sqlite_lock(void) {
    pthread_mutex_lock(&g_sqlite_mutex);
}

static void sqlite_unlock(void) {
    pthread_mutex_unlock(&g_sqlite_mutex);
}
#endif

/* Store sqlite3* as integer in a TLL map under "__sqlite_db" */
static sqlite3 *get_db(TLLValue v) {
    if (v.type != TLL_MAP) return NULL;
    TLLValue ptr = map_get(v.as.map, "__sqlite_db");
    if (ptr.type != TLL_INT) return NULL;
    return (sqlite3 *)(intptr_t)ptr.as.integer;
}

static TLLValue make_db_handle(sqlite3 *db) {
    TLLValue m = tll_map();
    map_set(m.as.map, "__sqlite_db", tll_int((long long)(intptr_t)db));
    return m;
}

TLLValue sqlite_builtin_invoke(TLLVM *vm, int idx, TLLValue *args, int argCount) {
    sqlite_lock();
    TLLValue result = tll_null();
    switch (idx) {
        case 150: { /* sqlite.open(path) */
            const char *path = (argCount > 0 && args[0].type == TLL_STRING) ? args[0].as.string : ":memory:";
            sqlite3 *db = NULL;
            int rc = sqlite3_open(path, &db);
            if (rc != SQLITE_OK) {
                const char *err = db ? sqlite3_errmsg(db) : "cannot open";
                TLLValue m = tll_map();
                map_set(m.as.map, "error", tll_string(err));
                map_set(m.as.map, "__sqlite_db", tll_int(0));
                if (db) sqlite3_close(db);
                result = m;
                goto cleanup;
            }
            sqlite3_exec(db, "PRAGMA journal_mode=WAL;", NULL, NULL, NULL);
            sqlite3_exec(db, "PRAGMA foreign_keys=ON;", NULL, NULL, NULL);
            result = make_db_handle(db);
            goto cleanup;
        }
        case 151: { /* sqlite.close(db) */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            if (db) sqlite3_close(db);
            result = tll_null();
            goto cleanup;
        }
        case 152: { /* sqlite.exec(db, sql) -> changes count */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            const char *sql = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
            if (!db || !sql) { result = tll_int(0); goto cleanup; }
            char *err = NULL;
            int rc = sqlite3_exec(db, sql, NULL, NULL, &err);
            if (rc != SQLITE_OK && err) {
                fprintf(stderr, "tll sqlite exec error: %s\n", err);
                sqlite3_free(err);
                result = tll_int(-1);
                goto cleanup;
            }
            result = tll_int(sqlite3_changes(db));
            goto cleanup;
        }
        case 153: { /* sqlite.query(db, sql) -> array of maps */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            const char *sql = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
            TLLValue rows = tll_array();
            if (!db || !sql) { result = rows; goto cleanup; }

            sqlite3_stmt *stmt = NULL;
            int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
            if (rc != SQLITE_OK) {
                fprintf(stderr, "tll sqlite query error: %s\n", sqlite3_errmsg(db));
                result = rows;
                goto cleanup;
            }

            int colCount = sqlite3_column_count(stmt);
            while (sqlite3_step(stmt) == SQLITE_ROW) {
                TLLValue row = tll_map();
                for (int i = 0; i < colCount; i++) {
                    const char *colName = sqlite3_column_name(stmt, i);
                    int colType = sqlite3_column_type(stmt, i);
                    TLLValue val;
                    switch (colType) {
                        case SQLITE_INTEGER:
                            val = tll_int(sqlite3_column_int64(stmt, i));
                            break;
                        case SQLITE_FLOAT:
                            val = tll_float(sqlite3_column_double(stmt, i));
                            break;
                        case SQLITE_NULL:
                            val = tll_null();
                            break;
                        case SQLITE_TEXT:
                        default: {
                            const unsigned char *text = sqlite3_column_text(stmt, i);
                            val = text ? tll_string((const char *)text) : tll_null();
                            break;
                        }
                    }
                    map_set(row.as.map, colName, val);
                }
                array_push(rows.as.array, row);
            }
            sqlite3_finalize(stmt);
            result = rows;
            goto cleanup;
        }
        case 154: { /* sqlite.lastInsertRowid(db) */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            if (!db) { result = tll_int(0); goto cleanup; }
            result = tll_int((long long)sqlite3_last_insert_rowid(db));
            goto cleanup;
        }
        case 155: { /* sqlite.changes(db) */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            if (!db) { result = tll_int(0); goto cleanup; }
            result = tll_int(sqlite3_changes(db));
            goto cleanup;
        }
        case 156: { /* sqlite.version() */
            result = tll_string(sqlite3_version);
            goto cleanup;
        }
        case 157: { /* sqlite.tableExists(db, name) */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            const char *name = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
            if (!db || !name) { result = tll_bool(0); goto cleanup; }
            sqlite3_stmt *stmt = NULL;
            int rc = sqlite3_prepare_v2(db, "SELECT name FROM sqlite_master WHERE type='table' AND name=?1", -1, &stmt, NULL);
            if (rc != SQLITE_OK) { result = tll_bool(0); goto cleanup; }
            sqlite3_bind_text(stmt, 1, name, -1, SQLITE_TRANSIENT);
            int exists = (sqlite3_step(stmt) == SQLITE_ROW);
            sqlite3_finalize(stmt);
            result = tll_bool(exists);
            goto cleanup;
        }
        case 158: { /* sqlite.columns(db, table) -> array of strings */
            sqlite3 *db = get_db(argCount > 0 ? args[0] : tll_null());
            const char *table = (argCount > 1 && args[1].type == TLL_STRING) ? args[1].as.string : "";
            TLLValue cols = tll_array();
            if (!db || !table) { result = cols; goto cleanup; }
            char sql[512];
            snprintf(sql, sizeof(sql), "PRAGMA table_info(%s)", table);
            sqlite3_stmt *stmt = NULL;
            if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) == SQLITE_OK) {
                while (sqlite3_step(stmt) == SQLITE_ROW) {
                    const unsigned char *cname = sqlite3_column_text(stmt, 1);
                    if (cname) array_push(cols.as.array, tll_string((const char *)cname));
                }
                sqlite3_finalize(stmt);
            }
            result = cols;
            goto cleanup;
        }
        default:
            fprintf(stderr, "tll sqlite: unknown builtin index %d\n", idx);
            result = tll_null();
            goto cleanup;
    }
cleanup:
    sqlite_unlock();
    return result;
}

