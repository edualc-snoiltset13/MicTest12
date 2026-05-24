"""Simple Python web server that serves a tabbed HTML website.

Usage:
    python3 app.py [port]

Defaults to port 8000. Open http://localhost:8000 in a browser.
"""

import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class TabbedSiteHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", ""):
            self.path = "/tabs.html"
        return super().do_GET()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    directory = Path(__file__).resolve().parent

    handler = lambda *args, **kwargs: TabbedSiteHandler(
        *args, directory=str(directory), **kwargs
    )
    server = HTTPServer(("0.0.0.0", port), handler)

    print(f"Serving tabbed website on http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
