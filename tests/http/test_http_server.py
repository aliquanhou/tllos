#!/usr/bin/env python3
"""P1-NEXT L2: HTTP Server Gate Test Driver
Starts TLL HTTP server, sends requests, validates responses, shuts down.
"""
import subprocess
import time
import sys
import os
import signal
import urllib.request
import urllib.error
import json

PORT = 18091
BASE = f"http://127.0.0.1:{PORT}"
PASSED = 0
FAILED = 0

def log(msg):
    print(msg, flush=True)

def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        log(f"PASS: {name}")
        PASSED += 1
    else:
        log(f"FAIL: {name} {detail}")
        FAILED += 1

def http_get(path, headers=None):
    hdrs = {"Connection": "close"}
    if headers: hdrs.update(headers)
    req = urllib.request.Request(BASE + path, headers=hdrs)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = resp.status, dict(resp.headers), resp.read().decode('utf-8', errors='replace')
                time.sleep(0.15)
                return result
        except urllib.error.HTTPError as e:
            result = e.code, dict(e.headers), e.read().decode('utf-8', errors='replace')
            time.sleep(0.15)
            return result
        except (ConnectionResetError, OSError) as e:
            if attempt < 2:
                time.sleep(0.5)
                continue
            raise

def http_post(path, body, content_type="text/plain"):
    data = body.encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": content_type, "Connection": "close"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = resp.status, dict(resp.headers), resp.read().decode('utf-8', errors='replace')
                time.sleep(0.15)
                return result
        except urllib.error.HTTPError as e:
            result = e.code, dict(e.headers), e.read().decode('utf-8', errors='replace')
            time.sleep(0.15)
            return result
        except (ConnectionResetError, OSError) as e:
            if attempt < 2:
                time.sleep(0.5)
                continue
            raise

def main():
    # Find tllvm - use platform-specific binary name
    # On Linux/macOS, tllvm.exe may exist in repo (Windows prebuilt) but is not executable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if sys.platform == "win32":
        tllvm = os.path.join(repo_root, "host", "c", "tllvm.exe")
    else:
        tllvm = os.path.join(repo_root, "host", "c", "tllvm")
        # Ensure executable permission on Unix
        if os.path.exists(tllvm):
            os.chmod(tllvm, 0o755)
    tllc = os.path.join(repo_root, "tools", "TLLC", "tllc.tllbc")
    server_tll = os.path.join(script_dir, "gate_http_server.tll")
    server_bc = os.path.join(script_dir, "gate_http_server.tllbc")

    # Compile server
    log("=== Compiling HTTP server test ===")
    compile_result = subprocess.run([tllvm, tllc, "compile", server_tll, "-o", server_bc],
                                     capture_output=True, text=True, cwd=repo_root)
    if compile_result.returncode != 0:
        log(f"Compile failed: {compile_result.stderr}")
        sys.exit(1)
    log("Compile OK")

    # Start server
    log("=== Starting HTTP server ===")
    proc = subprocess.Popen([tllvm, server_bc],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            cwd=repo_root)
    time.sleep(2)

    # Wait for server to be ready
    ready = False
    for i in range(10):
        try:
            status, _, _ = http_get("/")
            if status == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not ready:
        log("FAIL: Server did not become ready")
        proc.kill()
        sys.exit(1)
    log("Server ready")

    try:
        # Gate 1: Basic GET /
        log("--- Gate 1: Basic GET / ---")
        status, headers, body = http_get("/")
        check("GET / returns 200", status == 200, f"got {status}")
        check("GET / body correct", body == "Hello TLL HTTP Server", f"got: {body}")
        check("GET / Content-Type present", "Content-Type" in headers)

        # Gate 2: Query parsing
        log("--- Gate 2: Query parsing ---")
        status, headers, body = http_get("/search?q=test&page=2")
        check("Query returns 200", status == 200)
        check("Query q parsed", '"q":"test"' in body, f"got: {body}")
        check("Query page parsed", '"page":"2"' in body, f"got: {body}")

        # Gate 3: Headers
        log("--- Gate 3: Request headers ---")
        status, headers, body = http_get("/headers", headers={"User-Agent": "TLL-Gate-Test/1.0"})
        check("Headers returns 200", status == 200)
        check("User-Agent echoed", "TLL-Gate-Test/1.0" in body, f"got: {body}")

        # Gate 4: Custom response headers + 201
        log("--- Gate 4: Custom headers + 201 ---")
        status, headers, body = http_get("/create")
        check("Create returns 201", status == 201, f"got {status}")
        check("X-Custom-Header present", "X-Custom-Header" in headers, f"headers: {list(headers.keys())}")
        check("X-Custom-Header value correct", headers.get("X-Custom-Header") == "TLL-OS",
              f"got: {headers.get('X-Custom-Header')}")
        check("Body correct", '"created":true' in body, f"got: {body}")

        # Gate 5: 404
        log("--- Gate 5: 404 status ---")
        status, headers, body = http_get("/notfound")
        check("Notfound returns 404", status == 404, f"got {status}")
        check("404 body correct", body == "Not Found", f"got: {body}")

        # Gate 6: POST body
        log("--- Gate 6: POST body echo ---")
        status, headers, body = http_post("/echo", "test payload 123")
        check("POST returns 200", status == 200, f"got {status}")
        check("POST body echoed", body == "Echo: test payload 123", f"got: {body}")

        # Gate 7: 500 error
        log("--- Gate 7: 500 error status ---")
        status, headers, body = http_get("/error")
        check("Error returns 500", status == 500, f"got {status}")
        check("500 body correct", body == "Internal Error", f"got: {body}")

        # Gate 8: Unknown path 404
        log("--- Gate 8: Unknown path ---")
        status, headers, body = http_get("/nonexistent/path")
        check("Unknown path returns 404", status == 404, f"got {status}")

    finally:
        # Shutdown server
        log("=== Shutting down server ===")
        proc.kill()
        proc.wait(timeout=5)
        # Cleanup
        # Keep server_bc for re-runs; CI will clean workspace

    # Results
    log("")
    log("=== Results ===")
    log(f"Passed: {PASSED}")
    log(f"Failed: {FAILED}")
    if FAILED == 0:
        log("ALL HTTP SERVER GATES PASSED")
        sys.exit(0)
    else:
        log("SOME GATES FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
