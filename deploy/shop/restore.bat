@echo off
REM TLL Mall - Database Restore Script
REM Usage: restore.bat <backup_file>

setlocal

set "SCRIPT_DIR=%~dp0"
set "DB_FILE=%SCRIPT_DIR%data\mall.db"
set "BACKUP_FILE=%~1"

if "%BACKUP_FILE%"=="" (
    echo [ERROR] Usage: restore.bat ^<backup_file^>
    echo Example: restore.bat backups\mall_20260904_120000.db
    exit /b 1
)

if not exist "%BACKUP_FILE%" (
    echo [ERROR] Backup file not found: %BACKUP_FILE%
    exit /b 1
)

echo [WARN] This will overwrite the current database: %DB_FILE%
echo [WARN] Current database will be backed up as mall.db.bak
choice /c YN /m "Continue?"
if errorlevel 2 (
    echo [ABORT] Restore cancelled
    exit /b 0
)

if exist "%DB_FILE%" (
    copy "%DB_FILE%" "%DB_FILE%.bak" >nul
    echo [OK] Current database backed up to mall.db.bak
)

copy "%BACKUP_FILE%" "%DB_FILE%" >nul
if %errorlevel% equ 0 (
    echo [OK] Database restored from: %BACKUP_FILE%
) else (
    echo [ERROR] Restore failed
    exit /b 1
)

echo [DONE] Restore complete. Restart the server to apply changes.
endlocal
