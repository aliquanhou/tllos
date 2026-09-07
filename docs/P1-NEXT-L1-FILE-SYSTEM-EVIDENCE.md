# P1-NEXT L1: File System Gate — Evidence

## Capability
File System stdlib (fs builtin idx 79-90)

## Existing Capability Audit
File System was listed as MISSING in TLL-V1-CAPABILITY-MATRIX.md, but audit revealed it was already IMPLEMENTED in `host/c/builtin.c` (idx 79-90):
- 79: readFile
- 80: writeFile
- 81: appendFile
- 82: exists
- 83: mkdir
- 84: remove
- 85: listDir
- 86: isFile
- 87: isDir
- 88: fileSize
- 89: copyFile
- 90: rename

The compiler (`tools/TLLC/compiler_driver.tll`) already uses fs.readFile/writeFile/exists extensively.

## Bug Discovery
**FS API return values were broken**: writeFile, appendFile, mkdir, remove, copyFile, rename all returned `tll_null()` instead of a boolean success/failure indicator. Callers could not determine if operations succeeded.

### Root Cause
Original implementation ignored return values of fopen/fwrite/mkdir/remove/rename and always returned null.

### Minimal Fix
Modified `host/c/builtin.c` cases 80, 81, 83, 84, 89, 90 to return `tll_bool()` based on actual operation success:
- writeFile: returns true if fwrite wrote all bytes
- appendFile: returns true if fwrite wrote all bytes
- mkdir: returns true if mkdir succeeded or directory already exists (EEXIST)
- remove: returns true if remove() returned 0
- copyFile: returns true if all bytes copied successfully
- rename: returns true if rename() returned 0

Also added `#include <errno.h>` for EEXIST check.

## Test
`tests/fs/gate_file_system.tll` — 25 assertions covering:
- Gate 1: writeFile + readFile roundtrip (2 assertions)
- Gate 2: exists (file exists + nonexistent) (2 assertions)
- Gate 3: appendFile (return value + content) (2 assertions)
- Gate 4: fileSize (1 assertion)
- Gate 5: isFile (file + directory) (2 assertions)
- Gate 6: isDir (directory + file) (2 assertions)
- Gate 7: mkdir + listDir (3 assertions)
- Gate 8: copyFile (return + content) (2 assertions)
- Gate 9: rename (return + original gone + renamed exists + content) (4 assertions)
- Gate 10: remove (return + file gone) (2 assertions)
- Gate 11: error paths (read missing + remove missing + size missing) (3 assertions)

## Gate Result
**25/25 PASS** (Windows local verification)

## Compiler Bootstrap
- Old compiler compiles tools/TLLC/main.tll → new compiler (Constants: 3911, matches original)
- New compiler compiles fs Gate test → runs successfully 25/25 PASS
- Bootstrap: PASS

## Regression
- P1-01 Secure Random: PASS
- P1-02 Password Hashing: 36/36 PASS
- P1-03 HMAC-SHA256: 20/20 PASS
- P1-04 Level 1-4: not re-run (no HTTP code modified)

## CI
Added to `.github/workflows/p1-04-http-client.yml` for all 3 platforms (Ubuntu, Windows, macOS), placed after compiler bootstrap, before HTTP tests.

## Files Modified
- `host/c/builtin.c` — fixed 6 fs functions return values from null to bool
- `tests/fs/gate_file_system.tll` — NEW: 25-assertion Gate test
- `.github/workflows/p1-04-http-client.yml` — added FS test to 3 platforms

## Capability Matrix Correction
File System status corrected from MISSING → COMPLETE (with this Gate test).

## Known Limitations
- fs.stat() (combined size/isDir/mtime map) not implemented; individual fileSize/isFile/isDir exist
- No recursive directory operations (rm -rf, cp -r)
- No file watch/inotify
- No symlink support
- Path separator normalization not handled (TLL code must use platform-appropriate paths)
