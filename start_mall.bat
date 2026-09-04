@echo off
REM TLLOS Mall - Start Script
REM Starts TLLOS Mall server and Nginx reverse proxy

echo ========================================
echo   TLLOS Mall - Starting Services
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if TLLOS Mall is already running
tasklist /FI "IMAGENAME eq tllvm.exe" 2>NUL | find /I /N "tllvm.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] TLLOS Mall is already running, stopping first...
    taskkill /F /IM tllvm.exe >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)

REM Start TLLOS Mall server
echo [START] Starting TLLOS Mall server (port 8090)...
start "TLLOS Mall" /B cmd /c "host\c\tllvm.exe mall\main.tllbc"
timeout /t 4 /nobreak >NUL

REM Verify TLLOS Mall is running
tasklist /FI "IMAGENAME eq tllvm.exe" 2>NUL | find /I /N "tllvm.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] TLLOS Mall server started successfully
) else (
    echo [ERROR] TLLOS Mall server failed to start!
    pause
    exit /b 1
)

REM Check if Nginx is already running
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Nginx is already running, reloading config...
    cd nginx-1.24.0
    nginx.exe -s reload
    cd ..
) else (
    echo [START] Starting Nginx reverse proxy (port 80)...
    cd nginx-1.24.0
    start "Nginx" /B nginx.exe
    cd ..
    timeout /t 2 /nobreak >NUL
)

REM Verify Nginx is running
tasklist /FI "IMAGENAME eq nginx.exe" 2>NUL | find /I /N "nginx.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Nginx started successfully
) else (
    echo [WARN] Nginx may not have started, check logs
)

echo.
echo ========================================
echo   Services Started Successfully!
echo ========================================
echo.
echo   TLLOS Mall:  http://127.0.0.1:8090
echo   Nginx Proxy: http://127.0.0.1:80
echo   Domain:      http://shop.tllos.com
echo.
echo   Admin:       http://shop.tllos.com/admin
echo   Username:    admin
echo   Password:    admin123
echo.
echo   Press Ctrl+C to stop this monitor
echo   (Services will continue running in background)
echo ========================================

REM Keep script running to show status
:loop
timeout /t 30 /nobreak >NUL
tasklist /FI "IMAGENAME eq tllvm.exe" 2>NUL | find /I /N "tllvm.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [%TIME%] TLLOS Mall: Running
) else (
    echo [%TIME%] [WARN] TLLOS Mall: NOT RUNNING!
)
goto loop
