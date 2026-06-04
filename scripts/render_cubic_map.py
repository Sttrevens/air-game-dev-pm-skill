#!/usr/bin/env python3
"""Render an Air PM cubic progress map as a self-contained HTML file.

The output HTML embeds Three.js, OrbitControls, data, CSS, and app code, so it
can be opened directly from disk with file:// or by double-clicking.

Input can be:
  1. CSV feature rows using the same columns as render_heatmap.py.
  2. JSON {"mainstays": [...]} with nested features/tasks.
  3. JSON {"features": [...]} or a list of feature rows.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


LEVEL_SCORE = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
ALIASES = {
    "mainstay_id": ["mainstay_id", "mainstay id", "mainstay", "m", "支柱id", "支柱 ID"],
    "mainstay_name": ["mainstay_name", "mainstay name", "支柱名称", "mainstay_name"],
    "feature_id": ["feature_id", "feature id", "feature", "特性id", "特性 ID"],
    "feature_name": ["feature_name", "feature name", "特性名称", "任务名称"],
    "type": ["type", "类型", "特性类型", "f/c"],
    "current_level": ["current_level", "current l", "当前质量层次", "当前层级"],
    "target_level": ["target_level", "target l", "目标质量层次", "目标层级"],
    "owner": ["owner", "负责人", "特性负责人"],
    "iter": ["iter", "iteration", "所属迭代", "迭代"],
    "status": ["status", "迭代状态", "状态"],
    "evidence": ["evidence", "概念案链接", "证据", "链接"],
    "depends_on": ["depends_on", "depends on", "依赖", "依赖的能力"],
}


def norm_key(key: str) -> str:
    return " ".join(str(key).strip().lower().replace("_", " ").split())


def canonical_level(value: Any) -> str:
    text = str(value or "").strip().upper().replace("LEVEL", "L")
    if text in LEVEL_SCORE:
        return text
    if text in {"0", "1", "2", "3", "4"}:
        return f"L{text}"
    return "L0"


def normalize_row(row: Dict[str, Any]) -> Dict[str, str]:
    source = {norm_key(k): v for k, v in row.items()}
    out: Dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        out[canonical] = ""
        for alias in aliases:
            if norm_key(alias) in source:
                out[canonical] = "" if source[norm_key(alias)] is None else str(source[norm_key(alias)]).strip()
                break
    out["current_level"] = canonical_level(out.get("current_level"))
    out["target_level"] = canonical_level(out.get("target_level") or "L4")
    out["mainstay_id"] = out["mainstay_id"] or "M-?"
    out["mainstay_name"] = out["mainstay_name"] or out["mainstay_id"]
    out["feature_id"] = out["feature_id"] or "F-?"
    out["feature_name"] = out["feature_name"] or out["feature_id"]
    out["type"] = out["type"] or ("C" if out["feature_id"].startswith("C-") else "F")
    out["status"] = out["status"] or "todo"
    return out


def read_input(path: Path) -> Dict[str, Any]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("mainstays"), list):
            return normalize_mainstay_data(data)
        rows = data.get("features", data) if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError("JSON input must contain 'mainstays', 'features', or be a list.")
        return rows_to_mainstays([normalize_row(r) for r in rows if isinstance(r, dict)])

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return rows_to_mainstays([normalize_row(r) for r in csv.DictReader(f)])


def feature_maturity(row: Dict[str, str]) -> float:
    status = row.get("status", "").strip().lower()
    base = LEVEL_SCORE.get(row.get("current_level", "L0"), 0) / 4
    if status in {"done", "已完成"}:
        return 1.0
    if status in {"blocked", "阻塞"}:
        return max(0.05, base * 0.72)
    if status in {"in progress", "进行中"}:
        return min(0.95, max(base, base + 0.12))
    return base


def rows_to_mainstays(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    names: Dict[str, str] = {}
    for row in rows:
        grouped[row["mainstay_id"]].append(row)
        names[row["mainstay_id"]] = row["mainstay_name"]

    mainstays = []
    for mid in sorted(grouped):
        features = []
        for row in sorted(grouped[mid], key=lambda r: r["feature_id"]):
            maturity = feature_maturity(row)
            features.append(
                {
                    "id": row["feature_id"],
                    "name": row["feature_name"],
                    "type": row["type"],
                    "level": LEVEL_SCORE.get(row["current_level"], 0),
                    "targetLevel": LEVEL_SCORE.get(row["target_level"], 4),
                    "maturity": round(maturity, 3),
                    "status": row["status"],
                    "owner": row["owner"],
                    "iter": row["iter"],
                    "dependsOn": row["depends_on"],
                    "evidence": row["evidence"],
                    "taskCount": 0,
                    "doneTasks": 0,
                    "tasks": [],
                    "url": row["evidence"] if row["evidence"].startswith(("http://", "https://")) else "",
                }
            )
        avg = sum(f["maturity"] for f in features) / len(features) if features else 0
        mainstays.append({"id": mid, "name": names[mid], "maturity": round(avg, 3), "features": features, "url": ""})
    return {"generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"), "mainstays": mainstays}


def normalize_mainstay_data(data: Dict[str, Any]) -> Dict[str, Any]:
    mainstays = []
    for m in data.get("mainstays", []):
        if not isinstance(m, dict):
            continue
        features = []
        for f in m.get("features", []) or []:
            if not isinstance(f, dict):
                continue
            tasks = f.get("tasks") or []
            done_tasks = sum(1 for t in tasks if isinstance(t, dict) and t.get("done"))
            task_count = f.get("taskCount", len(tasks))
            maturity = float(f.get("maturity", 0) or 0)
            features.append(
                {
                    "id": str(f.get("id", "F-?")),
                    "name": str(f.get("name", f.get("id", "Feature"))),
                    "type": str(f.get("type", "F")),
                    "level": float(f.get("level", maturity * 4) or 0),
                    "targetLevel": float(f.get("targetLevel", 4) or 4),
                    "maturity": round(max(0, min(1, maturity)), 3),
                    "status": str(f.get("status", "todo")),
                    "owner": str(f.get("owner", "")),
                    "iter": str(f.get("iter", "")),
                    "dependsOn": str(f.get("dependsOn", "")),
                    "evidence": str(f.get("evidence", "")),
                    "taskCount": int(task_count or 0),
                    "doneTasks": int(f.get("doneTasks", done_tasks) or 0),
                    "tasks": tasks,
                    "url": str(f.get("url", "")),
                }
            )
        avg = sum(f["maturity"] for f in features) / len(features) if features else float(m.get("maturity", 0) or 0)
        mainstays.append(
            {
                "id": str(m.get("id", "M-?")),
                "name": str(m.get("name", m.get("id", "Mainstay"))),
                "maturity": round(max(0, min(1, float(m.get("maturity", avg) or avg))), 3),
                "features": features,
                "url": str(m.get("url", "")),
            }
        )
    return {"generatedAt": str(data.get("generatedAt", datetime.now().strftime("%Y-%m-%d %H:%M"))), "mainstays": mainstays}


def read_vendor(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing vendor file: {path}")
    return path.read_text(encoding="utf-8")


def esc_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def render_html(data: Dict[str, Any], title: str, skill_dir: Path) -> str:
    three_js = read_vendor(skill_dir / "vendor" / "three.min.js")
    controls_js = read_vendor(skill_dir / "vendor" / "OrbitControls.js")
    license_text = html.escape(read_vendor(skill_dir / "vendor" / "THREE_LICENSE"))
    payload = esc_json(data)
    generated = html.escape(str(data.get("generatedAt", "")))
    title_esc = html.escape(title)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title_esc}</title>
<style>
:root{{color-scheme:dark;--bg:#081018;--panel:rgba(11,18,29,.88);--line:rgba(148,163,184,.22);--line2:rgba(148,163,184,.36);--text:#e7f0fb;--muted:#95a6ba;--accent:#38bdf8}}
*{{box-sizing:border-box}}html,body{{margin:0;height:100%;overflow:hidden;background:var(--bg);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--text);letter-spacing:0}}#app{{position:fixed;inset:0}}canvas{{display:block;width:100%;height:100%}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:8px;backdrop-filter:blur(13px);box-shadow:0 18px 50px rgba(0,0,0,.34)}}.hud{{position:fixed;left:14px;top:14px;width:min(404px,calc(100vw - 28px));padding:12px}}.hud h1{{margin:0 0 6px;font-size:17px;line-height:1.15}}.hud p{{margin:0;color:var(--muted);font-size:12px;line-height:1.42}}.toolbar{{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}}button{{height:28px;border:1px solid var(--line2);border-radius:7px;background:rgba(15,23,42,.72);color:#dce8f7;padding:0 9px;font-size:12px;cursor:pointer;white-space:nowrap}}button:hover,button.active{{border-color:var(--accent);background:rgba(14,165,233,.16);color:white}}.legend{{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-top:9px}}.legend span{{height:20px;border-radius:5px;color:#07111c;font-weight:800;font-size:10px;display:flex;align-items:center;justify-content:center}}
.side{{position:fixed;right:14px;top:14px;bottom:14px;width:min(438px,calc(100vw - 28px));padding:12px;overflow:hidden;display:flex;flex-direction:column}}.side h2{{margin:0;font-size:16px;line-height:1.2}}.sub{{color:var(--muted);font-size:12px;line-height:1.35;margin:5px 0 0}}.tabs{{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin:10px 0}}.tab{{height:27px;padding:0 4px;font-size:11px}}.content{{min-height:0;overflow:auto;padding-right:2px}}.metric{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0}}.metric div{{border:1px solid var(--line);border-radius:7px;background:rgba(15,23,42,.46);padding:7px 6px;min-width:0}}.metric b{{display:block;font-size:17px;color:#fff;line-height:1.1}}.metric span{{display:block;color:var(--muted);font-size:10px;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.bar{{height:7px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden}}.bar i{{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f97316,#facc15,#84cc16,#22c55e)}}
.row{{border:1px solid var(--line);border-radius:7px;background:rgba(15,23,42,.42);padding:8px;margin:6px 0}}.row:hover{{border-color:rgba(56,189,248,.62);background:rgba(14,165,233,.10)}}.row strong{{display:block;font-size:12px;color:#eef6ff;line-height:1.25}}.row .meta{{display:flex;gap:7px;flex-wrap:wrap;margin:6px 0 0;color:var(--muted);font-size:11px}}.pill{{border:1px solid var(--line);border-radius:999px;padding:2px 6px;background:rgba(2,6,23,.36)}}.task{{display:grid;grid-template-columns:18px 1fr auto;gap:6px;align-items:start;font-size:12px;line-height:1.34;border-top:1px solid rgba(148,163,184,.14);padding:6px 0;color:#dbe7f4}}.task:first-child{{border-top:0}}.task .mark{{width:14px;height:14px;border-radius:3px;border:1px solid var(--line2);margin-top:1px}}.task.done .mark{{background:#22c55e;border-color:#22c55e}}.task.todo .mark{{background:rgba(239,68,68,.25);border-color:rgba(239,68,68,.55)}}.task a,.row a{{color:#7dd3fc;text-decoration:none}}.mini{{font-size:11px;color:var(--muted)}}.section-title{{font-size:12px;color:#c7d7ea;margin:10px 0 6px}}.tooltip{{position:fixed;z-index:5;pointer-events:none;padding:7px 9px;background:rgba(2,6,23,.92);border:1px solid var(--line2);border-radius:7px;display:none;max-width:340px;font-size:12px;line-height:1.35}}.footer{{position:fixed;left:14px;bottom:12px;color:#7890a7;font-size:11px;background:rgba(2,6,23,.46);border:1px solid rgba(148,163,184,.16);padding:7px 9px;border-radius:7px}}.search{{width:100%;height:30px;border:1px solid var(--line);border-radius:7px;background:rgba(2,6,23,.42);color:var(--text);padding:0 9px;margin:4px 0 6px}}.focusline{{height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,.7),transparent);margin:8px 0}}
@media(max-width:980px){{.side{{left:14px;right:14px;top:auto;height:43vh;width:auto}}.hud{{right:14px;width:auto}}.footer{{display:none}}.metric{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div id="app"></div>
<section class="hud panel"><h1>{title_esc}</h1><p>Self-contained Air PM cubic map. Drag to rotate; click pillars to inspect Mainstay, Feature, Task, and imbalance details. This file can be opened directly from disk.</p><div class="toolbar"><button id="viewIso" class="active">Iso</button><button id="viewTop">Top</button><button id="viewSide">Side</button><button id="viewGaps">Gap</button><button id="viewDense">Near</button><button id="viewReset">Reset</button></div><div class="legend"><span style="background:#ef4444">L0</span><span style="background:#f97316">L1</span><span style="background:#facc15">L2</span><span style="background:#84cc16">L3</span><span style="background:#22c55e">L4</span></div></section>
<aside class="side panel" id="side"></aside><div class="tooltip" id="tip"></div><div class="footer">Generated {generated} · self-contained HTML · Three.js license included in source comment</div>
<script id="pm-data" type="application/json">{payload}</script>
<script>/* Three.js MIT License\\n{license_text}\\n*/</script>
<script>{three_js}</script>
<script>{controls_js}</script>
<script>
const DATA=JSON.parse(document.getElementById('pm-data').textContent);
const app=document.getElementById('app'),side=document.getElementById('side'),tip=document.getElementById('tip');
const scene=new THREE.Scene();scene.background=new THREE.Color(0x081018);scene.fog=new THREE.Fog(0x081018,34,92);
const camera=new THREE.PerspectiveCamera(43,innerWidth/innerHeight,.1,240);camera.position.set(16,17,17);
const renderer=new THREE.WebGLRenderer({{antialias:true}});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;app.appendChild(renderer.domElement);
const controls=new THREE.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.075;controls.target.set(0,2.7,0);controls.minDistance=7;controls.maxDistance=72;controls.maxPolarAngle=Math.PI*.495;
scene.add(new THREE.HemisphereLight(0xc9eeff,0x142033,1.65));const sun=new THREE.DirectionalLight(0xffffff,2.2);sun.position.set(18,30,15);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);scene.add(sun);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(76,76),new THREE.MeshStandardMaterial({{color:0x0b1420,roughness:.92,metalness:.04}}));floor.rotation.x=-Math.PI/2;floor.position.y=-.055;floor.receiveShadow=true;scene.add(floor);const grid=new THREE.GridHelper(76,76,0x213b50,0x132536);grid.position.y=.002;scene.add(grid);
const objects=[],labels=[],mainstayGroups=[];let selected={{m:null,f:null,tab:'overview'}};
const maxHeight=8.2,tile=4.72,gap=-.02,cols=Math.ceil(Math.sqrt(DATA.mainstays.length)),rows=Math.ceil(DATA.mainstays.length/cols),x0=-((cols-1)*(tile+gap))/2,z0=-((rows-1)*(tile+gap))/2;
function clamp(v,a=0,b=1){{return Math.max(a,Math.min(b,v))}}function colorFor(v){{const stops=[new THREE.Color(0xef4444),new THREE.Color(0xf97316),new THREE.Color(0xfacc15),new THREE.Color(0x84cc16),new THREE.Color(0x22c55e)],t=clamp(v),s=t*(stops.length-1),i=Math.min(stops.length-2,Math.floor(s));return stops[i].clone().lerp(stops[i+1],s-i)}}function mat(c,o=1){{return new THREE.MeshStandardMaterial({{color:c,roughness:.58,metalness:.08,transparent:o<1,opacity:o,depthWrite:o>=1}})}}function block(g,x,y,z,w,h,d,m,meta){{const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);mesh.position.set(x,y+h/2,z);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData=meta;g.add(mesh);objects.push(mesh);return mesh}}
function labelSprite(text,size=58){{const cvs=document.createElement('canvas'),ctx=cvs.getContext('2d');cvs.width=1024;cvs.height=220;ctx.fillStyle='rgba(4,10,18,.68)';ctx.fillRect(0,0,cvs.width,cvs.height);ctx.strokeStyle='rgba(148,163,184,.24)';ctx.strokeRect(0,0,cvs.width,cvs.height);ctx.font=`760 ${{size}}px Inter,Arial`;ctx.fillStyle='#edf6ff';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text.slice(0,32),512,110);const tex=new THREE.CanvasTexture(cvs);const spr=new THREE.Sprite(new THREE.SpriteMaterial({{map:tex,transparent:true}}));spr.scale.set(3.5,.75,1);return spr}}function taskMaturity(f,i){{if(!f.tasks||!f.tasks.length)return f.maturity;const t=f.tasks[i];if(!t)return f.maturity;return t.done?Math.max(.88,f.maturity):Math.min(.42,f.maturity)}}
for(let index=0;index<DATA.mainstays.length;index++){{const m=DATA.mainstays[index],c=index%cols,r=Math.floor(index/cols),cx=x0+c*(tile+gap),cz=z0+r*(tile+gap),group=new THREE.Group();group.position.set(cx,0,cz);scene.add(group);mainstayGroups.push({{group,data:m,cx,cz}});block(group,0,0,0,tile,.13,tile,mat(0x182235,.92),{{kind:'mainstay',data:m}});block(group,0,0,0,tile+.04,maxHeight,tile+.04,mat(colorFor(m.maturity),.045),{{kind:'mainstay-shell',data:m}});const edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(tile+.05,maxHeight,tile+.05)),new THREE.LineBasicMaterial({{color:colorFor(m.maturity),transparent:true,opacity:.24}}));edge.position.y=maxHeight/2;group.add(edge);const lab=labelSprite(`${{m.id}} ${{m.name}}`,52);lab.position.set(0,.22,tile/2+.36);group.add(lab);labels.push(lab);const features=m.features||[],fcols=Math.ceil(Math.sqrt(Math.max(1,features.length))),frows=Math.ceil(Math.max(1,features.length)/fcols),usable=tile,spacingX=usable/fcols,spacingZ=usable/frows,cellX=spacingX*1.005,cellZ=spacingZ*1.005;for(let i=0;i<features.length;i++){{const f=features[i],fx=-usable/2+(i%fcols)*spacingX+spacingX/2,fz=-usable/2+Math.floor(i/fcols)*spacingZ+spacingZ/2,h=Math.max(.26,f.maturity*maxHeight),empty=maxHeight-h,tc=Math.max(f.taskCount||0,(f.tasks||[]).length),segments=Math.max(1,tc||Math.ceil((f.level||1)*1.35));if(empty>.05)block(group,fx,h,fz,cellX,empty,cellZ,mat(0x7f1d1d,.13),{{kind:'feature-empty',data:f,mainstay:m}});for(let s=0;s<segments;s++){{const segH=h/segments,tm=tc?taskMaturity(f,s):(s+1)/segments*f.maturity;block(group,fx,s*segH,fz,cellX,Math.max(.04,segH-.008),cellZ,mat(colorFor(tm),.98),{{kind:'feature',data:f,mainstay:m,segment:s+1,task:(f.tasks||[])[s]}})}}}}}}
function esc(s){{return String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]))}}function pct(v){{return Math.round((v||0)*100)}}function level(f){{return `L${{Math.round(f.level||0)}}`}}function totalTasks(m){{return m.features.reduce((a,f)=>a+(f.taskCount||0),0)}}function doneTasks(m){{return m.features.reduce((a,f)=>a+(f.doneTasks||0),0)}}function byWeak(a,b){{return (a.maturity||0)-(b.maturity||0)}}function summary(m){{const fs=m.features||[],total=fs.length,done=fs.filter(f=>(f.maturity||0)>=.9).length,weak=fs.filter(f=>(f.maturity||0)<.35).length;return{{total,done,weak,tasks:totalTasks(m),doneTasks:doneTasks(m),avg:pct(m.maturity)}}}}
function taskRow(t){{const done=t.done?'done':'todo';return `<div class="task ${{done}}"><span class="mark"></span><div>${{esc(t.id||'T')}} ${{esc(t.name||'Untitled task')}}<div class="mini">${{esc(t.status||'todo')}}</div></div>${{t.url?`<a href="${{esc(t.url)}}" target="_blank">link</a>`:''}}</div>`}}function featureRow(m,f,clickable=true){{return `<div class="row" ${{clickable?`data-mid="${{esc(m.id)}}" data-fid="${{esc(f.id)}}"`:''}}><strong>${{esc(f.id)}} ${{esc(f.name)}}</strong><div class="bar"><i style="width:${{pct(f.maturity)}}%"></i></div><div class="meta"><span class="pill">${{level(f)}}</span><span class="pill">${{pct(f.maturity)}}%</span><span class="pill">${{f.doneTasks||0}}/${{f.taskCount||0}} tasks</span><span class="pill">${{esc(f.status||'')}}</span></div></div>`}}
function mainstayOverview(m){{const s=summary(m),weak=[...m.features].sort(byWeak).slice(0,5);return `<h2>${{esc(m.id)}} ${{esc(m.name)}}</h2><p class="sub">Mainstay is one large pillar; internal blocks are Features, segmented by task or level evidence.</p><div class="metric"><div><b>${{s.avg}}%</b><span>Mainstay</span></div><div><b>${{s.total}}</b><span>Features</span></div><div><b>${{s.doneTasks}}/${{s.tasks}}</b><span>Tasks</span></div><div><b>${{s.weak}}</b><span>Early</span></div></div><div class="section-title">Features to shore up</div>${{weak.map(f=>featureRow(m,f)).join('')}}<div class="section-title">Air PM read</div><div class="row"><strong>${{s.weak>0?'Fill foundations before deep polish':'Ready to plan next validation layer'}}</strong><div class="mini">If one green tower sits inside a red field, pause local polish and bring neighboring pillars to L1/L2 evidence.</div></div>`}}
function featureDetail(m,f){{const tasks=f.tasks||[];return `<h2>${{esc(f.id)}} ${{esc(f.name)}}</h2><p class="sub">Under ${{esc(m.id)}} ${{esc(m.name)}}.</p><div class="metric"><div><b>${{level(f)}}</b><span>Level</span></div><div><b>${{pct(f.maturity)}}%</b><span>Maturity</span></div><div><b>${{f.doneTasks||0}}/${{f.taskCount||0}}</b><span>Tasks</span></div><div><b>${{esc(f.type||'F')}}</b><span>Type</span></div></div><div class="bar"><i style="width:${{pct(f.maturity)}}%"></i></div><div class="focusline"></div><div class="section-title">Task details</div>${{tasks.length?tasks.map(taskRow).join(''):`<div class="row"><strong>No task rows in this data</strong><div class="mini">Add task objects to the JSON input for drilldown details.</div></div>`}}${{f.url?`<div class="row"><strong>Feature link</strong><div class="mini"><a href="${{esc(f.url)}}" target="_blank">Open evidence</a></div></div>`:''}}`}}
function featureList(m){{const rows=[...m.features].sort((a,b)=>a.id.localeCompare(b.id));return `<h2>${{esc(m.id)}} Feature Matrix</h2><input class="search" id="filter" placeholder="Filter features or tasks"/><div id="featureRows">${{rows.map(f=>featureRow(m,f)).join('')}}</div>`}}function gapView(){{const ms=[...DATA.mainstays].sort((a,b)=>(a.maturity||0)-(b.maturity||0));const avg=DATA.mainstays.reduce((a,m)=>a+(m.maturity||0),0)/DATA.mainstays.length;return `<h2>Global Imbalance</h2><p class="sub">Use this view to spot short pillars and premature depth.</p><div class="metric"><div><b>${{pct(avg)}}%</b><span>Average</span></div><div><b>${{pct(ms[0].maturity)}}</b><span>Lowest</span></div><div><b>${{pct(ms.at(-1).maturity)}}</b><span>Highest</span></div><div><b>${{pct(ms.at(-1).maturity-ms[0].maturity)}}</b><span>Gap</span></div></div>${{ms.map(m=>{{const s=summary(m);return `<div class="row" data-mid="${{esc(m.id)}}"><strong>${{esc(m.id)}} ${{esc(m.name)}} <span class="pill">${{pct(m.maturity)}}%</span></strong><div class="bar"><i style="width:${{pct(m.maturity)}}%"></i></div><div class="meta"><span class="pill">${{s.total}} F</span><span class="pill">${{s.doneTasks}}/${{s.tasks}} T</span><span class="pill">${{s.weak}} early</span></div></div>`}}).join('')}}`}}
function render(){{const m=selected.m||DATA.mainstays[0],f=selected.f;let body='';if(selected.tab==='overview')body=mainstayOverview(m);if(selected.tab==='features')body=featureList(m);if(selected.tab==='tasks')body=f?featureDetail(m,f):`<h2>Task Drilldown</h2><p class="sub">Click a Feature pillar or choose a row.</p>${{[...m.features].sort(byWeak).slice(0,8).map(x=>featureRow(m,x)).join('')}}`;if(selected.tab==='gaps')body=gapView();side.innerHTML=`<div class="tabs"><button class="tab ${{selected.tab==='overview'?'active':''}}" data-tab="overview">Overview</button><button class="tab ${{selected.tab==='features'?'active':''}}" data-tab="features">Feature</button><button class="tab ${{selected.tab==='tasks'?'active':''}}" data-tab="tasks">Task</button><button class="tab ${{selected.tab==='gaps'?'active':''}}" data-tab="gaps">Gap</button></div><div class="content">${{body}}</div>`;bindPanel()}}
function bindPanel(){{side.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{{selected.tab=b.dataset.tab;render()}});side.querySelectorAll('[data-fid]').forEach(el=>el.onclick=()=>{{const m=DATA.mainstays.find(x=>x.id===el.dataset.mid),f=m?.features.find(x=>x.id===el.dataset.fid);selected={{m,f,tab:'tasks'}};focusMainstay(m);render()}});side.querySelectorAll('[data-mid]:not([data-fid])').forEach(el=>el.onclick=()=>{{const m=DATA.mainstays.find(x=>x.id===el.dataset.mid);selected={{m,f:null,tab:'overview'}};focusMainstay(m);render()}});const filter=side.querySelector('#filter');if(filter)filter.oninput=()=>{{const q=filter.value.trim().toLowerCase();side.querySelectorAll('#featureRows .row').forEach(row=>{{row.style.display=row.textContent.toLowerCase().includes(q)?'block':'none'}})}}}}function focusMainstay(m){{const g=mainstayGroups.find(x=>x.data===m);if(!g)return;controls.target.set(g.cx,2.7,g.cz);camera.position.set(g.cx+10,13,g.cz+11);controls.update()}}render();
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();function hover(e){{pointer.x=e.clientX/innerWidth*2-1;pointer.y=-(e.clientY/innerHeight)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(objects,false)[0];if(!hit){{tip.style.display='none';return}}const u=hit.object.userData,d=u.data;tip.style.display='block';tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px';if(u.kind.startsWith('feature'))tip.innerHTML=`<b>${{esc(d.id)}} ${{esc(d.name)}}</b><br>${{esc(u.mainstay.id)}} · ${{level(d)}} · ${{pct(d.maturity)}}% · ${{d.doneTasks||0}}/${{d.taskCount||0}} tasks${{u.task?`<br>${{u.task.done?'Done':'Todo'}}: ${{esc(u.task.name)}}`:''}}`;else tip.innerHTML=`<b>${{esc(d.id)}} ${{esc(d.name)}}</b><br>${{pct(d.maturity)}}% · ${{(d.features||[]).length}} features · ${{doneTasks(d)}}/${{totalTasks(d)}} tasks`}}function click(){{raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(objects,false)[0];if(!hit)return;const u=hit.object.userData;if(u.kind.startsWith('feature'))selected={{m:u.mainstay,f:u.data,tab:'tasks'}};else if(u.kind.startsWith('mainstay'))selected={{m:u.data,f:null,tab:'overview'}};render()}}renderer.domElement.addEventListener('pointermove',hover);renderer.domElement.addEventListener('click',click);
function setActive(id){{document.querySelectorAll('.toolbar button').forEach(b=>b.classList.toggle('active',b.id===id))}}function fly(pos,target,id){{camera.position.copy(pos);controls.target.copy(target);controls.update();setActive(id)}}viewIso.onclick=()=>fly(new THREE.Vector3(16,17,17),new THREE.Vector3(0,2.7,0),'viewIso');viewTop.onclick=()=>fly(new THREE.Vector3(0,42,.01),new THREE.Vector3(0,0,0),'viewTop');viewSide.onclick=()=>fly(new THREE.Vector3(0,8.2,31),new THREE.Vector3(0,3.7,0),'viewSide');viewDense.onclick=()=>fly(new THREE.Vector3(9,10,9),new THREE.Vector3(0,3.1,0),'viewDense');viewReset.onclick=()=>fly(new THREE.Vector3(16,17,17),new THREE.Vector3(0,2.7,0),'viewIso');viewGaps.onclick=()=>{{selected.tab='gaps';render();const sorted=[...mainstayGroups].sort((a,b)=>a.data.maturity-b.data.maturity),low=sorted[0],high=sorted.at(-1);fly(new THREE.Vector3((low.cx+high.cx)/2,11,Math.max(low.cz,high.cz)+20),new THREE.Vector3((low.cx+high.cx)/2,3,(low.cz+high.cz)/2),'viewGaps')}};
addEventListener('resize',()=>{{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)}});function animate(){{requestAnimationFrame(animate);for(const l of labels)l.quaternion.copy(camera.quaternion);controls.update();renderer.render(scene,camera)}}animate();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a self-contained Air PM cubic map HTML.")
    parser.add_argument("input", type=Path, help="Input CSV or JSON file.")
    parser.add_argument("-o", "--output", type=Path, default=Path("air_pm_cubic_map.html"))
    parser.add_argument("--title", default="Air Game Dev PM Cubic Map")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    data = read_input(args.input)
    args.output.write_text(render_html(data, args.title, skill_dir), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
