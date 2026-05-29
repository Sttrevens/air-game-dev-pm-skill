#!/usr/bin/env python3
"""Render an Air Game Dev PM feature heatmap as a standalone HTML file.

Input can be CSV or JSON.

CSV expected columns, with aliases accepted:
  mainstay_id, mainstay_name, feature_id, feature_name, type,
  current_level, target_level, owner, iter, status, evidence, depends_on

JSON can be either:
  [{"mainstay_id": "...", "feature_id": "..."}]
or:
  {"features": [...], "title": "..."}
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


LEVELS = ["L0", "L1", "L2", "L3", "L4"]
LEVEL_SCORE = {level: i for i, level in enumerate(LEVELS)}
LEVEL_COLORS = {
    "L0": "#f3f4f6",
    "L1": "#f97316",
    "L2": "#facc15",
    "L3": "#38bdf8",
    "L4": "#2563eb",
}
LEVEL_LABELS = {
    "L0": "Not started",
    "L1": "Concept",
    "L2": "Prototype",
    "L3": "Implementation",
    "L4": "Polish",
}
STATUS_COLORS = {
    "blocked": "#ef4444",
    "阻塞": "#ef4444",
    "in progress": "#8b5cf6",
    "进行中": "#8b5cf6",
    "done": "#10b981",
    "已完成": "#10b981",
    "todo": "#9ca3af",
    "待办": "#9ca3af",
}

ALIASES = {
    "mainstay_id": ["mainstay_id", "mainstay id", "mainstay", "m", "支柱id", "支柱 ID", "mainstay_id"],
    "mainstay_name": ["mainstay_name", "mainstay name", "支柱名称", "名称", "mainstay_name"],
    "feature_id": ["feature_id", "feature id", "feature", "特性id", "特性 ID", "feature_id"],
    "feature_name": ["feature_name", "feature name", "特性名称", "任务名称", "feature_name"],
    "type": ["type", "类型", "特性类型", "f/c"],
    "depends_on": ["depends_on", "depends on", "依赖", "依赖的能力"],
    "current_level": ["current_level", "current l", "当前质量层次", "当前层级", "current_level"],
    "target_level": ["target_level", "target l", "目标质量层次", "目标层级", "target_level"],
    "owner": ["owner", "负责人", "特性负责人"],
    "iter": ["iter", "iteration", "所属迭代", "迭代"],
    "status": ["status", "迭代状态", "状态"],
    "evidence": ["evidence", "概念案链接", "证据", "链接"],
}


def canonical_level(value: Any) -> str:
    text = str(value or "").strip().upper().replace("LEVEL", "L")
    if text in LEVEL_SCORE:
        return text
    if text in {"1", "2", "3", "4"}:
        return f"L{text}"
    return "L0"


def norm_key(key: str) -> str:
    return " ".join(str(key).strip().lower().replace("_", " ").split())


def normalize_row(row: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    source = {norm_key(k): v for k, v in row.items()}
    for canonical, aliases in ALIASES.items():
        value = ""
        for alias in aliases:
            if norm_key(alias) in source:
                value = source[norm_key(alias)]
                break
        normalized[canonical] = "" if value is None else str(value).strip()
    normalized["current_level"] = canonical_level(normalized.get("current_level"))
    normalized["target_level"] = canonical_level(normalized.get("target_level") or "L4")
    if not normalized["mainstay_id"]:
        normalized["mainstay_id"] = "M-?"
    if not normalized["feature_id"]:
        normalized["feature_id"] = "F-?"
    if not normalized["feature_name"]:
        normalized["feature_name"] = normalized["feature_id"]
    if not normalized["mainstay_name"]:
        normalized["mainstay_name"] = normalized["mainstay_id"]
    return normalized


def read_rows(path: Path) -> List[Dict[str, str]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("features", data) if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError("JSON input must be a list or an object with a 'features' list.")
        return [normalize_row(r) for r in rows if isinstance(r, dict)]

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [normalize_row(r) for r in csv.DictReader(f)]


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def progress_stats(rows: Iterable[Dict[str, str]]) -> Dict[str, Any]:
    rows = list(rows)
    if not rows:
        return {"count": 0, "avg": 0, "blocked": 0, "l4": 0}
    scores = [LEVEL_SCORE.get(r["current_level"], 0) for r in rows]
    blocked = sum(1 for r in rows if r.get("status", "").strip().lower() in {"blocked", "阻塞"})
    l4 = sum(1 for r in rows if r["current_level"] == "L4")
    return {
        "count": len(rows),
        "avg": round(sum(scores) / (4 * len(scores)) * 100),
        "blocked": blocked,
        "l4": l4,
    }


def render_html(rows: List[Dict[str, str]], title: str) -> str:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[f"{row['mainstay_id']} {row['mainstay_name']}"].append(row)

    overall = progress_stats(rows)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    group_cards = []
    feature_rows = []

    for group_name, items in sorted(grouped.items()):
        stats = progress_stats(items)
        group_cards.append(
            f"""
            <section class="mainstay-card">
              <div>
                <h2>{esc(group_name)}</h2>
                <p>{stats['count']} features · {stats['avg']}% maturity · {stats['blocked']} blocked</p>
              </div>
              <div class="bar"><span style="width:{stats['avg']}%"></span></div>
            </section>
            """
        )
        feature_rows.append(
            f"<tr class='group-row'><th colspan='10'>{esc(group_name)}</th></tr>"
        )
        for item in sorted(items, key=lambda r: r["feature_id"]):
            current = item["current_level"]
            target = item["target_level"]
            status_key = item.get("status", "").strip().lower()
            status_color = STATUS_COLORS.get(status_key, "#6b7280")
            cells = []
            current_score = LEVEL_SCORE.get(current, 0)
            for level in LEVELS[1:]:
                level_score = LEVEL_SCORE[level]
                active = level_score <= current_score
                target_mark = " target" if level == target else ""
                style = f"background:{LEVEL_COLORS[level] if active else '#eef2f7'}"
                cells.append(
                    f"<td class='level-cell{target_mark}' title='{esc(level)} {esc(LEVEL_LABELS[level])}'><span style='{style}'>{esc(level) if active else ''}</span></td>"
                )
            feature_rows.append(
                f"""
                <tr>
                  <td class="id">{esc(item['feature_id'])}</td>
                  <td class="feature">{esc(item['feature_name'])}</td>
                  <td>{esc(item['type'] or 'F')}</td>
                  <td>{esc(item['owner'])}</td>
                  <td>{esc(item['iter'])}</td>
                  <td><span class="status" style="background:{status_color}">{esc(item['status'] or 'todo')}</span></td>
                  {''.join(cells)}
                  <td class="evidence">{render_evidence(item.get('evidence', ''))}</td>
                </tr>
                """
            )

    legend = "".join(
        f"<span><i style='background:{LEVEL_COLORS[l]}'></i>{l}: {esc(LEVEL_LABELS[l])}</span>"
        for l in LEVELS[1:]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
  :root {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; background: #f6f7f9; }}
  body {{ margin: 0; }}
  header {{ padding: 28px 32px 18px; background: #111827; color: white; }}
  h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
  h2 {{ margin: 0 0 8px; font-size: 16px; letter-spacing: 0; }}
  p {{ margin: 0; color: #d1d5db; }}
  main {{ padding: 24px 32px 40px; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; margin: 18px 0 0; }}
  .stat {{ background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); border-radius: 8px; padding: 12px; }}
  .stat b {{ display: block; font-size: 24px; margin-bottom: 3px; }}
  .stat span {{ color: #cbd5e1; font-size: 13px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; color: #475569; }}
  .legend span {{ display: inline-flex; align-items: center; gap: 6px; font-size: 13px; }}
  .legend i {{ width: 14px; height: 14px; border-radius: 3px; display: inline-block; }}
  .mainstay-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-bottom: 22px; }}
  .mainstay-card {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }}
  .mainstay-card p {{ color: #64748b; font-size: 13px; }}
  .bar {{ height: 8px; background: #eef2f7; border-radius: 999px; overflow: hidden; margin-top: 12px; }}
  .bar span {{ display: block; height: 100%; background: linear-gradient(90deg, #f97316, #facc15, #38bdf8, #2563eb); }}
  .table-wrap {{ overflow: auto; background: white; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }}
  table {{ border-collapse: collapse; width: 100%; min-width: 980px; }}
  th, td {{ border-bottom: 1px solid #edf0f4; padding: 10px 10px; text-align: left; font-size: 13px; vertical-align: middle; }}
  thead th {{ position: sticky; top: 0; background: #f8fafc; z-index: 1; color: #475569; font-weight: 700; }}
  .group-row th {{ background: #e5e7eb; color: #111827; font-size: 14px; }}
  .id {{ font-weight: 700; color: #111827; white-space: nowrap; }}
  .feature {{ min-width: 210px; }}
  .status {{ color: white; font-size: 12px; padding: 3px 7px; border-radius: 999px; white-space: nowrap; }}
  .level-cell {{ width: 64px; text-align: center; padding: 6px; }}
  .level-cell span {{ display: block; height: 30px; line-height: 30px; border-radius: 6px; color: #0f172a; font-weight: 700; }}
  .level-cell.target span {{ outline: 2px solid #111827; outline-offset: 2px; }}
  .evidence {{ max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  a {{ color: #2563eb; text-decoration: none; }}
  @media (max-width: 760px) {{ header, main {{ padding-left: 16px; padding-right: 16px; }} .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }} }}
</style>
</head>
<body>
<header>
  <h1>{esc(title)}</h1>
  <p>Air Game Dev PM heatmap · generated {esc(now)}</p>
  <div class="stats">
    <div class="stat"><b>{overall['count']}</b><span>features</span></div>
    <div class="stat"><b>{overall['avg']}%</b><span>overall maturity</span></div>
    <div class="stat"><b>{overall['l4']}</b><span>L4 polished</span></div>
    <div class="stat"><b>{overall['blocked']}</b><span>blocked</span></div>
  </div>
</header>
<main>
  <div class="legend">{legend}</div>
  <section class="mainstay-grid">{''.join(group_cards)}</section>
  <section class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Feature ID</th><th>Feature</th><th>Type</th><th>Owner</th><th>Iter</th><th>Status</th>
          <th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>Evidence</th>
        </tr>
      </thead>
      <tbody>{''.join(feature_rows)}</tbody>
    </table>
  </section>
</main>
</body>
</html>"""


def render_evidence(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("http://") or value.startswith("https://"):
        return f"<a href='{esc(value)}'>{esc(value)}</a>"
    return esc(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an Air PM feature heatmap HTML.")
    parser.add_argument("input", type=Path, help="Input CSV or JSON file.")
    parser.add_argument("-o", "--output", type=Path, default=Path("air_pm_heatmap.html"))
    parser.add_argument("--title", default="Air Game Dev PM Heatmap")
    args = parser.parse_args()

    rows = read_rows(args.input)
    if not rows:
        raise SystemExit("No feature rows found.")
    args.output.write_text(render_html(rows, args.title), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
