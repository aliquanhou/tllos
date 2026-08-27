@echo off
REM ============================================================
REM TLL OS - Compile All Tests (Windows)
REM Compiles all .tll test files to .tllbc using tllc.
REM Usage: scripts\compile-tests.bat
REM ============================================================
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0.."
set "TLLVM_EXE=%REPO_ROOT%\host\c\tllvm.exe"
set "TLLC_BC=%REPO_ROOT%\tools\TLLC\tllc.tllbc"
set "ACCEPTANCE_DIR=%REPO_ROOT%\tests\acceptance"
set "REGRESSION_DIR=%REPO_ROOT%\tests\regression"

echo === TLL OS Compile Tests (Windows) ===
echo.

REM Ensure tllc exists
if not exist "%TLLC_BC%" (
    echo tllc.tllbc not found. Running bootstrap first...
    call "%~dp0bootstrap-tllc.bat"
    if errorlevel 1 exit /b 1
) else (
    echo [1/4] tllc already available
)

REM Compile acceptance tests
echo [2/4] Compiling acceptance tests...
set "ACC_COUNT=0"
set "ACC_FAIL=0"
for %%F in ("%ACCEPTANCE_DIR%\*.tll") do (
    if /i "%%~xF"==".tll" (
        set /a ACC_COUNT+=1
        "%TLLVM_EXE%" "%TLLC_BC%" compile "%%F" -o "%%~dpnF.tllbc" >nul 2>&1
        if errorlevel 1 (
            echo   FAIL: %%~nxF
            set /a ACC_FAIL+=1
        ) else (
            echo   OK:   %%~nxF
        )
    )
)
echo   Acceptance: !ACC_COUNT! files, !ACC_FAIL! failures

REM Compile regression tests (single .tll files)
echo [3/4] Compiling regression tests (single files)...
set "REG_COUNT=0"
set "REG_FAIL=0"
for %%F in ("%REGRESSION_DIR%\*.tll") do (
    if /i "%%~xF"==".tll" (
        set /a REG_COUNT+=1
        "%TLLVM_EXE%" "%TLLC_BC%" compile "%%F" -o "%%~dpnF.tllbc" >nul 2>&1
        if errorlevel 1 (
            echo   FAIL: %%~nxF
            set /a REG_FAIL+=1
        ) else (
            echo   OK:   %%~nxF
        )
    )
)
echo   Regression: !REG_COUNT! files, !REG_FAIL! failures

REM Compile regression test directories (each has main.tll)
echo [4/4] Compiling regression test directories...
set "DIR_COUNT=0"
set "DIR_FAIL=0"
for /d %%D in ("%REGRESSION_DIR%\*") do (
    if exist "%%D\main.tll" (
        set /a DIR_COUNT+=1
        "%TLLVM_EXE%" "%TLLC_BC%" compile "%%D\main.tll" -o "%%D\main.tllbc" >nul 2>&1
        if errorlevel 1 (
            echo   FAIL: %%~nxD\main.tll
            set /a DIR_FAIL+=1
        ) else (
            echo   OK:   %%~nxD\main.tll
        )
    )
)
echo   Directories: !DIR_COUNT! dirs, !DIR_FAIL! failures

echo.
echo === Test Compilation Complete ===
echo.
echo To run tests: scripts\run-tests.bat
endlocal
