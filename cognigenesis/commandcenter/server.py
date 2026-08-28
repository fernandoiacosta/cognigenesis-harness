from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from cognigenesis.commandcenter.store import CommandCenterStore


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Cognigenesis Command Center</title>
<style>
:root{--bg:#05070D;--surface:#0B1020;--elev:#11182B;--border:#1B2440;--text:#F3F7FF;--muted:#A7B0C3;--cyan:#62F5FF;--violet:#8B7CFF;--magenta:#C96CFF;--green:#54E6A8;--amber:#FFC857;--red:#FF6B7A}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#11182B 0,#05070D 40%);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}
header{display:flex;align-items:center;justify-content:space-between;padding:18px 24px;border-bottom:1px solid var(--border);position:sticky;top:0;background:rgba(5,7,13,.92);backdrop-filter:blur(16px)}
.brand{font-weight:800;letter-spacing:.18em;color:var(--cyan)}.version{color:var(--violet)}#updated{color:var(--muted);font-size:12px}
main{padding:20px;display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px;max-width:1800px;margin:auto}
.card{background:rgba(11,16,32,.88);border:1px solid var(--border);border-radius:16px;padding:16px;min-width:0;box-shadow:0 12px 50px rgba(0,0,0,.25)}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.15em;color:var(--muted);margin:0 0 14px}.span4{grid-column:span 4}.span6{grid-column:span 6}.span8{grid-column:span 8}.span12{grid-column:span 12}
.metricrow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.metric{padding:12px;border:1px solid var(--border);border-radius:12px;background:var(--elev)}.metric b{display:block;font-size:24px;color:var(--cyan)}
.item{padding:10px 0;border-bottom:1px solid rgba(27,36,64,.7)}.item:last-child{border:0}.muted{color:var(--muted)}.tag{display:inline-block;padding:2px 7px;border-radius:999px;border:1px solid var(--border);font-size:11px;margin-right:6px}.ok{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}.violet{color:var(--violet)}.magenta{color:var(--magenta)}
pre{white-space:pre-wrap;word-break:break-word;margin:0;color:var(--muted);font:12px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;max-height:460px;overflow:auto}
.agentgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}.agent{background:var(--elev);border:1px solid var(--border);border-radius:12px;padding:10px}
.empty{color:var(--muted);font-style:italic;padding:8px 0}
@media(max-width:900px){.span4,.span6,.span8,.span12{grid-column:span 12}main{padding:12px}.metricrow{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div><span class="brand">COGNIGENESIS</span> <span class="version">COMMAND CENTER</span></div><div id="updated">waiting for runtime…</div></header>
<main>
<section class="card span4"><h2>Cognitive State</h2><div class="metricrow">
<div class="metric"><b id="hyp">0</b><span class="muted">hypotheses</span></div>
<div class="metric"><b id="contra">0</b><span class="muted">contradictions</span></div>
<div class="metric"><b id="questions">0</b><span class="muted">open questions</span></div>
</div><div id="hypotheses"></div></section>
<section class="card span8"><h2>Mission Task Graph</h2><div id="tasks" class="empty">No tasks yet.</div></section>
<section class="card span8"><h2>Teams & Agents</h2><div id="teams" class="empty">No team active.</div></section>
<section class="card span4"><h2>Evidence</h2><div id="evidence" class="empty">No evidence recorded.</div></section>
<section class="card span12"><h2>Runtime Event Stream</h2><pre id="events">No events yet.</pre></section>
</main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function items(target,arr,render,empty){document.getElementById(target).innerHTML=arr?.length?arr.map(render).join(''):'<div class="empty">'+empty+'</div>'}
async function refresh(){
 try{
  const d=await fetch('/api/state',{cache:'no-store'}).then(r=>r.json());
  document.getElementById('updated').textContent=d.updated_at?'updated '+new Date(d.updated_at).toLocaleTimeString():'waiting for runtime…';
  const c=d.cognition||{},m=c.metrics||{};
  document.getElementById('hyp').textContent=m.active_hypotheses||0;document.getElementById('contra').textContent=m.contradictions||0;document.getElementById('questions').textContent=m.unresolved_questions||0;
  items('hypotheses',c.hypotheses,h=>'<div class="item"><span class="tag violet">'+esc(h.status)+'</span>'+esc(h.claim)+'<div class="muted">confidence '+esc(h.confidence)+'</div></div>','No hypotheses recorded.');
  items('evidence',c.evidence,e=>'<div class="item"><span class="tag '+(e.polarity==='contradicts'?'bad':e.polarity==='supports'?'ok':'')+'">'+esc(e.polarity)+'</span>'+esc(e.claim)+'<div class="muted">'+esc(e.source||'no source')+'</div></div>','No evidence recorded.');
  items('tasks',d.tasks,t=>'<div class="item"><span class="tag">'+esc(t.status)+'</span><b>'+esc(t.title)+'</b><div class="muted">'+esc(t.description||'')+(t.assigned_agent?' · '+esc(t.assigned_agent):'')+'</div></div>','No tasks yet.');
  items('teams',d.teams,t=>'<div class="item"><b>'+esc(t.name)+'</b><div class="muted">'+esc(t.objective)+'</div><div class="agentgrid">'+(t.agents||[]).map(a=>'<div class="agent"><span class="violet">'+esc(a.name)+'</span><div>'+esc(a.role)+'</div><div class="muted">messages '+esc(a.pending_messages||0)+'</div></div>').join('')+'</div></div>','No team active.');
  document.getElementById('events').textContent=(d.events||[]).slice(-40).map(e=>e.time+'  '+e.type+'  '+JSON.stringify(e.payload)).join('\n')||'No events yet.';
 }catch(e){document.getElementById('updated').textContent='state unavailable'}
}
refresh();setInterval(refresh,1000);
</script>
</body></html>"""


def serve_command_center(workspace: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    state_path = workspace / ".cognigenesis" / "command-center.json"
    store = CommandCenterStore(state_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/state":
                body = json.dumps(store.load(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path in {"/", "/index.html"}:
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
