#!/usr/bin/env python3
"""
Servidor temporal de mantenimiento.
Sirve maintenance.html con HTTP 503 en puerto 5000 para cualquier peticion.
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SCRIPT_DIR, 'maintenance.html'), 'rb') as f:
    HTML = f.read()


class Handler(BaseHTTPRequestHandler):
    def _respond(self):
        self.send_response(503)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Retry-After', '15')
        self.end_headers()
        self.wfile.write(HTML)

    def do_GET(self):
        self._respond()

    def do_POST(self):
        self._respond()

    def do_PUT(self):
        self._respond()

    def do_DELETE(self):
        self._respond()

    def do_OPTIONS(self):
        self._respond()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 5000), Handler)
    print('Mantenimiento activo en http://0.0.0.0:5000')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print('Mantenimiento detenido')
