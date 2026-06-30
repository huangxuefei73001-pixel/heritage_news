#!/usr/bin/env python3
from __future__ import annotations

import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


def bing_news_rss(query: str) -> bytes:
    q = urllib.parse.quote(query)
    url = f"https://www.bing.com/news/search?q={q}&format=rss"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            body = b"RSSHub shim ok.\nRoutes:\n- /reuters/world\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/reuters/world"):
            body = bing_news_rss("Reuters Lebanon heritage")
            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        print(fmt % args)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 1200), Handler).serve_forever()
