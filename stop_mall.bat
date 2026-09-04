@echo off
REM TLLOS Mall - Stop Script
REM Stops TLLOS Mall server and Nginx

echo ========================================
echo   TLLOS Mall - Stopping Services
echo ========================================
echo.

cd /d "%~dp0"

REM Stop Nginx
echo [STOP] Stopping Nginx...
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    cd nginx-1.24.0
    nginx.exe -s stop 2>NUL
    cd ..
    timeout /t 2 /nobreak >NUL
    taskkill /F /IM nginx.exe >NUL 2>&1
    echo [OK] Nginx stopped
) else (
    echo [INFO] Nginx is not running
)

REM Stop TLLOS Mall
echo [STOP] Stopping TLLOS Mall...
tasklist /FI "IMAGENAME eq tllvm.exe" 2>NUL | find /I /N "tllvm.exe">NUL
if "%ERRORLEVEL%"=="0" (
    taskkill /F /IM tllvm.exe >NUL 2>&1
    echo [OK] TLLOS Mall stopped
) else (
    echo [INFO] TLLOS Mall is not running
)

echo.
echo ========================================
echo   All Services Stopped
echo ========================================
timeout /t 3 /nobreak >NUL
