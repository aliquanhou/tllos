@echo off
REM ============================================================
REM TLL OS - Builtin ABI Consistency Check (Windows)
REM Verifies spec/BUILTINS.json matches host/c/builtin.c
REM Usage: scripts\check-abi.bat
REM ============================================================
setlocal enabledelayedexpansion

set "SPEC=%~dp0..\spec\BUILTINS.json"
set "IMPL=%~dp0..\host\c\builtin.c"

echo === TLL OS ABI Consistency Check ===
echo.

set /a ERRORS=0

if not exist "%SPEC%" (
    echo FAIL: spec\BUILTINS.json not found
    exit /b 1
)
if not exist "%IMPL%" (
    echo FAIL: host\c\builtin.c not found
    exit /b 1
)

echo Checking process and time/fs builtins ^(P0-2/P0-3 extension^)...
for %%I in (120 121 122 123 124 125) do (
    findstr /c:"\"index\": %%I" "%SPEC%" >nul 2>&1
    if errorlevel 1 (
        echo   FAIL: idx %%I missing from BUILTINS.json
        set /a ERRORS+=1
    )
    findstr /c:"idx == %%I" "%IMPL%" >nul 2>&1
    if errorlevel 1 (
        echo   FAIL: idx %%I missing from builtin.c
        set /a ERRORS+=1
    )
)

echo Checking Genesis builtin ranges ^(0-97^)...
for %%R in ("idx >= 5 && idx <= 23" "idx >= 24 && idx <= 48" "idx >= 49 && idx <= 71" "idx >= 72 && idx <= 78" "idx >= 79 && idx <= 90" "idx >= 91 && idx <= 97") do (
    findstr /c:%%~R "%IMPL%" >nul 2>&1
    if errorlevel 1 (
        echo   FAIL: range %%~R missing from builtin.c
        set /a ERRORS+=1
    )
)

echo.
if %ERRORS% equ 0 (
    echo === ABI CONSISTENT ===
    exit /b 0
) else (
    echo === ABI DRIFT DETECTED: %ERRORS% error^(s^) ===
    exit /b 1
)
