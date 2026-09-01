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
set "EXPECTED_TOTAL_ASSERTS=95"
REM P0-15.18.4-RUNTIME.4: TLL Compiler Semantic Guardrail
REM Verifies variable scope semantics: global/local, shadowing, params,
REM nested functions, closures, block scope, coroutines, recursion,
REM return value lifetime, and complete scope chain.

REM === ASSERTION HARD GATE ===
REM Independent golden values. These are NOT derived from source at runtime.
REM If someone adds/removes an assertion in a test file, they MUST update
REM the corresponding value here. Mismatch causes CI FAIL.
set "TLLC_BC=%~dp0..\tools\TLLC\tllc.tllbc"
for %%F in ("%~dp0..\tests\scope\*.tll") do (
    set /a TOTAL+=1
    set "NAME=%%~nF"
    set "OUT=%%~dpnF.tllbc"
    REM Look up expected assertion count for this test (independent golden value)
    set "EXPECTED=0"
    if "!NAME!"=="scope_01_global_local" set "EXPECTED=8"
    if "!NAME!"=="scope_02_shadowing" set "EXPECTED=11"
    if "!NAME!"=="scope_03_params" set "EXPECTED=10"
    if "!NAME!"=="scope_04_nested_fn" set "EXPECTED=10"
    if "!NAME!"=="scope_05_closure" set "EXPECTED=9"
    if "!NAME!"=="scope_06_block" set "EXPECTED=14"
    if "!NAME!"=="scope_07_coroutine" set "EXPECTED=5"
    if "!NAME!"=="scope_08_multi_fn_recursion" set "EXPECTED=6"
    if "!NAME!"=="scope_09_return_lifetime" set "EXPECTED=12"
    if "!NAME!"=="scope_10_complete_chain" set "EXPECTED=10"
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
                    REM Assertion Hard Gate: compare actual source count vs independent expected value
                    for /f %%A in ('type "%%F" ^| find /c "FAIL " 2^>nul') do set "ACTUAL_ASSERTS=%%A"
                    if not "!ACTUAL_ASSERTS!"=="!EXPECTED!" (
                        echo   FAIL: %%~nxF ^(assertion count mismatch: expected=!EXPECTED!, actual=!ACTUAL_ASSERTS!^)
                        echo     If you added/removed assertions, update EXPECTED values in this script.
                        set /a FAILED+=1
                    ) else (
                        echo   PASS: %%~nxF ^(!ACTUAL_ASSERTS!/!EXPECTED! assertions verified^)
                        set /a PASSED+=1
                        set /a SCOPE_ASSERTS+=!ACTUAL_ASSERTS!
                    )
                )
            )
        )
        if exist "!OUT!" del "!OUT!"
    )
)

REM Assertion Hard Gate: verify total
if not "%SCOPE_ASSERTS%"=="%EXPECTED_TOTAL_ASSERTS%" (
    echo FAIL: Scope assertion total mismatch: expected=%EXPECTED_TOTAL_ASSERTS%, actual=%SCOPE_ASSERTS%
    set /a FAILED+=1
) else (
    echo   Scope assertion total: %SCOPE_ASSERTS%/%EXPECTED_TOTAL_ASSERTS% ^(HARD GATE PASS^)
)

if exist "%TMPFILE%" del "%TMPFILE%"

echo.
echo === Test Results ===
echo Total:  %TOTAL%
echo Passed: %PASSED%
echo Failed: %FAILED%
echo Scope assertions verified: %SCOPE_ASSERTS%/%EXPECTED_TOTAL_ASSERTS% ^(HARD GATE^)
echo.

if %FAILED% gtr 0 (
    echo SOME TESTS FAILED
    exit /b 1
) else (
    echo ALL TESTS PASSED
    exit /b 0
)
