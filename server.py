"""Simple HTTP server that serves page.html and a small counter API."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
PORT = 8000
HTML_FILE = Path(__file__).parent / "page.html"


class AppHandler(BaseHTTPRequestHandler):
    counter = 0

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/index.html", "/page.html"):
            self._serve_html()
        elif parsed.path == "/api/counter":
            self._handle_counter(parse_qs(parsed.query))
        else:
            self._send(404, "text/plain", b"Not Found")

    def _serve_html(self):
        try:
            body = HTML_FILE.read_bytes()
        except FileNotFoundError:
            self._send(500, "text/plain", b"page.html is missing")
            return
        self._send(200, "text/html; charset=utf-8", body)

    def _handle_counter(self, query):
        action = (query.get("action") or ["get"])[0]
        if action == "increment":
            AppHandler.counter += 1
        elif action == "decrement":
            AppHandler.counter -= 1
        elif action == "reset":
            AppHandler.counter = 0

        payload = json.dumps({"value": AppHandler.counter}).encode("utf-8")
        self._send(200, "application/json", payload)

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


def main():
    server = HTTPServer((HOST, PORT), AppHandler)
    print(f"Serving on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
