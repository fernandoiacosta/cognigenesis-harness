"""Read-only mathematical graph projection of recorded harness state.

No fabricated nodes, agent telemetry, or inferred model cognition.
"""
from __future__ import annotations

from typing import Any


def topology(snapshot: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, dict[str, str]] = {}
    links: dict[tuple[str, str, str], dict[str, str]] = {}

    def node(kind: str, value: Any, label: Any = None) -> str:
        ident = f"{kind}:{str(value)[:160]}"
        nodes[ident] = {"id": ident, "type": kind, "label": str(label if label is not None else value)[:100]}
        return ident

    def edge(source: str, target: str, relation: str) -> None:
        if source != target:
            links[(source, target, relation)] = {"source": source, "target": target, "relation": relation}

    for task in (snapshot.get("tasks") or [])[:500]:
        if not isinstance(task, dict):
            continue
        ident = task.get("id")
        if not ident:
            continue
        task_id = node("task", ident, task.get("title") or ident)
        for dependency in (task.get("dependencies") or [])[:50]:
            edge(task_id, node("task", dependency), "depends_on")
        if task.get("assigned_agent"):
            edge(node("agent", task["assigned_agent"]), task_id, "assigned")
    for team in (snapshot.get("teams") or [])[:100]:
        if not isinstance(team, dict):
            continue
        team_id = node("team", team.get("id") or team.get("name") or "unnamed",
                       team.get("name") or "Team")
        for agent in (team.get("agents") or [])[:100]:
            if not isinstance(agent, dict):
                continue
            agent_id = node("agent", agent.get("id") or agent.get("name") or "unnamed",
                            agent.get("name") or "Agent")
            edge(team_id, agent_id, "contains")
    cognition = snapshot.get("cognition") or {}
    if isinstance(cognition, dict):
        for hypothesis in (cognition.get("hypotheses") or [])[:200]:
            if isinstance(hypothesis, dict) and hypothesis.get("claim"):
                node("hypothesis", hypothesis.get("id") or hypothesis["claim"], hypothesis["claim"])
        for evidence in (cognition.get("evidence") or [])[:200]:
            if not isinstance(evidence, dict) or not evidence.get("claim"):
                continue
            evidence_id = node("evidence", evidence.get("id") or evidence["claim"], evidence["claim"])
            for key in ("hypothesis_id", "claim_id"):
                if evidence.get(key):
                    target = f"hypothesis:{str(evidence[key])[:160]}"
                    if target in nodes:
                        edge(evidence_id, target, "supports")
    for event in (snapshot.get("events") or [])[-300:]:
        if not isinstance(event, dict):
            continue
        source = event.get("source")
        if source and source != "runtime":
            node("source", source)
    return {"nodes": list(nodes.values()), "links": list(links.values()),
            "updated_at": snapshot.get("updated_at"),
            "event_count": len(snapshot.get("events") or [])}


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cognigenesis · Live Geometry</title>
<style>
:root{color-scheme:dark;font:14px system-ui,sans-serif;background:#080e19;color:#e7f2ff}
*{box-sizing:border-box}body{margin:0}.bar{display:flex;gap:16px;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid #23354a;flex-wrap:wrap}
a{color:#78dff5}h1{margin:0;font-size:22px}.sub{color:#91a7c3;font-size:12px}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;min-height:calc(100vh - 85px)}
.canvas{position:relative;min-height:500px}canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:pan-y}
aside{background:#101a2a;border-left:1px solid #23354a;padding:18px}.metric{padding:14px 0;border-bottom:1px solid #23354a}
.metric b{font-size:25px;display:block}.metric span{color:#a1b3c9}.legend{margin-top:22px;line-height:2}
.legend i{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:9px}.note{color:#a4b2c5;font-size:12px;line-height:1.6;margin-top:25px}
.status{padding:6px 10px;background:#153044;border-radius:8px;color:#78dff5}
@media(max-width:850px){.layout{grid-template-columns:1fr}.canvas{min-height:60vh}aside{border-left:0;border-top:1px solid #23354a;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.legend,.note{grid-column:span 2}}
</style></head><body>
<header class="bar"><div><a href="/">← Command Center</a><h1>Live cognitive topology</h1><div class="sub">Recorded relationships · weighted force-directed projection · no fabricated activity</div></div><div class="status" id="status">Connecting</div></header>
<div class="layout"><div class="canvas" id="viewport"><canvas id="scene" aria-label="Runtime graph of recorded harness entities"></canvas></div>
<aside><div class="metric"><b id="nodeCount">0</b><span>Observed nodes</span></div><div class="metric"><b id="linkCount">0</b><span>Recorded relationships</span></div><div class="metric"><b id="eventCount">0</b><span>Snapshot events</span></div><div class="metric"><b id="stamp">—</b><span>Last saved state</span></div>
<div class="legend" id="legend"></div><p class="note">Positions are calculated by force-directed graph layout (repulsion, spring constraints, damping), not claimed to be a measured physical attractor. Source: /api/topology. Refresh every 3 seconds. Rendering runs in the browser.</p></aside></div>
<script>
'use strict';
const kinds={task:'#65d5ff',agent:'#9b8cff',team:'#54e6ad',hypothesis:'#f5a5e5',evidence:'#e8bc79',source:'#91a6bf'};
const el=id=>document.getElementById(id),canvas=el('scene'),ctx=canvas.getContext('2d');
let nodes=[],edges=[],width=600,height=500,pointer=null,frame=0,lastUpdate=0,fetching=false;
el('legend').textContent='';
for(const [kind,color] of Object.entries(kinds)){const row=document.createElement('div'),dot=document.createElement('i');dot.style.background=color;row.append(dot,document.createTextNode(kind));el('legend').append(row)}
function resize(){const r=el('viewport').getBoundingClientRect();width=r.width;height=r.height;const d=Math.min(devicePixelRatio||1,2);canvas.width=Math.max(1,Math.floor(width*d));canvas.height=Math.max(1,Math.floor(height*d));ctx.setTransform(d,0,0,d,0,0)}
new ResizeObserver(resize).observe(el('viewport'));resize();
const hash=s=>{let n=2166136261;for(let i=0;i<s.length;i++){n^=s.charCodeAt(i);n=Math.imul(n,16777619)}return n>>>0};
function integrate(data){const previous=new Map(nodes.map(n=>[n.id,n]));nodes=(data.nodes||[]).map(n=>{const old=previous.get(n.id),seed=hash(n.id),a=(seed%6283)/1000;return {...n,x:old?.x??width/2+100*Math.cos(a),y:old?.y??height/2+100*Math.sin(a),vx:old?.vx??0,vy:old?.vy??0}});
const lookup=new Map(nodes.map(n=>[n.id,n]));edges=(data.links||[]).filter(e=>lookup.has(e.source)&&lookup.has(e.target)).map(e=>({...e,a:lookup.get(e.source),b:lookup.get(e.target)}));
el('nodeCount').textContent=nodes.length;el('linkCount').textContent=edges.length;el('eventCount').textContent=data.event_count||0;el('stamp').textContent=data.updated_at?new Date(data.updated_at).toLocaleTimeString():'No state';lastUpdate=Date.now();}
async function refresh(){if(fetching)return;fetching=true;try{const res=await fetch('/api/topology',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);integrate(await res.json());el('status').textContent='Snapshot connected'}catch(err){el('status').textContent='Unavailable: '+err.message}finally{fetching=false}}
function step(){frame++;ctx.clearRect(0,0,width,height);ctx.fillStyle='#080e19';ctx.fillRect(0,0,width,height);
for(let i=0;i<nodes.length;i++){const a=nodes[i];for(let j=i+1;j<nodes.length;j++){const b=nodes[j],dx=a.x-b.x,dy=a.y-b.y,dist2=Math.max(100,dx*dx+dy*dy),force=Math.min(1.5,1100/dist2),dist=Math.sqrt(dist2);a.vx+=dx/dist*force;b.vx-=dx/dist*force;a.vy+=dy/dist*force;b.vy-=dy/dist*force}}
for(const e of edges){const dx=e.b.x-e.a.x,dy=e.b.y-e.a.y,dist=Math.max(1,Math.hypot(dx,dy)),force=(dist-115)*0.0018;e.a.vx+=dx/dist*force;e.a.vy+=dy/dist*force;e.b.vx-=dx/dist*force;e.b.vy-=dy/dist*force;ctx.strokeStyle='#4d789590';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(e.a.x,e.a.y);ctx.lineTo(e.b.x,e.b.y);ctx.stroke()}
for(const n of nodes){n.vx+=(width/2-n.x)*0.00025;n.vy+=(height/2-n.y)*0.00025;n.vx*=0.86;n.vy*=0.86;n.x=Math.max(20,Math.min(width-20,n.x+n.vx));n.y=Math.max(20,Math.min(height-20,n.y+n.vy));
ctx.beginPath();ctx.arc(n.x,n.y,5,0,Math.PI*2);ctx.fillStyle=kinds[n.type]||'#ccc';ctx.fill();
if(nodes.length<100){ctx.font='11px system-ui';ctx.fillStyle='#d4e4fa';ctx.fillText(n.label.slice(0,29),n.x+9,n.y-7)}}
if(!nodes.length){ctx.fillStyle='#91a7c3';ctx.font='15px system-ui';ctx.textAlign='center';ctx.fillText('No recorded entities yet — run the harness to populate this graph.',width/2,height/2);ctx.textAlign='left'}
requestAnimationFrame(step)}
refresh();setInterval(refresh,3000);requestAnimationFrame(step);
</script></body></html>"""
