@echo off
REM TLL Native Runtime Build Script (Windows)
REM Canonical single source of truth for native build.
REM All CI workflows and local builds should use this script.

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set HOST_C_DIR=%SCRIPT_DIR%..\host\c

REM Canonical C source files — DO NOT modify this list without updating
REM build-native.sh and all CI workflows accordingly.
set TLL_C_SOURCES=main.c vm.c value.c json.c builtin.c ffi_builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c sqlite3.c

cd /d "%HOST_C_DIR%"

echo [build-native] Windows detected

REM Try MSVC first (cl.exe), then fall back to TCC
where cl.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [build-native] Using MSVC (cl.exe)
    cl /O2 /D_CRT_SECURE_NO_WARNINGS /Fe:tllvm.exe %TLL_C_SOURCES% ws2_32.lib winhttp.lib bcrypt.lib
    if %ERRORLEVEL% neq 0 (
        echo [build-native] MSVC build failed
        exit /b 1
    )
) else (
    echo [build-native] MSVC not found, trying TCC
    if defined TCC_EXE (
        "%TCC_EXE%" -O2 -std=c99 -D_WIN32 "-Wl,-stack=0x4000000" -o tllvm.exe %TLL_C_SOURCES% "%SystemRoot%\System32\winhttp.dll" "%SystemRoot%\System32\ws2_32.dll" "%SystemRoot%\System32\bcrypt.dll"
        if %ERRORLEVEL% neq 0 (
            echo [build-native] TCC build failed
            exit /b 1
        )
    ) else (
        echo [build-native] ERROR: Neither MSVC (cl.exe) nor TCC (TCC_EXE) found
        echo [build-native] Install Visual Studio Build Tools or set TCC_EXE environment variable
        exit /b 1
    )
)

echo [build-native] Build complete: %HOST_C_DIR%\tllvm.exe
endlocal
