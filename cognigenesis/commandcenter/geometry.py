"""Read-only mathematical graph projection of recorded harness state.

No fabricated nodes, agent telemetry, or inferred model cognition.
"""
from __future__ import annotations

from typing import Any


MAX_NODES = 2000
MAX_LINKS = 4000


def topology(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Bounded display projection; labels are text, identities are never truncated."""
    if not isinstance(snapshot, dict):
        snapshot = {}
    nodes: dict[str, dict[str, str]] = {}
    links: dict[tuple[str, str, str], dict[str, str]] = {}
    truncated = False

    def items(value: Any, limit: int) -> list:
        nonlocal truncated
        if not isinstance(value, list):
            return []
        truncated |= len(value) > limit
        return value[:limit]

    def node(kind: str, value: Any, label: Any = None) -> str | None:
        nonlocal truncated
        if not isinstance(value, str) or not value:
            return None
        ident = f"{kind}:{value}"
        if ident not in nodes and len(nodes) >= MAX_NODES:
            truncated = True
            return None
        # A reference must not replace the entity's recorded display name.
        if ident not in nodes or label is not None:
            nodes[ident] = {"id": ident, "type": kind,
                            "label": str(label if label is not None else value)[:100]}
        return ident

    def edge(source: str | None, target: str | None, relation: str) -> None:
        nonlocal truncated
        if source and target and source != target:
            key = (source, target, relation)
            if key not in links and len(links) >= MAX_LINKS:
                truncated = True
                return
            links[key] = {"source": source, "target": target, "relation": relation}

    for task in items(snapshot.get("tasks"), 500):
        if not isinstance(task, dict):
            continue
        task_id = node("task", task.get("id"), task.get("title"))
        if not task_id:
            continue
        for dependency in items(task.get("dependencies"), 50):
            edge(task_id, node("task", dependency), "depends_on")
        edge(node("agent", task.get("assigned_agent")), task_id, "assigned")
    for team in items(snapshot.get("teams"), 100):
        if not isinstance(team, dict):
            continue
        team_id = node("team", team.get("id"), team.get("name"))
        if not team_id:
            continue
        for agent in items(team.get("agents"), 100):
            if isinstance(agent, dict):
                edge(team_id, node("agent", agent.get("id"), agent.get("name")), "contains")
    cognition = snapshot.get("cognition")
    if isinstance(cognition, dict):
        hypotheses = items(cognition.get("hypotheses"), 200)
        evidence_items = items(cognition.get("evidence"), 200)
        for hypothesis in hypotheses:
            if isinstance(hypothesis, dict):
                node("hypothesis", hypothesis.get("id"), hypothesis.get("claim"))
        evidence_by_id = {}
        for evidence in evidence_items:
            if isinstance(evidence, dict):
                ident = node("evidence", evidence.get("id"), evidence.get("claim"))
                if ident:
                    evidence_by_id[evidence["id"]] = evidence
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue
            target = f"hypothesis:{hypothesis.get('id')}"
            if target not in nodes:
                continue
            for evidence_id in items(hypothesis.get("evidence_ids"), 200):
                if not isinstance(evidence_id, str) or evidence_id not in evidence_by_id:
                    continue
                evidence = evidence_by_id[evidence_id]
                polarity = evidence.get("polarity", "neutral")
                relation = polarity if polarity in {"supports", "contradicts"} else "neutral"
                edge(f"evidence:{evidence_id}", target, relation)
    events = snapshot.get("events")
    events = events if isinstance(events, list) else []
    for event in events[-300:]:
        if isinstance(event, dict) and event.get("source") != "runtime":
            node("source", event.get("source"))
    return {"nodes": list(nodes.values()), "links": list(links.values()),
            "updated_at": snapshot.get("updated_at"), "event_count": len(events),
            "truncated": truncated}


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
let nodes=[],edges=[],width=600,height=500,frame=0,fetching=false,remaining=0,animation=null,signature='';
el('legend').textContent='';
for(const [kind,color] of Object.entries(kinds)){const row=document.createElement('div'),dot=document.createElement('i');dot.style.background=color;row.append(dot,document.createTextNode(kind));el('legend').append(row)}
function wake(){remaining=300;if(animation===null&&!document.hidden)animation=requestAnimationFrame(step)}
function resize(){const r=el('viewport').getBoundingClientRect();width=r.width;height=r.height;const d=Math.min(devicePixelRatio||1,2);canvas.width=Math.max(1,Math.floor(width*d));canvas.height=Math.max(1,Math.floor(height*d));ctx.setTransform(d,0,0,d,0,0);wake()}
new ResizeObserver(resize).observe(el('viewport'));resize();
const hash=s=>{let n=2166136261;for(let i=0;i<s.length;i++){n^=s.charCodeAt(i);n=Math.imul(n,16777619)}return n>>>0};
function integrate(data){const next=JSON.stringify([data.nodes,data.links]);if(next===signature){el('eventCount').textContent=data.event_count||0;el('stamp').textContent=data.updated_at?new Date(data.updated_at).toLocaleTimeString():'No state';return}signature=next;wake();const previous=new Map(nodes.map(n=>[n.id,n]));nodes=(data.nodes||[]).map(n=>{const old=previous.get(n.id),seed=hash(n.id),a=(seed%6283)/1000;return {...n,x:old?.x??width/2+100*Math.cos(a),y:old?.y??height/2+100*Math.sin(a),vx:old?.vx??0,vy:old?.vy??0}});
const lookup=new Map(nodes.map(n=>[n.id,n]));edges=(data.links||[]).filter(e=>lookup.has(e.source)&&lookup.has(e.target)).map(e=>({...e,a:lookup.get(e.source),b:lookup.get(e.target)}));
el('nodeCount').textContent=nodes.length;el('linkCount').textContent=edges.length;el('eventCount').textContent=data.event_count||0;el('stamp').textContent=data.updated_at?new Date(data.updated_at).toLocaleTimeString():'No state';}
async function refresh(){if(fetching||document.hidden)return;fetching=true;try{const res=await fetch('/api/topology',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);const data=await res.json();integrate(data);el('status').textContent=data.truncated?'Snapshot connected · display limit reached':'Snapshot connected'}catch(err){el('status').textContent='Unavailable: '+err.message}finally{fetching=false}}
function step(){animation=null;if(document.hidden)return;frame++;remaining--;ctx.clearRect(0,0,width,height);ctx.fillStyle='#080e19';ctx.fillRect(0,0,width,height);
for(let i=0;i<nodes.length;i++){const a=nodes[i];const stride=Math.max(1,Math.ceil((nodes.length-i-1)/32));for(let j=i+1+(frame%stride);j<nodes.length;j+=stride){const b=nodes[j],dx=a.x-b.x,dy=a.y-b.y,dist2=Math.max(100,dx*dx+dy*dy),force=Math.min(1.5,1100/dist2),dist=Math.sqrt(dist2);a.vx+=dx/dist*force;b.vx-=dx/dist*force;a.vy+=dy/dist*force;b.vy-=dy/dist*force}}
for(const e of edges){const dx=e.b.x-e.a.x,dy=e.b.y-e.a.y,dist=Math.max(1,Math.hypot(dx,dy)),force=(dist-115)*0.0018;e.a.vx+=dx/dist*force;e.a.vy+=dy/dist*force;e.b.vx-=dx/dist*force;e.b.vy-=dy/dist*force;ctx.strokeStyle='#4d789590';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(e.a.x,e.a.y);ctx.lineTo(e.b.x,e.b.y);ctx.stroke()}
for(const n of nodes){n.vx+=(width/2-n.x)*0.00025;n.vy+=(height/2-n.y)*0.00025;n.vx*=0.86;n.vy*=0.86;n.x=Math.max(20,Math.min(width-20,n.x+n.vx));n.y=Math.max(20,Math.min(height-20,n.y+n.vy));
ctx.beginPath();ctx.arc(n.x,n.y,5,0,Math.PI*2);ctx.fillStyle=kinds[n.type]||'#ccc';ctx.fill();
if(nodes.length<100){ctx.font='11px system-ui';ctx.fillStyle='#d4e4fa';ctx.fillText(n.label.slice(0,29),n.x+9,n.y-7)}}
if(!nodes.length){ctx.fillStyle='#91a7c3';ctx.font='15px system-ui';ctx.textAlign='center';ctx.fillText('No recorded entities yet — run the harness to populate this graph.',width/2,height/2);ctx.textAlign='left'}
if(remaining>0)animation=requestAnimationFrame(step)}
document.addEventListener('visibilitychange',()=>{if(!document.hidden){refresh();wake()}});
refresh();setInterval(refresh,3000);
</script></body></html>"""
