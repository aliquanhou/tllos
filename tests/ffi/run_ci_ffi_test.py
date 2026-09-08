#!/usr/bin/env python3
"""
Cross-platform FFI CI test for TLL.
Runs on Windows, Linux, macOS.
Verifies ffi.load -> ffi.symbol -> ffi.call -> real native result.
"""
import os
import sys
import subprocess
import platform

def find_tllvm():
    """Find tllvm executable in host/c/."""
    if platform.system() == "Windows":
        path = os.path.join("host", "c", "tllvm.exe")
    else:
        path = os.path.join("host", "c", "tllvm")
    if os.path.exists(path):
        return os.path.abspath(path)
    return None

def find_or_build_compiler(tllvm):
    """Find compiler bytecode, or build it from source."""
    # Prefer new compiler with FFI support
    new_compiler = os.path.join("tools", "TLLC", "tllc_new.tllbc")
    if os.path.exists(new_compiler):
        return os.path.abspath(new_compiler)

    # Try to build new compiler from baseline
    baseline = os.path.join("tools", "TLLC", "tllc.tllbc")
    main_tll = os.path.join("tools", "TLLC", "main.tll")
    if os.path.exists(baseline) and os.path.exists(main_tll):
        print("Building new compiler with FFI support...")
        rc, stdout, stderr = run_command([
            tllvm, baseline, "compile", main_tll, "-o", new_compiler
        ])
        if rc == 0 and os.path.exists(new_compiler):
            print("New compiler built successfully")
            return os.path.abspath(new_compiler)
        else:
            print(f"Warning: failed to build new compiler (rc={rc})")
            if stderr:
                print(stderr.strip()[:500])

    # Fall back to baseline (may not have FFI support)
    if os.path.exists(baseline):
        print("Warning: using baseline compiler (FFI may not be supported)")
        return os.path.abspath(baseline)

    return None

def get_platform_library():
    """Get platform-specific C library path and test function."""
    system = platform.system()
    if system == "Windows":
        return "msvcrt.dll", "strlen", "hello", 5
    elif system == "Linux":
        candidates = [
            "/lib/x86_64-linux-gnu/libc.so.6",
            "/lib64/libc.so.6",
            "/usr/lib/libc.so",
            "libc.so.6",
        ]
        for c in candidates:
            if os.path.exists(c) or c.startswith("lib"):
                return c, "strlen", "hello", 5
        return "libc.so.6", "strlen", "hello", 5
    elif system == "Darwin":
        candidates = [
            "/usr/lib/libSystem.B.dylib",
            "/usr/lib/libc.dylib",
            "libSystem.B.dylib",
        ]
        for c in candidates:
            if os.path.exists(c) or c.startswith("lib"):
                return c, "strlen", "hello", 5
        return "libSystem.B.dylib", "strlen", "hello", 5
    else:
        return None, None, None, None

def write_test_file(lib_path, func_name, test_str, expected):
    """Write a TLL FFI test file."""
    # Note: do NOT use convert.toString on large integers (pointer handles),
    # it may return empty. Use direct io.println with the value.
    test_code = f'''// CI FFI test - {platform.system()}
let lib = ffi.load("{lib_path}")
if lib == 0 {{
    io.println("FAIL: could not load library {lib_path}")
    return
}}
io.println("PASS: library loaded")

let sym = ffi.symbol(lib, "{func_name}")
if sym == 0 {{
    io.println("FAIL: could not resolve symbol {func_name}")
    return
}}
io.println("PASS: symbol resolved")

let argTypes = [7]  // cstring
let args = ["{test_str}"]
let result = ffi.call(sym, 2, argTypes, args)  // int64 return
io.println("PASS: {func_name} returned " + convert.toString(result))

if result == {expected} {{
    io.println("ALL FFI CI TESTS PASSED")
}} else {{
    io.println("FAIL: expected {expected}, got " + convert.toString(result))
}}
'''
    test_path = os.path.join("tests", "ffi", "ci_ffi_test.tll")
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    with open(test_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(test_code)
    return os.path.abspath(test_path)

def run_command(cmd, cwd=None):
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=120
    )
    return result.returncode, result.stdout, result.stderr

def main():
    print(f"=== TLL FFI CI Test ===")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()

    # Find tools
    tllvm = find_tllvm()
    if not tllvm:
        print("FAIL: tllvm not found in host/c/")
        return 1

    compiler = find_or_build_compiler(tllvm)
    if not compiler:
        print("FAIL: compiler bytecode not found in tools/TLLC/")
        return 1

    print(f"tllvm: {tllvm}")
    print(f"compiler: {compiler}")
    print()

    # Get platform library
    lib_path, func_name, test_str, expected = get_platform_library()
    if not lib_path:
        print(f"FAIL: unsupported platform {platform.system()}")
        return 1

    print(f"Library: {lib_path}")
    print(f"Function: {func_name}")
    print(f"Test string: '{test_str}'")
    print(f"Expected result: {expected}")
    print()

    # Write test file
    test_file = write_test_file(lib_path, func_name, test_str, expected)
    output_file = test_file.replace(".tll", ".tllbc")

    # Compile
    print("--- Compiling ---")
    rc, stdout, stderr = run_command([tllvm, compiler, "compile", test_file, "-o", output_file])
    if stdout:
        # Only print last few lines to avoid noise
        lines = stdout.strip().split("\n")
        for l in lines[-5:]:
            print(l)
    if rc != 0:
        print(f"FAIL: compilation failed with exit code {rc}")
        if stderr:
            print(stderr.strip()[:500])
        return 1
    if not os.path.exists(output_file):
        print("FAIL: output file not created")
        return 1
    print("Compilation successful")
    print()

    # Run
    print("--- Running ---")
    rc, stdout, stderr = run_command([tllvm, output_file])
    if stdout:
        print(stdout.strip())
    if stderr:
        stderr_lines = [l for l in stderr.strip().split("\n") if l.strip()]
        if stderr_lines:
            print("STDERR (may include expected error messages):")
            for l in stderr_lines:
                print(f"  {l}")
    print()

    # Cleanup
    if os.path.exists(output_file):
        os.remove(output_file)

    # Check result
    if "ALL FFI CI TESTS PASSED" in stdout:
        print("=== FFI CI TEST: PASS ===")
        return 0
    else:
        print(f"=== FFI CI TEST: FAIL (exit code {rc}) ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())
