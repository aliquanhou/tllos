# P1-NEXT L3: Database Abstraction — Evidence

## Capability
Database Abstraction stdlib (stdlib/db.tll), extracted from mall/core/database.tll

## Existing Capability Audit
Database Abstraction was listed as PARTIAL in TLL-V1-CAPABILITY-MATRIX.md ("in mall/, not abstracted to stdlib"). Database Migration was listed as MISSING. Audit revealed:
- `mall/core/database.tll` (7180 bytes) already contained complete database abstraction: connection management, parameterized queries, transactions, migrations, utilities
- SQLite builtin (idx 150-159) already SEALED
- No stdlib-level database module existed
- **Critical Bug discovered**: `db_buildSQL()` type check used `"list"` but `convert.typeOf([])` returns `"array"`, causing parameterized queries to NEVER replace `?` placeholders. This bug existed in mall/core/database.tll and affected all parameterized queries.

## Bug Discovery
**db_buildSQL parameter replacement never worked**: Type check `convert.typeOf(params) != "list"` always evaluated true because TLL arrays have type `"array"`, not `"list"`. This meant all `?` placeholders in SQL queries were left unreplaced, potentially causing SQL syntax errors or silent failures.

### Root Cause
Incorrect type string in `db_buildSQL()` function. TLL's `convert.typeOf()` returns `"array"` for list/array literals, not `"list"`.

### Minimal Fix
Changed `"list"` to `"array"` in both `stdlib/db.tll` and `mall/core/database.tll`:
```
// Before (broken):
if (convert.typeOf(params) != "list") { return sql }
// After (fixed):
if (convert.typeOf(params) != "array") { return sql }
```

## Test
`tests/db/gate_database.tll` — 20 assertions covering 11 gates:
- Gate 1: db_open / db_close (1 assertion)
- Gate 2: CREATE TABLE + INSERT with rowids (2 assertions)
- Gate 3: db_query / db_queryOne with parameters (4 assertions)
- Gate 4: UPDATE / DELETE with parameters (2 assertions)
- Gate 5: Transaction commit (1 assertion)
- Gate 6: Transaction rollback (1 assertion)
- Gate 7: db_transaction auto-commit (1 assertion)
- Gate 8: db_transaction auto-rollback (1 assertion)
- Gate 9: SQL Injection protection (2 assertions)
- Gate 10: Migration (create table, apply, skip, migrate multiple) (4 assertions)
- Gate 11: db_stats (1 assertion)

## Gate Result
**20/20 PASS** (Windows local verification)

## Compiler Bootstrap
Not modified (no compiler changes).

## Regression
- P1-01 Secure Random: PASS (L1 verification)
- P1-02 Password Hashing: 36/36 PASS (L1 verification)
- P1-03 HMAC-SHA256: 20/20 PASS (L1 verification)
- P1-04 Level 1-4: not re-run (no HTTP code modified)
- File System L1: 25/25 PASS
- HTTP Server L2: 19/19 PASS
- mall/core/database.tll: fixed same bug, mall should now have working parameterized queries

## CI
Added to `.github/workflows/p1-04-http-client.yml` for all 3 platforms (Ubuntu, Windows, macOS), placed after HTTP Server test.

## Files Added
- `stdlib/db.tll` — Database abstraction stdlib (NEW, extracted from mall)
- `tests/db/gate_database.tll` — 20-assertion Gate test (NEW)

## Files Modified
- `mall/core/database.tll` — fixed db_buildSQL type check bug ("list" → "array")
- `.github/workflows/p1-04-http-client.yml` — added Database test to 3 platforms

## Capability Matrix Corrections
- Database Abstraction: PARTIAL → COMPLETE (stdlib/db.tll + Gate test)
- Database Migration: MISSING → COMPLETE (db_ensureMigrationsTable, db_applyMigration, db_migrate + Gate test)
- SQL Injection Protection: now verified working (parameterized queries + Gate test)

## Known Limitations
- Only SQLite backend (no MySQL/PostgreSQL)
- No connection pool (each db_get opens new connection)
- No async/non-blocking queries
- No prepared statement caching (SQL is rebuilt each call)
- db_queryValue function removed from stdlib (was broken in mall version)
- No ORM / query builder
- No database-level encryption
