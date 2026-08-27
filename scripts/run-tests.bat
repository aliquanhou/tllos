@echo off
REM ============================================================
REM TLL OS - Run All Tests (Windows)
REM Runs all compiled .tllbc test files and reports results.
REM Usage: scripts\run-tests.bat
REM ============================================================
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0.."
set "TLLVM_EXE=%REPO_ROOT%\host\c\tllvm.exe"

echo === TLL OS Run Tests (Windows) ===
echo.

REM Ensure tllvm exists
if not exist "%TLLVM_EXE%" (
    echo Building tllvm.exe first...
    call "%~dp0build.bat"
    if errorlevel 1 exit /b 1
)

set "TOTAL=0"
set "PASSED=0"
set "FAILED=0"

REM Run acceptance tests
echo --- Acceptance Tests ---
for %%F in ("%REPO_ROOT%\tests\acceptance\*.tllbc") do (
    if exist "%%F" (
        set /a TOTAL+=1
        "%TLLVM_EXE%" "%%F" >nul 2>&1
        if errorlevel 1 (
            echo   FAIL: %%~nxF
            set /a FAILED+=1
        ) else (
            echo   PASS: %%~nxF
            set /a PASSED+=1
        )
    )
)

REM Run regression tests
echo --- Regression Tests ---
for %%F in ("%REPO_ROOT%\tests\regression\*.tllbc") do (
    if exist "%%F" (
        set /a TOTAL+=1
        "%TLLVM_EXE%" "%%F" >nul 2>&1
        if errorlevel 1 (
            echo   FAIL: %%~nxF
            set /a FAILED+=1
        ) else (
            echo   PASS: %%~nxF
            set /a PASSED+=1
        )
    )
)

REM Run regression test directories
for /d %%D in ("%REPO_ROOT%\tests\regression\*") do (
    if exist "%%D\main.tllbc" (
        set /a TOTAL+=1
        "%TLLVM_EXE%" "%%D\main.tllbc" >nul 2>&1
        if errorlevel 1 (
            echo   FAIL: %%~nxD\main.tllbc
            set /a FAILED+=1
        ) else (
            echo   PASS: %%~nxD\main.tllbc
            set /a PASSED+=1
        )
    )
)

echo.
echo === Test Results ===
echo Total:  !TOTAL!
echo Passed: !PASSED!
echo Failed: !FAILED!
echo.

if !FAILED! gtr 0 (
    echo SOME TESTS FAILED
    exit /b 1
) else (
    echo ALL TESTS PASSED
    exit /b 0
)
endlocal
