#!/usr/bin/env python3
"""
Deterministic HTTP Test Server for TLL httpc cross-platform validation.
Provides fixed endpoints that return predictable responses.
Usage: python3 test_server.py [port]
"""
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer

class DeterministicHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs for clean CI output

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Test-Server', 'deterministic')
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, status=200, content_type='text/plain'):
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Test-Server', 'deterministic')
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
            self._send_json({
                "method": "GET",
                "path": self.path,
                "headers": dict(self.headers)
            })
        elif self.path.startswith('/status/'):
            try:
                code = int(self.path.split('/')[-1])
                self._send_json({"status": code}, status=code)
            except:
                self._send_json({"error": "invalid status code"}, status=400)
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''

        if self.path == '/echo':
            self._send_json({
                "method": "POST",
                "path": self.path,
                "headers": dict(self.headers),
                "body": body
            })
        elif self.path == '/json':
            try:
                data = json.loads(body) if body else {}
                self._send_json({"received": data, "ok": True})
            except:
                self._send_json({"error": "invalid JSON", "ok": False}, status=400)
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''

        if self.path == '/echo':
            self._send_json({
                "method": "PUT",
                "path": self.path,
                "headers": dict(self.headers),
                "body": body
            })
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_DELETE(self):
        if self.path == '/echo':
            self._send_json({
                "method": "DELETE",
                "path": self.path,
                "headers": dict(self.headers)
            })
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
    server = ThreadingHTTPServer(('127.0.0.1', port), DeterministicHandler)
    print(f"Deterministic HTTP Test Server running on http://127.0.0.1:{port}")
    print("Endpoints: /status, /headers, /json, /body, /echo, /status/{code}")
    sys.stdout.flush()
    server.serve_forever()
