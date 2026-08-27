@echo off
REM ============================================================
REM TLL OS - Build Native Launcher (Windows)
REM Usage: scripts\build.bat
REM ============================================================
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0.."
set "HOST_C=%REPO_ROOT%\host\c"
set "TCC_DIR=%HOST_C%\tcc"
set "TCC_EXE=%TCC_DIR%\tcc\tcc.exe"
set "TLLVM_EXE=%HOST_C%\tllvm.exe"

echo === TLL OS Build (Windows) ===
echo.

REM Step 1: Ensure TCC is available
if not exist "%TCC_EXE%" (
    echo [1/3] Extracting TCC compiler...
    if exist "%HOST_C%\tcc.zip" (
        powershell -Command "Expand-Archive -Path '%HOST_C%\tcc.zip' -DestinationPath '%TCC_DIR%' -Force"
        if errorlevel 1 (
            echo ERROR: Failed to extract tcc.zip
            exit /b 1
        )
    ) else (
        echo ERROR: tcc.zip not found at %HOST_C%\tcc.zip
        echo Please ensure the repository was cloned correctly.
        exit /b 1
    )
) else (
    echo [1/3] TCC compiler already available
)

REM Step 2: Build tllvm.exe
echo [2/3] Building tllvm.exe...
cd /d "%HOST_C%"
"%TCC_EXE%" -O2 -std=c99 -D_WIN32 "-Wl,-stack=0x4000000" -o tllvm.exe main.c vm.c value.c json.c builtin.c "%SystemRoot%\System32\winhttp.dll" "%SystemRoot%\System32\ws2_32.dll"
if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)

REM Step 3: Verify
echo [3/3] Verifying build...
if exist "%TLLVM_EXE%" (
    echo SUCCESS: tllvm.exe built successfully
    echo Size: %~z1 bytes
    for %%A in ("%TLLVM_EXE%") do echo Size: %%~zA bytes
) else (
    echo ERROR: tllvm.exe not found after build
    exit /b 1
)

echo.
echo === Build Complete ===
echo Native launcher: %TLLVM_EXE%
echo.
echo Next steps:
echo   scripts\bootstrap-tllc.bat    - Build tllc CLI tool
echo   scripts\compile-tests.bat      - Compile all test .tll files
echo   scripts\run-tests.bat          - Run all tests
endlocal
