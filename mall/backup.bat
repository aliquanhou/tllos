@echo off
REM TLL Mall - Database Backup Script
REM Usage: backup.bat [backup_dir]

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "DB_FILE=%SCRIPT_DIR%data\mall.db"
set "BACKUP_DIR=%~1"

if "%BACKUP_DIR%"=="" set "BACKUP_DIR=%SCRIPT_DIR%backups"

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "MIN=%dt:~10,2%"
set "SS=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD_%HH%%MIN%%SS%"

set "BACKUP_FILE=%BACKUP_DIR%\mall_%TIMESTAMP%.db"

if not exist "%DB_FILE%" (
    echo [ERROR] Database file not found: %DB_FILE%
    exit /b 1
)

copy "%DB_FILE%" "%BACKUP_FILE%" >nul
if %errorlevel% equ 0 (
    echo [OK] Backup created: %BACKUP_FILE%
) else (
    echo [ERROR] Backup failed
    exit /b 1
)

REM Clean old backups (keep last 10)
for /f "skip=10" %%f in ('dir /b /o-d "%BACKUP_DIR%\mall_*.db" 2^>nul') do (
    del "%BACKUP_DIR%\%%f"
    echo [CLEAN] Removed old backup: %%f
)

echo [DONE] Backup complete
endlocal
