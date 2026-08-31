@echo off
REM ============================================================
REM TLL OS - Run All Tests (Windows)
REM Supports stdout comparison via .expected.txt files.
REM Non-zero exit code: name test file exitN.tll (e.g. exit42.tll)
REM Usage: scripts\run-tests.bat
REM ============================================================
setlocal enabledelayedexpansion

set "TLLVM_EXE=%~dp0..\host\c\tllvm.exe"
set "TMPFILE=%~dp0..\.test_out.txt"

echo === TLL OS Run Tests (Windows) ===
echo.

if not exist "%TLLVM_EXE%" (
    echo Building tllvm.exe first...
    call "%~dp0build.bat"
    if errorlevel 1 exit /b 1
)

set /a TOTAL=0
set /a PASSED=0
set /a FAILED=0

echo --- Acceptance Tests ---
for %%F in ("%~dp0..\tests\acceptance\*.tllbc") do (
    if /i "%%~xF"==".tllbc" (
        set /a TOTAL+=1
        set "EXPECTED=0"
        set "NAME=%%~nF"
        if not "!NAME:exit=!"=="!NAME!" set "EXPECTED=!NAME:exit=!"
        "%TLLVM_EXE%" "%%F" >"%TMPFILE%" 2>&1
        set "ACTUAL=!ERRORLEVEL!"
        if not "!ACTUAL!"=="!EXPECTED!" (
            echo   FAIL: %%~nxF ^(exit=!ACTUAL! expected=!EXPECTED!^)
            set /a FAILED+=1
        ) else (
            set "STDOUT_OK=1"
            if exist "%%~dpnF.expected.txt" (
                fc "%TMPFILE%" "%%~dpnF.expected.txt" >nul 2>&1
                if not "!ERRORLEVEL!"=="0" set "STDOUT_OK=0"
            )
            if "!STDOUT_OK!"=="1" (
                echo   PASS: %%~nxF
                set /a PASSED+=1
            ) else (
                echo   FAIL: %%~nxF ^(stdout mismatch^)
                set /a FAILED+=1
            )
        )
    )
)

echo --- Regression Tests ---
for %%F in ("%~dp0..\tests\regression\*.tllbc") do (
    if /i "%%~xF"==".tllbc" (
        set /a TOTAL+=1
        set "EXPECTED=0"
        set "NAME=%%~nF"
        if not "!NAME:exit=!"=="!NAME!" set "EXPECTED=!NAME:exit=!"
        "%TLLVM_EXE%" "%%F" >"%TMPFILE%" 2>&1
        set "ACTUAL=!ERRORLEVEL!"
        if not "!ACTUAL!"=="!EXPECTED!" (
            echo   FAIL: %%~nxF ^(exit=!ACTUAL! expected=!EXPECTED!^)
            set /a FAILED+=1
        ) else (
            set "STDOUT_OK=1"
            if exist "%%~dpnF.expected.txt" (
                fc "%TMPFILE%" "%%~dpnF.expected.txt" >nul 2>&1
                if not "!ERRORLEVEL!"=="0" set "STDOUT_OK=0"
            )
            if "!STDOUT_OK!"=="1" (
                echo   PASS: %%~nxF
                set /a PASSED+=1
            ) else (
                echo   FAIL: %%~nxF ^(stdout mismatch^)
                set /a FAILED+=1
            )
        )
    )
)

echo --- Regression Test Directories ---
for /d %%D in ("%~dp0..\tests\regression\*") do (
    if exist "%%D\main.tllbc" (
        set /a TOTAL+=1
        set "EXPECT_ERROR=0"
        if exist "%%D\test.json" (
            findstr /c:"\"expectError\": true" "%%D\test.json" >nul 2>&1
            if not errorlevel 1 set "EXPECT_ERROR=1"
        )
        "%TLLVM_EXE%" "%%D\main.tllbc" >"%TMPFILE%" 2>&1
        set "ACTUAL=!ERRORLEVEL!"
        if "!EXPECT_ERROR!"=="1" (
            if "!ACTUAL!"=="0" (
                echo   FAIL: %%~nxD\main.tllbc ^(expected error, got exit 0^)
                set /a FAILED+=1
            ) else (
                echo   PASS: %%~nxD\main.tllbc ^(error as expected^)
                set /a PASSED+=1
            )
        ) else (
            if not "!ACTUAL!"=="0" (
                echo   FAIL: %%~nxD\main.tllbc ^(exit=!ACTUAL!^)
                set /a FAILED+=1
            ) else (
                echo   PASS: %%~nxD\main.tllbc
                set /a PASSED+=1
            )
        )
    )
)

if exist "%TMPFILE%" del "%TMPFILE%"

echo --- Scope Semantics Tests ---
set "SCOPE_ASSERTS=0"
REM P0-15.18.4-RUNTIME.4: TLL Compiler Semantic Guardrail
REM Verifies variable scope semantics: global/local, shadowing, params,
REM nested functions, closures, block scope, coroutines, recursion,
REM return value lifetime, and complete scope chain.
set "TLLC_BC=%~dp0..\tools\TLLC\tllc.tllbc"
for %%F in ("%~dp0..\tests\scope\*.tll") do (
    set /a TOTAL+=1
    set "NAME=%%~nF"
    set "OUT=%%~dpnF.tllbc"
    "%TLLVM_EXE%" "%TLLC_BC%" compile "%%F" -o "!OUT!" >"%TMPFILE%" 2>&1
    if errorlevel 1 (
        echo   FAIL: %%~nxF ^(compile error^)
        type "%TMPFILE%"
        set /a FAILED+=1
    ) else (
        "%TLLVM_EXE%" "!OUT!" >"%TMPFILE%" 2>&1
        set "ACTUAL=!ERRORLEVEL!"
        if not "!ACTUAL!"=="0" (
            echo   FAIL: %%~nxF ^(exit=!ACTUAL!^)
            type "%TMPFILE%"
            set /a FAILED+=1
        ) else (
            findstr /c:"PASS" "%TMPFILE%" >nul 2>&1
            if errorlevel 1 (
                echo   FAIL: %%~nxF ^(no PASS marker^)
                type "%TMPFILE%"
                set /a FAILED+=1
            ) else (
                findstr /c:"FAIL" "%TMPFILE%" >nul 2>&1
                if not errorlevel 1 (
                    echo   FAIL: %%~nxF ^(contains FAIL^)
                    type "%TMPFILE%"
                    set /a FAILED+=1
                ) else (
                    REM Count assertions in source file for hard verification
                    for /f "tokens=2 delims=:" %%A in ('find /c "FAIL " "%%F" 2^>nul') do set "ASSERTS=%%A"
                    echo   PASS: %%~nxF ^(!ASSERTS! assertions verified^)
                    set /a PASSED+=1
                    set /a SCOPE_ASSERTS+=!ASSERTS!
                )
            )
        )
        if exist "!OUT!" del "!OUT!"
    )
)

if exist "%TMPFILE%" del "%TMPFILE%"

echo.
echo === Test Results ===
echo Total:  %TOTAL%
echo Passed: %PASSED%
echo Failed: %FAILED%
echo Scope assertions verified: %SCOPE_ASSERTS%
echo.

if %FAILED% gtr 0 (
    echo SOME TESTS FAILED
    exit /b 1
) else (
    echo ALL TESTS PASSED
    exit /b 0
)
