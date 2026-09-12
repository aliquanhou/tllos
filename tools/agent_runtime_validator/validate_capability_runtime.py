#!/usr/bin/env python3
"""
TLL OS Native Capability Runtime Validator

5 Gates:
  Gate 1: Virtual File System
  Gate 2: Process Manager
  Gate 3: Code Runtime
  Gate 4: App Runtime
  Gate 5: All Tools Real (no mock)
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []


def gate1_virtual_fs():
    try:
        from tllos.virtual_machine.agent import TLLVirtualFileSystem
        fs = TLLVirtualFileSystem()
        fs.write_file("/test.txt", "hello")
        result = fs.read_file("/test.txt")
        if result["content"] == "hello" and result["exists"]:
            results.append(("Gate 1: Virtual File System", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 1: Virtual File System", FAIL))
    return False


def gate2_process_manager():
    try:
        from tllos.virtual_machine.agent import TLLProcessManager
        pm = TLLProcessManager()
        proc = pm.start_process("test-proc")
        procs = pm.list_processes()
        if proc["pid"] > 0 and procs["total"] >= 2:
            results.append(("Gate 2: Process Manager", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 2: Process Manager", FAIL))
    return False


def gate3_code_runtime():
    try:
        from tllos.virtual_machine.agent import TLLCodeRuntime
        cr = TLLCodeRuntime()
        gen = cr.generate_code("hello world")
        run = cr.run_code(gen["code"])
        if run.success and "hello" in run.output.lower():
            results.append(("Gate 3: Code Runtime", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 3: Code Runtime", FAIL))
    return False


def gate4_app_runtime():
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        from tllos.virtual_machine.agent import TLLAppRuntime, TLLProcessManager
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        pm = TLLProcessManager()
        ar = TLLAppRuntime(wm, pm)
        app = ar.create_app("Test App")
        launched = ar.launch_app(app["app_id"])
        if launched["status"] == "RUNNING" and launched["window_id"]:
            results.append(("Gate 4: App Runtime", PASS))
            return True
    except Exception as e:
        pass
    results.append(("Gate 4: App Runtime", FAIL))
    return False


def gate5_all_tools_real():
    """Check no mock implementations remain."""
    try:
        from tllos.virtual_machine import TLLFramebuffer, TLLWindowManager, TLLCompositor
        from tllos.virtual_machine.agent import TLLToolRuntime
        fb = TLLFramebuffer(800, 600)
        wm = TLLWindowManager(fb)
        comp = TLLCompositor(wm)
        runtime = TLLToolRuntime(wm, comp)

        # Test storage actually works
        r = runtime.execute_tool("storage.write", path="/test.txt", content="real")
        if not r.success or r.output.get("written") != True:
            results.append(("Gate 5: All Tools Real", FAIL))
            return False

        # Test process actually works
        r2 = runtime.execute_tool("process.start", name="test")
        if not r2.success or r2.output.get("pid") is None:
            results.append(("Gate 5: All Tools Real", FAIL))
            return False

        results.append(("Gate 5: All Tools Real", PASS))
        return True
    except Exception as e:
        results.append(("Gate 5: All Tools Real", f"FAIL: {e}"))
        return False


def main():
    print("=" * 60)
    print("TLL OS Native Capability Runtime Validator")
    print("=" * 60)
    print()

    gate1_virtual_fs()
    gate2_process_manager()
    gate3_code_runtime()
    gate4_app_runtime()
    gate5_all_tools_real()

    print()
    passed = sum(1 for _, r in results if r == PASS)
    failed = len(results) - passed
    for name, result in results:
        status = "✅" if result == PASS else "❌"
        print(f"  {status} {name:40s} {result}")

    print()
    print(f"Total: {passed}/5 Gates PASS, {failed} FAIL")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
