@echo off
REM TLL Mall - Start Server Script
REM Usage: start.bat [port]

setlocal

set "SCRIPT_DIR=%~dp0"
set "TLLVM=%SCRIPT_DIR%..\host\c\tllvm.exe"
set "BYTECODE=%SCRIPT_DIR%main.tllbc"
set "PORT=%~1"

if "%PORT%"=="" set "PORT=8090"

if not exist "%TLLVM%" (
    echo [ERROR] tllvm.exe not found: %TLLVM%
    echo Please build TLL VM first.
    exit /b 1
)

if not exist "%BYTECODE%" (
    echo [INFO] Compiling mall...
    "%TLLVM%" "%SCRIPT_DIR%..\tools\TLLC\tllc.tllbc" compile "%SCRIPT_DIR%main.tll" -o "%BYTECODE%"
    if errorlevel 1 (
        echo [ERROR] Compilation failed
        exit /b 1
    )
)

echo [INFO] Starting TLL Mall on port %PORT%...
echo [INFO] Press Ctrl+C to stop
"%TLLVM%" "%BYTECODE%"

endlocal
