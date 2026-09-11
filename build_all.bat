@echo off
REM P2-01-C-D3-BUILD-INTEGRITY-RECOVERY: Fail-Closed Build
REM Any compile/link failure must immediately exit, never link old .obj.

call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64 >nul
if errorlevel 1 (
    echo [BUILD] FATAL: vcvarsall failed
    exit /b 1
)

cd /d "C:\Users\Administrator\Doubao\tllos"

echo [BUILD] === P2-01-C-D3 Build Integrity Recovery ==
echo [BUILD] Cleaning old .obj and .exe...
del /q *.obj 2>nul
del /q tllvm.exe 2>nul
del /q tllvm.pdb 2>nul

echo [BUILD] Compiling all C files (non-ASan, fail-closed)...

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\sqlite3.c /Fo:sqlite3.obj
if errorlevel 1 ( echo [BUILD] FATAL: sqlite3.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\main.c /Fo:main.obj
if errorlevel 1 ( echo [BUILD] FATAL: main.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\vm.c /Fo:vm.obj
if errorlevel 1 ( echo [BUILD] FATAL: vm.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime runtime\value.c /Fo:value.obj
if errorlevel 1 ( echo [BUILD] FATAL: value.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime runtime\arithmetic.c /Fo:arithmetic.obj
if errorlevel 1 ( echo [BUILD] FATAL: arithmetic.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime runtime\io.c /Fo:io.obj
if errorlevel 1 ( echo [BUILD] FATAL: io.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\json.c /Fo:json.obj
if errorlevel 1 ( echo [BUILD] FATAL: json.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\builtin.c /Fo:builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: builtin.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\ffi_builtin.c /Fo:ffi_builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: ffi_builtin.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\sqlite_builtin.c /Fo:sqlite_builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: sqlite_builtin.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\crypto_builtin.c /Fo:crypto_builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: crypto_builtin.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\password_builtin.c /Fo:password_builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: password_builtin.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\hmac_builtin.c /Fo:hmac_builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: hmac_builtin.c compile failed & exit /b 1 )

cl /nologo /O2 /utf-8 /c /Ihost\c /Iruntime host\c\http_client_builtin.c /Fo:http_client_builtin.obj
if errorlevel 1 ( echo [BUILD] FATAL: http_client_builtin.c compile failed & exit /b 1 )

echo [BUILD] All .c compiled successfully.
echo [BUILD] Linking tllvm.exe...

link /nologo /SUBSYSTEM:CONSOLE /OUT:tllvm.exe main.obj vm.obj value.obj arithmetic.obj io.obj json.obj builtin.obj ffi_builtin.obj sqlite_builtin.obj crypto_builtin.obj password_builtin.obj hmac_builtin.obj http_client_builtin.obj sqlite3.obj winhttp.lib ws2_32.lib bcrypt.lib
if errorlevel 1 ( echo [BUILD] FATAL: link failed & exit /b 1 )

echo [BUILD] === BUILD SUCCESS ===
echo [BUILD] tllvm.exe produced from current source.
