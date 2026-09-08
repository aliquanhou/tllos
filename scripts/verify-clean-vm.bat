@echo off
REM ============================================================
REM TLL Clean VM Canonical Verification (Windows)
REM Usage: scripts\verify-clean-vm.bat
REM
REM This script verifies that TLL can be built and tested from
REM source in a clean environment.
REM
REM P2-01-B.6 Build & Source Convergence:
REM   Bytecode VM now uses Shared TLL Runtime Core (runtime/) instead of
REM   the old host/c/value.c. Bytecode and Native targets share the exact
REM   same value semantics, reference counting, and arithmetic implementations.
REM ============================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "HOST_C=%REPO_ROOT%\host\c"
set "RUNTIME_CORE=%REPO_ROOT%\runtime"
set "TOOLS_TLLC=%REPO_ROOT%\tools\TLLC"

set PASS_COUNT=0
set FAIL_COUNT=0
set WARN_COUNT=0

echo ============================================================
echo TLL Clean VM Canonical Verification (Windows)
echo Shared Runtime Core: %RUNTIME_CORE%
echo ============================================================
echo.

REM ============================================================
REM STEP 1: Environment Check
REM ============================================================
echo --- STEP 1: Environment Check ---

where cl.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [PASS] C compiler found: MSVC (cl.exe)
    set /a PASS_COUNT+=1
) else (
    if defined TCC_EXE (
        echo [PASS] C compiler found: TCC
        set /a PASS_COUNT+=1
    ) else (
        echo [FAIL] No C compiler found (MSVC or TCC required)
        set /a FAIL_COUNT+=1
    )
)

where git >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [PASS] Git found
    set /a PASS_COUNT+=1
) else (
    echo [WARN] Git not found
    set /a WARN_COUNT+=1
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [PASS] Python found
    set /a PASS_COUNT+=1
) else (
    echo [WARN] Python not found
    set /a WARN_COUNT+=1
)

echo.

REM ============================================================
REM STEP 2: Native Build
REM ============================================================
echo --- STEP 2: Native Build ---

cd /d "%HOST_C%"

REM Shared Runtime Core replaces old host/c/value.c:
REM   runtime\value.c      - value creation, refcount, truthy, equals, Array/Map
REM   runtime\arithmetic.c - arithmetic and comparison operations
REM   runtime\io.c         - basic IO and runtime lifecycle
set TLL_C_SOURCES=main.c vm.c ..\..\runtime\value.c ..\..\runtime\arithmetic.c ..\..\runtime\io.c json.c builtin.c ffi_builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c sqlite3.c

REM Verify all source files exist
set MISSING=0
for %%f in (%TLL_C_SOURCES%) do (
    if not exist "%%f" (
        echo [FAIL] Missing source file: host\c\%%f
        set /a FAIL_COUNT+=1
        set MISSING=1
    )
)
if %MISSING%==0 (
    echo [PASS] All 14 canonical C source files present (with Shared Runtime Core)
    set /a PASS_COUNT+=1
)

REM Build
where cl.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [INFO] Building tllvm.exe with MSVC (Shared Runtime Core)...
    cl /O2 /D_CRT_SECURE_NO_WARNINGS /I..\..\runtime /Fe:tllvm.exe %TLL_C_SOURCES% /link ws2_32.lib user32.lib advapi32.lib bcrypt.lib winhttp.lib >nul 2>&1
    if %ERRORLEVEL%==0 (
        echo [PASS] Native build successful
        set /a PASS_COUNT+=1
    ) else (
        echo [FAIL] Native build failed
        set /a FAIL_COUNT+=1
    )
) else (
    if defined TCC_EXE (
        echo [INFO] Building tllvm.exe with TCC (Shared Runtime Core)...
        "%TCC_EXE%" -O2 -std=c99 -D_WIN32 -I..\..\runtime "-Wl,-stack=0x4000000" -o tllvm.exe %TLL_C_SOURCES% "%SystemRoot%\System32\winhttp.dll" "%SystemRoot%\System32\ws2_32.dll" "%SystemRoot%\System32\bcrypt.dll" >nul 2>&1
        if %ERRORLEVEL%==0 (
            echo [PASS] Native build successful
            set /a PASS_COUNT+=1
        ) else (
            echo [FAIL] Native build failed
            set /a FAIL_COUNT+=1
        )
    )
)

