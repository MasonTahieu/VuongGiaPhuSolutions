"""Local preview server for site-moi with the content types GitHub Pages uses.

Python's built-in server takes MIME types from the Windows registry, where .webp is often missing and
gets served as application/octet-stream.

    python tools/serve.py [port]
"""
import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site-moi")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".woff2": "font/woff2",
        ".svg": "image/svg+xml",
        ".webmanifest": "application/manifest+json",
        ".js": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".xml": "application/xml",
    }

    def end_headers(self):
        # Without this browsers reuse a cached page for a while and keep showing an older design;
        # "no-cache" makes them revalidate every time (a cheap 304 when nothing changed).
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


class Server(http.server.ThreadingHTTPServer):
    # The default backlog of 5 overflows when a page asks for many images at once (through ngrok above all),
    # and Windows then refuses the extra connections, which the visitor sees as broken images (502).
    request_queue_size = 128


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    handler = functools.partial(Handler, directory=SITE)
    with Server(("127.0.0.1", port), handler) as httpd:
        print("Serving %s on http://127.0.0.1:%d" % (SITE, port))
        httpd.serve_forever()
