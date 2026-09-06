#!/usr/bin/env python3
"""
Deterministic HTTPS Test Server for TLL httpc Level 3 validation.
Generates a self-signed certificate at startup and serves HTTPS on 127.0.0.1.

Usage: python3 test_https_server.py [port]
Default port: 18443

Endpoints (same as test_server.py):
  /status    -> 200 JSON {"status":"ok","code":200}
  /headers   -> 200 JSON with received headers
  /json      -> 200 JSON
  /body      -> 200 text
  /echo      -> 200 JSON echo (GET/POST)
  /status/{code} -> custom status code
"""
import sys
import os
import ssl
import json
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer


def generate_self_signed_cert():
    """Generate a self-signed certificate. Priority: repo PEM files > cryptography > openssl."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cert_file = os.path.join(script_dir, "test_cert.pem")
    key_file = os.path.join(script_dir, "test_key.pem")

    # Priority 1: use pre-generated PEM files in repo (works on all platforms)
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file

    # Priority 2: generate with cryptography library
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        import ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TLL Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.IPv4Address('127.0.0.1'))]), critical=False)
            .sign(key, hashes.SHA256())
        )
        with open(key_file, "wb") as f:
            f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return cert_file, key_file
    except ImportError:
        pass

    # Priority 3: generate with openssl command
    import subprocess
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", key_file,
        "-out", cert_file, "-days", "365", "-nodes",
        "-subj", "/C=US/O=TLL Test/CN=127.0.0.1",
        "-addext", "subjectAltName=IP:127.0.0.1"
    ], check=True, capture_output=True)
    return cert_file, key_file


class DeterministicHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs for clean CI output

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Test-Server', 'https-deterministic')
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, status=200, content_type='text/plain'):
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Test-Server', 'https-deterministic')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/status':
            self._send_json({"status": "ok", "code": 200, "https": True})
        elif self.path == '/headers':
            headers = {}
            for key, value in self.headers.items():
                headers[key] = value
            self._send_json({"headers": headers})
        elif self.path == '/json':
            self._send_json({"name": "TLL", "version": "1.0", "https": True})
        elif self.path == '/body':
            self._send_text("Hello from HTTPS test server!")
        elif self.path == '/echo':
            self._send_json({"method": "GET", "path": self.path, "headers": dict(self.headers)})
        elif self.path.startswith('/status/'):
            try:
                code = int(self.path.split('/')[-1])
                self._send_json({"status": code, "https": True}, status=code)
            except:
                self._send_json({"error": "invalid status code"}, status=400)
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        if self.path == '/echo':
            self._send_json({"method": "POST", "path": self.path, "headers": dict(self.headers), "body": body})
        else:
            self._send_json({"error": "not found", "path": self.path}, status=404)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18443

    cert_file, key_file = generate_self_signed_cert()
    print(f"Certificate: {cert_file}")
    print(f"Key: {key_file}")

    server = ThreadingHTTPServer(('127.0.0.1', port), DeterministicHandler)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    server.socket = context.wrap_socket(server.socket, server_side=True)

    print(f"Deterministic HTTPS Test Server running on https://127.0.0.1:{port}")
    print("Endpoints: /status, /headers, /json, /body, /echo, /status/{code}")
    print("NOTE: This server uses a SELF-SIGNED certificate.")
    print("      Default httpc.get() will FAIL certificate validation (expected for Gate 2).")
    print("      Use httpc.request({url: ..., insecure: true}) for Gate 1 success.")
    sys.stdout.flush()
    server.serve_forever()
