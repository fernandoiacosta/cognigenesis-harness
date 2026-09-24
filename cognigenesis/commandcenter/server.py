from __future__ import annotations

import json
import ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from cognigenesis.commandcenter.store import CommandCenterStore
from cognigenesis.config import load_settings


def dashboard_config() -> dict[str, str | None]:
    """Public dashboard metadata; credentials and endpoint URLs stay server-side."""
    settings = load_settings()
    return {"provider": settings.provider, "model": settings.model,
            "connection": ("local" if settings.ollama_base_url.startswith(("http://127.0.0.1:", "http://localhost:")) else "network")
            if settings.provider == "ollama" else "configured"}


def _loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>Cognigenesis · Harness Dashboard</title>
<style>
:root{--bg:#080b13;--side:#0c111d;--panel:#111827;--edge:#263146;--ink:#eef3ff;--dim:#9caac2;--aqua:#62f5ff;--lilac:#af92ff;--pink:#ed94ef;--good:#54e6a8;--warn:#f2bd70;--bad:#ff8192}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 80% -20%,#182444 0,transparent 46%),var(--bg);color:var(--ink);font:14px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}button,input{font:inherit}button{cursor:pointer}a{color:inherit;text-decoration:none}
.shell{min-height:100vh;display:grid;grid-template-columns:236px minmax(0,1fr)}aside{position:sticky;top:0;height:100vh;padding:26px 15px;background:var(--side);border-right:1px solid var(--edge);display:flex;flex-direction:column;gap:30px}.identity{display:flex;align-items:center;gap:11px;padding:5px 9px}.glyph{display:grid;place-items:center;width:37px;height:37px;flex:none;border-radius:11px;background:linear-gradient(135deg,#c874f4,#62f5ff);color:#07101c;font-size:24px;font-weight:900;box-shadow:0 0 27px #62f5ff30}.identity strong{letter-spacing:.1em;font-size:12px}.identity small{display:block;color:var(--dim);letter-spacing:.12em}.navlabel{padding:0 14px;color:#7f91ab;font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase}.nav{display:grid;gap:5px}.nav button{width:100%;text-align:left;background:transparent;border:1px solid transparent;border-radius:10px;color:var(--dim);padding:11px 13px}.nav button:hover,.nav button:focus-visible{color:var(--ink);border-color:var(--edge)}.nav button.active{color:var(--aqua);background:#62f5ff10;border-color:#62f5ff33}.nav button span{display:inline-block;width:26px;font-size:17px;vertical-align:middle}.foot{margin-top:auto;border:1px solid var(--edge);border-radius:12px;padding:13px;color:var(--dim);font-size:12px}.foot strong{display:block;color:var(--good);font-size:11px;letter-spacing:.13em;text-transform:uppercase}
main{min-width:0;padding:24px clamp(16px,3vw,44px) 60px;max-width:1600px;width:100%;margin:0 auto}.top{display:flex;align-items:center;justify-content:space-between;gap:16px;border-bottom:1px solid var(--edge);padding-bottom:20px}.eyebrow{font-size:11px;font-weight:800;letter-spacing:.23em;color:var(--aqua);text-transform:uppercase}.top h1{font-size:clamp(24px,3vw,36px);letter-spacing:-.035em;margin:4px 0 0}.actions{display:flex;gap:9px;flex-wrap:wrap}.action{border:1px solid var(--edge);border-radius:10px;background:#182133;color:var(--ink);padding:9px 13px}.action:hover{border-color:var(--aqua)}.action.primary{color:#07101c;background:var(--aqua);border-color:var(--aqua);font-weight:700}.notice{margin:22px 0;padding:11px 14px;border:1px solid #af92ff40;background:#af92ff0e;border-radius:10px;color:#d1c8ec;font-size:12px}.view{display:none}.view.active{display:block}.hero{display:flex;justify-content:space-between;align-items:end;gap:14px;margin:29px 0 20px}.hero h2{font-size:23px;letter-spacing:-.02em;margin:0}.hero p{margin:4px 0 0;color:var(--dim)}.signal{display:inline-flex;gap:7px;align-items:center;color:var(--dim);font-size:12px}.dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 13px var(--good)}.dot.off{background:var(--warn);box-shadow:0 0 13px var(--warn)}
.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:15px}.card{grid-column:span 6;min-width:0;background:linear-gradient(145deg,#131e30,#0d1421);border:1px solid var(--edge);border-radius:16px;padding:19px;box-shadow:0 12px 45px #0002}.full{grid-column:span 12}.third{grid-column:span 4}.card h3{font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--dim);margin:0 0 18px}.cardheader{display:flex;justify-content:space-between;align-items:center;gap:12px}.cardheader h3{margin:0 0 14px}.small{color:var(--dim);font-size:12px}.big{font-size:31px;font-weight:750;letter-spacing:-.05em}.metric{display:flex;justify-content:space-between;align-items:end}.meter{height:5px;margin-top:15px;border-radius:5px;background:#273146;overflow:hidden}.meter span{display:block;height:100%;background:linear-gradient(90deg,var(--lilac),var(--aqua));max-width:100%}.model{color:var(--aqua);word-break:break-word;font-size:22px;font-weight:700}.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.pill{border:1px solid var(--edge);border-radius:999px;color:var(--dim);padding:3px 9px;font-size:11px}.pill.good{color:var(--good)}.pill.warn{color:var(--warn)}.row{padding:12px 0;border-bottom:1px solid var(--edge)}.row:last-child{border:0}.rowtitle{font-weight:650;overflow-wrap:anywhere}.rowmeta{color:var(--dim);font-size:12px;margin-top:3px;overflow-wrap:anywhere}.rowtop{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.badge{font-size:10px;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border-radius:6px;background:#a792ff23;color:#cebaff;white-space:nowrap}.badge.completed,.badge.supports{background:#54e6a820;color:var(--good)}.badge.failed,.badge.contradicts{background:#ff819222;color:var(--bad)}.badge.running{background:#62f5ff22;color:var(--aqua)}.empty{padding:24px 0;color:var(--dim)}.toolbar{display:flex;gap:8px;margin:0 0 16px}.toolbar input,.toolbar select{background:#111b2b;border:1px solid var(--edge);border-radius:9px;color:var(--ink);padding:10px 12px;min-width:0}.toolbar input{flex:1}.toolbar input:focus,.toolbar select:focus{outline:1px solid var(--aqua)}.timeline{border-left:1px solid var(--edge);margin-left:6px;padding-left:17px}.timeline .row{position:relative}.timeline .row:before{content:'';position:absolute;left:-22px;top:18px;width:8px;height:8px;border-radius:50%;background:var(--aqua)}.subgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:9px;margin-top:12px}.agent{border:1px solid var(--edge);border-radius:10px;padding:11px;background:#0b1321}.agent strong{color:var(--aqua)}.error{color:var(--bad)}
@media(max-width:900px){.shell{grid-template-columns:1fr}aside{position:static;height:auto;padding:12px;gap:10px}.nav{display:flex;overflow-x:auto}.nav button{white-space:nowrap}.navlabel,.foot{display:none}.identity{padding:0 7px}.card,.third{grid-column:span 12}main{padding:16px}.top{align-items:start}.actions{justify-content:end}}@media(max-width:560px){.top{display:block}.actions{margin-top:14px}.toolbar{flex-wrap:wrap}.toolbar input{min-width:100%}}
</style>
</head>
<body><div class="shell"><aside><div class="identity"><div class="glyph">◈</div><div><strong>COGNIGENESIS</strong><small>HARNESS / PRIVATE</small></div></div><div><div class="navlabel">Workspace</div><nav class="nav" aria-label="Dashboard sections"><button class="active" data-view="overview"><span>◉</span>Overview</button><button data-view="tasks"><span>▤</span>Tasks</button><button data-view="agents"><span>◇</span>Agents</button><button data-view="cognition"><span>✧</span>Cognition</button><button data-view="activity"><span>≋</span>Activity</button><button data-view="models"><span>⬡</span>Models</button></nav></div><div class="foot"><strong>● Local control</strong>Read-only view of the selected workspace. Runtime updates appear automatically.</div></aside><main><header class="top"><div><div class="eyebrow">OPERATIONS / COMMAND CENTER</div><h1>Harness dashboard</h1></div><div class="actions"><button id="download" class="action">Export snapshot</button><button id="refresh" class="action primary">↻ Refresh</button></div></header><div class="notice">PRIVATE WORKSPACE · This dashboard shows recorded harness state. It does not start agents or change credentials. Run <code>cogni harness</code> or <code>cogni team</code> in this workspace to generate activity.</div>
<section class="view active" id="overview"><div class="hero"><div><h2>Overview</h2><p>Live signals from your harness workspace.</p></div><div class="signal"><span class="dot off" id="liveDot"></span><span id="updated">Waiting for runtime</span></div></div><div class="grid"><article class="card third"><h3>Mission tasks</h3><div class="metric"><div><div class="big" id="taskCount">0</div><div class="small">tracked tasks</div></div><div class="big" id="taskDone">0</div></div><div class="meter"><span id="taskBar" style="width:0%"></span></div></article><article class="card third"><h3>Team agents</h3><div class="big" id="agentCount">0</div><div class="small">recorded across teams</div></article><article class="card third"><h3>Cognitive ledger</h3><div class="big" id="hypCount">0</div><div class="small">active hypotheses</div><div class="pills"><span class="pill" id="contraCount">0 contradictions</span><span class="pill" id="questionCount">0 open questions</span></div></article><article class="card"><div class="cardheader"><h3>Selected model</h3><span class="pill good" id="providerBadge">Loading</span></div><div class="model" id="modelName">Not selected</div><div class="small" id="connection">Configure with cogni setup</div></article><article class="card"><div class="cardheader"><h3>Recent activity</h3><button class="action" data-go="activity">View all →</button></div><div id="recentEvents" class="empty">No events recorded.</div></article><article class="card full"><div class="cardheader"><h3>Mission board</h3><button class="action" data-go="tasks">All tasks →</button></div><div id="overviewTasks" class="empty">No tasks recorded.</div></article></div></section>
<section class="view" id="tasks"><div class="hero"><div><h2>Tasks</h2><p>Recorded work and dependencies.</p></div></div><div class="toolbar"><input id="taskSearch" type="search" placeholder="Search tasks" aria-label="Search tasks"><select id="taskFilter" aria-label="Filter task status"><option value="">All statuses</option><option>pending</option><option>ready</option><option>running</option><option>blocked</option><option>completed</option><option>failed</option><option>cancelled</option></select></div><article class="card full" id="allTasks"></article></section>
<section class="view" id="agents"><div class="hero"><div><h2>Agents & teams</h2><p>Team membership, roles, and pending messages.</p></div></div><article class="card full" id="allTeams"></article></section>
<section class="view" id="cognition"><div class="hero"><div><h2>Cognitive ledger</h2><p>Observable hypotheses, evidence, and open questions.</p></div></div><div class="grid"><article class="card"><h3>Hypotheses</h3><div id="allHypotheses"></div></article><article class="card"><h3>Evidence</h3><div id="allEvidence"></div></article><article class="card full"><h3>Open questions</h3><div id="allQuestions"></div></article></div></section>
<section class="view" id="activity"><div class="hero"><div><h2>Runtime activity</h2><p>Latest recorded events, newest first.</p></div></div><div class="toolbar"><input id="eventSearch" type="search" placeholder="Search event types or sources" aria-label="Search activity"></div><article class="card full"><div class="timeline" id="allEvents"></div></article></section>
<section class="view" id="models"><div class="hero"><div><h2>Model connection</h2><p>Current provider configuration, without credentials.</p></div></div><div class="grid"><article class="card"><h3>Provider</h3><div class="model" id="providerName">Loading</div><div class="small" id="connectionDetail"></div></article><article class="card"><h3>Default model</h3><div class="model" id="modelDetail">Not selected</div><div class="small">Change it in the terminal with <code>cogni setup</code> or <code>/switch</code>.</div></article><article class="card full"><h3>Connect another model</h3><div class="small">The setup wizard supports OpenAI, Anthropic, Google, xAI, hosted Meta models, Ollama on this device or your network, and compatible local servers. API keys stay in your OS credential manager or environment; this page never displays them.</div></article></div></section>
</main></div><script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const node=id=>document.getElementById(id);let state={tasks:[],teams:[],events:[],cognition:{}},config={};
const safeStatus=s=>/^(completed|supports|failed|contradicts|running)$/.test(s)?s:'';
const badge=s=>'<span class="badge '+safeStatus(s)+'">'+esc(s||'unknown')+'</span>';
const empty=s=>'<div class="empty">'+esc(s)+'</div>';
const render=(id,arr,fn,msg)=>node(id).innerHTML=arr.length?arr.map(fn).join(''):empty(msg);
const task=t=>'<div class="row"><div class="rowtop"><div class="rowtitle">'+esc(t.title)+'</div>'+badge(t.status)+'</div><div class="rowmeta">'+esc(t.description||'')+(t.assigned_agent?' · agent '+esc(t.assigned_agent):'')+(t.dependencies?.length?' · '+t.dependencies.length+' dependencies':'')+'</div></div>';
const event=e=>'<div class="row"><div class="rowtop"><span class="rowtitle">'+esc(e.type)+'</span><span class="small">'+esc(e.time?new Date(e.time).toLocaleString():'')+'</span></div><div class="rowmeta">'+esc(e.source||'runtime')+' · '+esc(JSON.stringify(e.payload||{}))+'</div></div>';
function draw(){const tasks=state.tasks||[],teams=state.teams||[],events=state.events||[],c=state.cognition||{},m=c.metrics||{},agents=teams.flatMap(t=>t.agents||[]),done=tasks.filter(t=>t.status==='completed').length;
node('taskCount').textContent=tasks.length;node('taskDone').textContent=done+' done';node('taskBar').style.width=(tasks.length?100*done/tasks.length:0)+'%';node('agentCount').textContent=agents.length;node('hypCount').textContent=m.active_hypotheses||0;node('contraCount').textContent=(m.contradictions||0)+' contradictions';node('questionCount').textContent=(m.unresolved_questions||0)+' open questions';
node('modelName').textContent=config.model||'Not selected';node('modelDetail').textContent=config.model||'Not selected';node('providerBadge').textContent=config.provider||'Not configured';node('providerName').textContent=config.provider||'Not configured';node('connection').textContent=config.provider==='ollama'?('Ollama · '+(config.connection||'local')+' server'):'Provider configuration';node('connectionDetail').textContent=config.provider==='ollama'?('Ollama '+(config.connection||'local')+' server · no API key required'):'Use cogni setup to change the connection';
render('recentEvents',events.slice(-3).reverse(),event,'No events recorded.');render('overviewTasks',tasks.slice(0,5),task,'No tasks recorded.');render('allTasks',tasks.filter(t=>(!node('taskFilter').value||t.status===node('taskFilter').value)&&JSON.stringify(t).toLowerCase().includes(node('taskSearch').value.toLowerCase())),task,'No matching tasks.');
render('allTeams',teams,t=>'<div class="row"><div class="rowtitle">'+esc(t.name)+'</div><div class="rowmeta">'+esc(t.objective||'')+'</div><div class="subgrid">'+(t.agents||[]).map(a=>'<div class="agent"><strong>'+esc(a.name)+'</strong><div>'+esc(a.role)+'</div><div class="small">'+esc(a.model||'Default model')+' · '+esc(a.pending_messages||0)+' pending</div></div>').join('')+'</div></div>','No teams recorded.');
render('allHypotheses',c.hypotheses||[],h=>'<div class="row">'+badge(h.status)+' <span class="rowtitle">'+esc(h.claim)+'</span><div class="rowmeta">Confidence: '+esc(h.confidence??'unrecorded')+'</div></div>','No hypotheses recorded.');render('allEvidence',c.evidence||[],e=>'<div class="row">'+badge(e.polarity)+' <span class="rowtitle">'+esc(e.claim)+'</span><div class="rowmeta">'+esc(e.source||'No source recorded')+'</div></div>','No evidence recorded.');render('allQuestions',c.open_questions||[],q=>'<div class="row">'+esc(typeof q==='string'?q:JSON.stringify(q))+'</div>','No open questions recorded.');
render('allEvents',events.slice().reverse().filter(e=>JSON.stringify(e).toLowerCase().includes(node('eventSearch').value.toLowerCase())),event,'No matching events.');
const stamp=state.updated_at;node('updated').textContent=stamp?'Updated '+new Date(stamp).toLocaleTimeString():'No snapshot yet';node('liveDot').classList.toggle('off',!stamp);
}
async function refresh(){try{const [sr,cr]=await Promise.all([fetch('/api/state',{cache:'no-store'}),fetch('/api/config',{cache:'no-store'})]);if(!sr.ok||!cr.ok)throw Error('server unavailable');state=await sr.json();config=await cr.json();draw()}catch(e){node('updated').textContent='Connection unavailable';node('liveDot').classList.add('off')}}
function navigate(id){if(!node(id)?.classList.contains('view'))return;document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===id));history.replaceState(null,'','#'+id)}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.view)));document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.go)));['taskSearch','taskFilter','eventSearch'].forEach(id=>node(id).addEventListener('input',draw));node('refresh').addEventListener('click',refresh);node('download').addEventListener('click',()=>{const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}));a.href=url;a.download='cognigenesis-workspace-snapshot.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});navigate(location.hash.slice(1)||'overview');refresh();setInterval(refresh,3000);
</script></body></html>
"""


def serve_command_center(workspace: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    if not _loopback(host):
        raise ValueError("The dashboard is read-only but has no login; bind to localhost and use a trusted tunnel for remote access.")
    state_path = workspace / ".cognigenesis" / "command-center.json"
    store = CommandCenterStore(state_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            host_header = self.headers.get("Host", "")
            authority = host_header[1:].split("]", 1)[0] if host_header.startswith("[") else host_header.split(":", 1)[0]
            if not _loopback(authority):
                self.send_error(403)
                return
            path = urlparse(self.path).path
            if path in {"/api/state", "/api/config"}:
                body = json.dumps(store.load() if path == "/api/state" else dashboard_config(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path in {"/", "/index.html"}:
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'")
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
