#!/usr/bin/env python3
"""
Master Institutional Research Portal & Intelligence Hub File Server
===================================================================
Serves company research dossiers (docs/blogs) and the latest Market Intelligence
and Portfolio Audit reports (docs/reports) on http://localhost:9050/.
Maintained as a persistent background daemon via macOS launchd (com.portfolio.blogs.fileserver).
"""

import os
import sys
import glob
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLOGS_DIR = os.path.join(BASE_DIR, "docs/blogs")
NEWSLETTERS_DIR = os.path.join(BASE_DIR, "docs/reports")
PORT = 9050

def ensure_symlinks():
    """Ensure relative symlink docs/blogs/reports -> ../reports and newsletters -> ../reports exist."""
    os.makedirs(BLOGS_DIR, exist_ok=True)
    os.makedirs(NEWSLETTERS_DIR, exist_ok=True)
    for sym_name in ("newsletters", "reports"):
        symlink_path = os.path.join(BLOGS_DIR, sym_name)
        if not os.path.exists(symlink_path) and not os.path.islink(symlink_path):
            try:
                os.symlink("../reports", symlink_path)
                print(f"🔗 Created symlink: {symlink_path} -> ../reports", flush=True)
            except Exception as e:
                print(f"⚠️ Could not create symlink {symlink_path}: {e}", flush=True)

def get_latest_report(pattern):
    """Find the single latest report matching the glob pattern in newsletters dir."""
    matches = sorted(glob.glob(os.path.join(NEWSLETTERS_DIR, pattern)), reverse=True)
    return os.path.basename(matches[0]) if matches else None

class DossierHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BLOGS_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')

        # Canonical dynamic aliases to latest reports
        alias_map = {
            '/market-intelligence': 'Daily_Market_Intelligence_*.html',
            '/latest/market-intelligence': 'Daily_Market_Intelligence_*.html',
            '/portfolio-audit': 'Portfolio_Audit_*.html',
            '/latest/portfolio-audit': 'Portfolio_Audit_*.html',
            '/us-market-intelligence': 'Daily_US_Market_Intelligence_*.html',
            '/latest/us-market-intelligence': 'Daily_US_Market_Intelligence_*.html',
            '/us-portfolio-audit': 'US_Portfolio_Audit_*.html',
            '/latest/us-portfolio-audit': 'US_Portfolio_Audit_*.html',
        }

        if path in alias_map:
            latest_file = get_latest_report(alias_map[path])
            if latest_file:
                # Redirect to the specific dated file
                self.send_response(302)
                self.send_header('Location', f'/newsletters/{latest_file}')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.end_headers()
                return
            else:
                self.send_error(404, f"No report found matching {alias_map[path]}")
                return

        # Direct newsletters route fallback
        if parsed.path.startswith('/newsletters/'):
            filename = parsed.path.replace('/newsletters/', '', 1)
            target = os.path.join(NEWSLETTERS_DIR, filename)
            if os.path.isfile(target):
                self.send_response(200)
                if filename.endswith('.html'):
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(os.path.getsize(target)))
                self.end_headers()
                with open(target, 'rb') as f:
                    self.wfile.write(f.read())
                return

        return super().do_GET()

    def end_headers(self):
        # Disable caching so changes to dossiers, reports, or index are immediately reflected
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def run():
    ensure_symlinks()
    print(f"Starting Dossier Blog & Intelligence File Server on port {PORT}...", flush=True)
    print(f"Serving blogs directory: {BLOGS_DIR}", flush=True)
    print(f"Serving newsletters directory: {NEWSLETTERS_DIR}", flush=True)
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, DossierHTTPRequestHandler)
    print(f"File server ready at http://localhost:{PORT}/", flush=True)
    httpd.serve_forever()

if __name__ == '__main__':
    run()
