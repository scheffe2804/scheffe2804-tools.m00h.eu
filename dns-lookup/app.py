import subprocess, json, re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DNS Lookup – dns.m00h.eu</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: #0f1117; color: #e2e8f0; min-height: 100vh; padding: 2rem 1rem; }
h1 { color: #7dd3fc; font-size: 1.6rem; margin-bottom: .3rem; }
p.sub { color: #94a3b8; margin-bottom: 1.5rem; font-size: .9rem; }
form { display: flex; flex-wrap: wrap; gap: .75rem; max-width: 720px; }
input[name=domain] { flex: 1; min-width: 200px; padding: .6rem .9rem;
  background: #1a1f2e; border: 1px solid #2d3748; border-radius: 8px;
  color: #e2e8f0; font-size: 1rem; outline: none; }
input[name=domain]:focus { border-color: #7dd3fc; }
select { padding: .6rem .9rem; background: #1a1f2e; border: 1px solid #2d3748;
  border-radius: 8px; color: #e2e8f0; font-size: 1rem; outline: none; }
button { padding: .6rem 1.4rem; background: #0369a1; color: #fff;
  border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
button:hover { background: #0284c7; }
#results { margin-top: 1.5rem; max-width: 720px; }
pre { background: #1a1f2e; border: 1px solid #2d3748; border-radius: 10px;
  padding: 1.2rem; white-space: pre-wrap; word-break: break-all;
  font-size: .85rem; color: #7dd3fc; line-height: 1.6; }
.err { color: #f87171; }
.back { display:inline-block; margin-top:1.5rem; color:#7dd3fc; font-size:.85rem; text-decoration:none; }
</style>
</head>
<body>
<h1>DNS Lookup</h1>
<p class="sub">nslookup / dig – A, AAAA, MX, TXT, NS, CNAME, SOA, PTR</p>
<form method="get" action="/lookup">
  <input name="domain" placeholder="example.com oder IP" value="DOMAIN_VAL" autofocus>
  <select name="type">
    TYPE_OPTIONS
  </select>
  <button type="submit">Abfragen</button>
</form>
RESULTS_BLOCK
<a class="back" href="https://tools.m00h.eu">&larr; Alle Tools</a>
</body></html>"""

TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA", "PTR", "ANY"]

def safe(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def run_dig(domain, qtype):
    try:
        result = subprocess.run(
            ["dig", "+noall", "+answer", "+authority", "+time=5", "+tries=2",
             domain, qtype],
            capture_output=True, text=True, timeout=10
        )
        out = result.stdout.strip()
        if not out:
            out = result.stderr.strip() or "(keine Antwort / NXDOMAIN)"
        return out
    except subprocess.TimeoutExpired:
        return "Timeout: DNS-Server antwortet nicht."
    except Exception as e:
        return f"Fehler: {e}"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_page(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok"); return

        qs = parse_qs(parsed.query)
        domain = (qs.get("domain", [""])[0]).strip()
        qtype  = (qs.get("type",   ["A"])[0]).upper()
        if qtype not in TYPES: qtype = "A"

        opts = "".join(
            f'<option{" selected" if t==qtype else ""}>{t}</option>' for t in TYPES
        )
        html = HTML.replace("TYPE_OPTIONS", opts).replace("DOMAIN_VAL", safe(domain))

        if parsed.path == "/lookup" and domain:
            output = run_dig(domain, qtype)
            cls = "err" if output.startswith(("Fehler","Timeout")) else ""
            block = f'<div id="results"><pre class="{cls}">{safe(output)}</pre></div>'
        else:
            block = ""

        self.send_page(html.replace("RESULTS_BLOCK", block))

if __name__ == "__main__":
    s = HTTPServer(("0.0.0.0", 8080), Handler)
    s.serve_forever()