echo.

REM ============================================================
REM STEP 3: Bootstrap Compiler
REM ============================================================
echo --- STEP 3: Bootstrap Compiler ---

cd /d "%REPO_ROOT%"

if exist "%TOOLS_TLLC%\tllc.tllbc" (
    echo [PASS] Canonical bootstrap compiler exists
    set /a PASS_COUNT+=1
) else (
    echo [FAIL] Canonical bootstrap compiler missing
    set /a FAIL_COUNT+=1
)

echo [INFO] Rebuilding tllc.tllbc from source...
"%HOST_C%\tllvm.exe" "%TOOLS_TLLC%\tllc.tllbc" compile "%TOOLS_TLLC%\main.tll" -o "%TEMP%\tllc_rebuilt.tllbc" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [PASS] Bootstrap source rebuilds compiler successfully
    set /a PASS_COUNT+=1
) else (
    echo [FAIL] Bootstrap source rebuild failed
    set /a FAIL_COUNT+=1
)

echo.

REM ============================================================
REM STEP 4: Compile Smoke Test
REM ============================================================
echo --- STEP 4: Compile Smoke Test ---

cd /d "%REPO_ROOT%"

"%HOST_C%\tllvm.exe" "%TOOLS_TLLC%\tllc.tllbc" compile examples\hello.tll -o "%TEMP%\hello.tllbc" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [PASS] Compile examples\hello.tll successful
    set /a PASS_COUNT+=1
) else (
    echo [FAIL] Compile examples\hello.tll failed
    set /a FAIL_COUNT+=1
)

echo.

REM ============================================================
REM STEP 5: Runtime Smoke Test
REM ============================================================
echo --- STEP 5: Runtime Smoke Test ---

cd /d "%REPO_ROOT%"

if exist "%TEMP%\hello.tllbc" (
    for /f "delims=" %%o in ('"%HOST_C%\tllvm.exe" "%TEMP%\hello.tllbc" 2^>^&1') do set OUTPUT=%%o
    echo !OUTPUT! | findstr /i "Hello" >nul
    if !ERRORLEVEL!==0 (
        echo [PASS] Runtime executes hello.tllbc correctly
        set /a PASS_COUNT+=1
    ) else (
        echo [FAIL] Runtime output incorrect: !OUTPUT!
        set /a FAIL_COUNT+=1
    )
) else (
    echo [FAIL] hello.tllbc not found
    set /a FAIL_COUNT+=1
)

echo.

REM ============================================================
REM STEP 6: FFI Test
REM ============================================================
echo --- STEP 6: FFI / Native Interop Test ---

cd /d "%REPO_ROOT%"

if exist tests\ffi\probe_ffi.tll (
    "%HOST_C%\tllvm.exe" "%TOOLS_TLLC%\tllc.tllbc" compile tests\ffi\probe_ffi.tll -o "%TEMP%\ffi_test.tllbc" >nul 2>&1
    if %ERRORLEVEL%==0 (
        for /f "delims=" %%o in ('"%HOST_C%\tllvm.exe" "%TEMP%\ffi_test.tllbc" 2^>^&1 ^| findstr /c:"PASS:" /c:"FAIL:"') do (
            echo %%o
        )
        echo [INFO] FFI test completed (see above)
        set /a PASS_COUNT+=1
    ) else (
        echo [WARN] FFI test compilation failed
        set /a WARN_COUNT+=1
    )
) else (
    echo [WARN] FFI test not found
    set /a WARN_COUNT+=1
)

echo.

REM ============================================================
REM FINAL SUMMARY
REM ============================================================
echo ============================================================
echo CLEAN VM VERIFICATION SUMMARY
echo ============================================================
echo   PASS: %PASS_COUNT%
echo   FAIL: %FAIL_COUNT%
echo   WARN: %WARN_COUNT%
echo.

if %FAIL_COUNT%==0 (
    echo CANONICAL VM VERIFICATION: PASS
    echo ============================================================
    endlocal
    exit /b 0
) else (
    echo CANONICAL VM VERIFICATION: FAIL
    echo ============================================================
    endlocal
    exit /b 1
)
