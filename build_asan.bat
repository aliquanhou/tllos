@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64 >nul
cd /d "C:\Users\Administrator\Doubao\tllos"
echo Compiling all C files (ASan)...
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\main.c /Fo:main_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\vm.c /Fo:vm_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime runtime\value.c /Fo:value_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime runtime\arithmetic.c /Fo:arithmetic_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime runtime\io.c /Fo:io_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\json.c /Fo:json_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\builtin.c /Fo:builtin_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\ffi_builtin.c /Fo:ffi_builtin_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\sqlite_builtin.c /Fo:sqlite_builtin_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\crypto_builtin.c /Fo:crypto_builtin_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\password_builtin.c /Fo:password_builtin_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\hmac_builtin.c /Fo:hmac_builtin_asan.obj
cl /nologo /Od /Zi /fsanitize=address /utf-8 /c /Ihost\c /Iruntime host\c\http_client_builtin.c /Fo:http_client_builtin_asan.obj
echo Linking tllvm_asan.exe...
link /nologo /SUBSYSTEM:CONSOLE /OUT:tllvm_asan.exe main_asan.obj vm_asan.obj value_asan.obj arithmetic_asan.obj io_asan.obj json_asan.obj builtin_asan.obj ffi_builtin_asan.obj sqlite_builtin_asan.obj crypto_builtin_asan.obj password_builtin_asan.obj hmac_builtin_asan.obj http_client_builtin_asan.obj sqlite3.obj winhttp.lib ws2_32.lib bcrypt.lib
echo Done.
