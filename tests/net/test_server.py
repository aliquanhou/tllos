#!/usr/bin/env python3
"""
Deterministic HTTP Test Server for TLL httpc cross-platform validation.
Supports connection counting and X-Connection-ID for Level 4 verification.
Usage: python3 test_server.py [port] [idle_timeout_seconds]
"""
import sys
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_stats_lock = threading.Lock()
_connection_count = 0
_request_count = 0


def get_stats():
    with _stats_lock:
        return {"connections": _connection_count, "requests": _request_count}


def reset_stats():
    global _connection_count, _request_count
    with _stats_lock:
        _connection_count = 0
        _request_count = 0


def _inc_connection():
    global _connection_count
    with _stats_lock:
        _connection_count += 1


def _inc_request():
    global _request_count
    with _stats_lock:
        _request_count += 1


class CountingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True


class DeterministicHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def setup(self):
        _inc_connection()
        super().setup()
        self.connection.settimeout(self.server.idle_timeout)
        with _stats_lock:
            self.conn_id = _connection_count

    def _common_headers(self):
        self.send_header('X-Test-Server', 'deterministic')
        self.send_header('X-Connection-ID', str(getattr(self, 'conn_id', 0)))

    def _send_json(self, data, status=200, extra_headers=None):
        _inc_request()
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self._common_headers()
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, status=200, content_type='text/plain', extra_headers=None):
        _inc_request()
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self._common_headers()
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/status':
            self._send_json({"status": "ok", "code": 200})
        elif self.path == '/headers':
            headers = {}
            for key, value in self.headers.items():
                headers[key] = value
            self._send_json({"headers": headers})
        elif self.path == '/json':
            self._send_json({"name": "TLL", "version": "1.0", "active": True})
        elif self.path == '/body':
            self._send_text("Hello from deterministic test server!")
        elif self.path == '/echo':
            self._send_json({"method": "GET", "path": self.path, "headers": dict(self.headers)})
        elif self.path == '/stats':
            stats = get_stats()
            body = json.dumps(stats).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self._common_headers()
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/reset-stats':
            reset_stats()
            self._send_json({"reset": True})
        elif self.path == '/close':
            self._send_json({"closed": True}, extra_headers={"Connection": "close"})
        elif self.path.startswith('/sleep/'):
            try:
                seconds = float(self.path.split('/')[-1])
                time.sleep(min(seconds, 10))
                self._send_json({"slept": seconds})
            except Exception:
                self._send_json({"error": "invalid sleep duration"}, status=400)
        elif self.path.startswith('/status/'):
            try:
                code = int(self.path.split('/')[-1])
                self._send_json({"status": code}, status=code)
            except Exception:
                self._send_json({"error": "invalid status code"}, status=400)
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        if self.path == '/echo':
            self._send_json({"method": "POST", "path": self.path, "headers": dict(self.headers), "body": body})
        elif self.path == '/json':
            try:
                data = json.loads(body) if body else {}
                self._send_json({"received": data, "ok": True})
            except Exception:
                self._send_json({"error": "invalid JSON", "ok": False}, status=400)
        elif self.path == '/close':
            self._send_json({"closed": True, "method": "POST"}, extra_headers={"Connection": "close"})
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        if self.path == '/echo':
            self._send_json({"method": "PUT", "path": self.path, "headers": dict(self.headers), "body": body})
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_DELETE(self):
        if self.path == '/echo':
            self._send_json({"method": "DELETE", "path": self.path, "headers": dict(self.headers)})
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
    idle_timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    server = CountingHTTPServer(('127.0.0.1', port), DeterministicHandler)
    server.idle_timeout = idle_timeout
    print(f"Deterministic HTTP Test Server running on http://127.0.0.1:{port}")
    print(f"Idle connection timeout: {idle_timeout}s")
    sys.stdout.flush()
    server.serve_forever()
