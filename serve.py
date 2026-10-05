#!/usr/bin/env python3
"""AEGIS offline server. Serves ONLY this drive\'s files. Range support for .gguf streaming."""
import argparse, http.server, json, os, re, socket, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw): super().__init__(*a, directory=ROOT, **kw)
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes"); self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store"); super().end_headers()
    def log_message(self, fmt, *args): sys.stderr.write("[aegis] " + fmt % args + "\n")
    def do_GET(self):
        if self.path == "/api/status":
            wdir = os.path.join(ROOT, "models", "weights")
            ws = [f for f in os.listdir(wdir) if f.endswith(".gguf")] if os.path.isdir(wdir) else []
            body = json.dumps({"server": "aegis-drive", "offline": True, "weights_present": ws}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        rng = self.headers.get("Range")
        if rng: return self._range(rng)
        return super().do_GET()
    def _range(self, rng):
        path = self.translate_path(self.path)
        if not os.path.isfile(path): self.send_error(404); return
        size = os.path.getsize(path)
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        if not m: self.send_error(416); return
        start = int(m.group(1)) if m.group(1) else 0
        end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
        if start > end: self.send_error(416); return
        length = end - start + 1
        self.send_response(206); self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length)); self.end_headers()
        with open(path, "rb") as f:
            f.seek(start); remaining = length
            while remaining > 0:
                chunk = f.read(min(1 << 20, remaining))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): break
                remaining -= len(chunk)
def lan_ips():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]; s.close(); return [ip]
    except Exception: return ["127.0.0.1"]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--lan", action="store_true"); a = ap.parse_args()
    srv = http.server.ThreadingHTTPServer(("0.0.0.0" if a.lan else "127.0.0.1", a.port), Handler)
    print(f"AEGIS server online. Root: {ROOT}"); print(f"  This device: http://127.0.0.1:{a.port}/")
    if a.lan:
        for ip in lan_ips(): print(f"  On this Wi-Fi: http://{ip}:{a.port}/")
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\nstopped.")
if __name__ == "__main__": main()
