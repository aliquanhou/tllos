@echo off
REM ============================================================
REM TLL OS - Bootstrap tllc CLI Tool (Windows)
REM Compiles tools/TLLC/ from source using the compiler seed.
REM Uses file-swap with pre-defined compiler/bootstrap_tllc.tll.
REM Usage: scripts\bootstrap-tllc.bat
REM ============================================================
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0.."
set "HOST_C=%REPO_ROOT%\host\c"
set "TLLVM_EXE=%HOST_C%\tllvm.exe"
set "COMPILER_DIR=%REPO_ROOT%\compiler"
set "COMPILER_TLL=%COMPILER_DIR%\compiler.tll"
set "COMPILER_BC=%COMPILER_DIR%\compiler.tllbc"
set "BOOTSTRAP_TLL=%COMPILER_DIR%\bootstrap_tllc.tll"
set "TLLC_BC=%REPO_ROOT%\tools\TLLC\tllc.tllbc"

echo === TLL OS Bootstrap tllc (Windows) ===
echo.

REM Step 1: Ensure tllvm exists
if not exist "%TLLVM_EXE%" (
    echo [1/4] Building tllvm.exe first...
    call "%~dp0build.bat"
    if errorlevel 1 exit /b 1
) else (
    echo [1/4] tllvm.exe already available
)

REM Step 2: Swap compiler.tll with bootstrap entry
echo [2/4] Swapping compiler.tll with bootstrap entry...
copy /Y "%COMPILER_TLL%" "%COMPILER_TLL%.bootstrap_backup" >nul
copy /Y "%BOOTSTRAP_TLL%" "%COMPILER_TLL%" >nul

REM Step 3: Two-stage compile
echo [3/4] Compiling tllc (two-stage bootstrap)...
cd /d "%COMPILER_DIR%"

REM Stage 1: seed compiler compiles bootstrap entry
echo   Stage 1: seed compiles bootstrap compiler...
"%TLLVM_EXE%" "%COMPILER_BC%"
if errorlevel 1 (
    echo ERROR: Stage 1 failed
    goto cleanup
)
if not exist "%COMPILER_DIR%\compiler_self_compiled.tllbc" (
    echo ERROR: Stage 1 output not found
    goto cleanup
)

REM Stage 2: bootstrap compiler compiles tllc
echo   Stage 2: bootstrap compiler compiles tllc...
"%TLLVM_EXE%" "%COMPILER_DIR%\compiler_self_compiled.tllbc"
if errorlevel 1 (
    echo ERROR: Stage 2 failed
    goto cleanup
)

REM Step 4: Verify
echo [4/4] Verifying output...
if exist "%TLLC_BC%" (
    echo SUCCESS: tllc.tllbc built
    for %%A in ("%TLLC_BC%") do echo   Size: %%~zA bytes
) else (
    echo ERROR: tllc.tllbc not found after build
    goto cleanup
)

:cleanup
echo Restoring compiler.tll...
copy /Y "%COMPILER_TLL%.bootstrap_backup" "%COMPILER_TLL%" >nul
del "%COMPILER_TLL%.bootstrap_backup" >nul 2>&1
del "%COMPILER_DIR%\compiler_self_compiled.tllbc" >nul 2>&1

echo.
echo === Bootstrap Complete ===
echo Usage: tllvm.exe tools\TLLC\tllc.tllbc ^<command^> [options]
echo   help      Show help
echo   compile   Compile .tll to .tllbc
echo   check     Compile check (no output)
echo   info      Inspect .tllbc bytecode
endlocal
