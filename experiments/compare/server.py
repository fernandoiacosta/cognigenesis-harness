"""Localhost-only UI for Cognigenesis Compare. No account/cloud/public hosting.

Run: python experiments/compare/server.py
Security: binds 127.0.0.1; no CORS; no script/tool execution from model prose.
"""
from __future__ import annotations
import importlib.util
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("cognigenesis_compare",HERE/"compare.py")
compare_module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare_module)
RUN_LOCK=threading.Lock()
MAX_PROMPT=10000
MAX_MODEL=150

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in {"/","/index.html"}:
            self.send_error(404)
            return
        self.respond((HERE/"index.html").read_bytes(),"text/html; charset=utf-8")

    def do_POST(self):
        if self.path!="/api/compare":
            self.send_error(404)
            return
        try:
            content_length=int(self.headers.get("Content-Length","0"))
            if not 0<content_length<=20000:
                raise ValueError("Invalid request length")
            body=json.loads(self.rfile.read(content_length).decode())
            prompt=body.get("prompt","")
            model=body.get("model","")
            if not isinstance(prompt,str) or not 0<len(prompt.strip())<=MAX_PROMPT:
                raise ValueError("Prompt must be 1–10000 characters")
            if not isinstance(model,str) or not 0<len(model.strip())<=MAX_MODEL:
                raise ValueError("Provide an explicit installed model ID")
            if not RUN_LOCK.acquire(blocking=False):
                self.send_json({"error":"A comparison is already running. Retry after completion."},429)
                return
            try:
                key=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+'-'+uuid4().hex[:8]
                path=HERE/"results"/(key+".json")
                out=compare_module.compare(prompt,model,path)
                self.send_json({"id":key,"records":out["records"]},200)
            finally:
                RUN_LOCK.release()
        except (ValueError,TypeError,json.JSONDecodeError) as exc:
            self.send_json({"error":str(exc)},400)
        except Exception as exc:
            self.send_json({"error":"Comparison failed: "+type(exc).__name__},500)

    def respond(self,data,mime,status=200):
        self.send_response(status)
        self.send_header("Content-Type",mime)
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'unsafe-inline' 'self'; style-src 'unsafe-inline' 'self'; connect-src 'self'; object-src 'none'")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self,body,status):
        self.respond(json.dumps(body).encode(),"application/json; charset=utf-8",status)

def main():
    host,port="127.0.0.1",8787
    print(f"Cognigenesis Compare local preview: http://{host}:{port}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()

if __name__=="__main__": main()
