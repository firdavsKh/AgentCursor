#!/usr/bin/env python3
"""Build static visualizations from prepared model CSV outputs.

The script reads model pieces produced by prepare_model_pieces.py and generates
an HTML dashboard with:
- summary KPI cards
- fact/category/measure/fallback bar charts
- period timeline table
- sample category hierarchy trees
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate static visualizations for prepared model outputs."
    )
    parser.add_argument(
        "--model-dir",
        default="prepared_model",
        help="Directory with generated model CSV files",
    )
    parser.add_argument(
        "--output-dir",
        default="prepared_model/visualizations",
        help="Directory for dashboard outputs",
    )
    parser.add_argument(
        "--top-tables",
        type=int,
        default=6,
        help="How many most-populated tables to include in bar charts",
    )
    parser.add_argument(
        "--tree-tables",
        default="PB1,PB2,PB23",
        help="Comma-separated table keys to show hierarchy trees for",
    )
    parser.add_argument(
        "--tree-max-nodes",
        type=int,
        default=250,
        help="Maximum hierarchy nodes to render per table tree",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_hierarchy_html(
    rows: list[dict[str, str]],
    pb_table: int,
    max_nodes: int,
) -> str:
    code_to_name: dict[str, str] = {}
    parent_to_children: defaultdict[str, list[str]] = defaultdict(list)
    present_codes: set[str] = set()

    for row in rows:
        if parse_int(row.get("pb_table", "")) != pb_table:
            continue
        code = (row.get("category_code") or "").strip()
        if not code:
            continue
        present_codes.add(code)
        name = (row.get("category_name_primary") or row.get("category_name_en") or "").strip()
        label = name if name else code
        code_to_name[code] = label
        parent = (row.get("parent_category_code") or "").strip()
        parent_to_children[parent].append(code)

    if not present_codes:
        return "<p>No hierarchy rows found.</p>"

    for parent in list(parent_to_children):
        parent_to_children[parent] = sorted(set(parent_to_children[parent]))

    roots = parent_to_children.get("", [])
    if not roots:
        # fallback root detection for edge cases where parent is missing in data
        roots = sorted(
            code for code in present_codes if "." not in code.rstrip(".")
        )

    rendered_nodes = 0

    def render_node(code: str) -> str:
        nonlocal rendered_nodes
        if rendered_nodes >= max_nodes:
            return ""
        rendered_nodes += 1
        node_label = f"{code} - {code_to_name.get(code, code)}"
        children_html = ""
        child_codes = parent_to_children.get(code, [])
        child_parts = []
        for child in child_codes:
            if child == code:
                continue
            child_html = render_node(child)
            if child_html:
                child_parts.append(child_html)
            if rendered_nodes >= max_nodes:
                break
        if child_parts:
            children_html = f"<ul>{''.join(child_parts)}</ul>"
        return f"<li><span>{node_label}</span>{children_html}</li>"

    parts = []
    for root in roots:
        root_html = render_node(root)
        if root_html:
            parts.append(root_html)
        if rendered_nodes >= max_nodes:
            break

    truncated = (
        f"<p class='trunc-note'>Tree truncated at {max_nodes} nodes.</p>"
        if rendered_nodes >= max_nodes
        else ""
    )
    return f"<ul class='tree'>{''.join(parts)}</ul>{truncated}"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    model_dir = Path(args.model_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    fact_path = model_dir / "fact_rows_long.csv"
    dim_category_path = model_dir / "dim_category_member.csv"
    dim_period_path = model_dir / "dim_report_period.csv"
    dim_measure_path = model_dir / "dim_measure_type.csv"
    summary_path = model_dir / "run_summary.json"
    fallback_path = model_dir / "_logs" / "measure_column_fallbacks.csv"

    required = [fact_path, dim_category_path, dim_period_path, dim_measure_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required model files:\n- " + "\n- ".join(missing)
        )

    fact_rows = read_csv(fact_path)
    category_rows = read_csv(dim_category_path)
    period_rows = read_csv(dim_period_path)
    measure_rows = read_csv(dim_measure_path)
    fallback_rows = read_csv(fallback_path) if fallback_path.exists() else []

    run_summary: dict[str, Any] = {}
    if summary_path.exists():
        run_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        run_summary = {
            "files_processed": 0,
            "facts_rows": len(fact_rows),
            "dim_category_rows": len(category_rows),
            "period_rows": len(period_rows),
            "measure_types": len(measure_rows),
            "data_scopes": 0,
            "measure_column_fallbacks": len(fallback_rows),
        }

    facts_by_table = Counter(row.get("table_key", "") for row in fact_rows)
    categories_by_table = Counter(
        f"PB{parse_int(row.get('pb_table', ''))}" for row in category_rows
    )
    measure_by_type = Counter(row.get("measure_type_key", "") for row in fact_rows)
    fallback_by_table = Counter(
        f"PB{parse_int(row.get('pb_table', ''))}" for row in fallback_rows
    )
    max_depth_by_table: dict[str, int] = defaultdict(int)
    for row in category_rows:
        key = f"PB{parse_int(row.get('pb_table', ''))}"
        depth = parse_int(row.get("hierarchy_level", "0"))
        if depth > max_depth_by_table[key]:
            max_depth_by_table[key] = depth

    top_tables = [
        table_key
        for table_key, _ in sorted(
            facts_by_table.items(),
            key=lambda item: (-item[1], item[0]),
        )[: args.top_tables]
    ]

    top_fact_data = [
        {"key": key, "value": facts_by_table.get(key, 0)} for key in top_tables
    ]
    top_category_data = [
        {"key": key, "value": categories_by_table.get(key, 0)} for key in top_tables
    ]
    top_fallback_data = [
        {"key": key, "value": fallback_by_table.get(key, 0)} for key in top_tables
    ]

    top_measures = [
        {"key": key, "value": value}
        for key, value in sorted(
            measure_by_type.items(),
            key=lambda item: (-item[1], item[0]),
        )[:10]
    ]

    period_rows_sorted = sorted(
        period_rows,
        key=lambda row: parse_int(row.get("period_sort_key", "0")),
    )
    period_timeline = [
        {
            "period": row.get("report_period_key", ""),
            "year": row.get("report_year", ""),
            "quarter": row.get("report_quarter", ""),
        }
        for row in period_rows_sorted
    ]

    tree_tables = [value.strip() for value in args.tree_tables.split(",") if value.strip()]
    tree_sections = []
    for table_key in tree_tables:
        if not table_key.startswith("PB"):
            continue
        pb_number = parse_int(table_key[2:])
        tree_html = build_hierarchy_html(
            rows=category_rows,
            pb_table=pb_number,
            max_nodes=args.tree_max_nodes,
        )
        tree_sections.append(
            {
                "table_key": table_key,
                "max_depth": max_depth_by_table.get(table_key, 0),
                "html": tree_html,
            }
        )

    dashboard_data = {
        "summary": run_summary,
        "facts_by_table": top_fact_data,
        "categories_by_table": top_category_data,
        "fallbacks_by_table": top_fallback_data,
        "measures_top": top_measures,
        "period_timeline": period_timeline,
        "tree_tables": tree_sections,
    }

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Prepared Model Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2 {{ margin: 0 0 12px 0; }}
    .subtle {{ color: #6b7280; margin-bottom: 20px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; background: #f9fafb; }}
    .card .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.04em; }}
    .card .value {{ font-size: 22px; font-weight: 700; margin-top: 6px; }}
    .panel {{ margin-bottom: 24px; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; }}
    .chart-row {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
    svg {{ width: 100%; height: 280px; background: #ffffff; border-radius: 6px; }}
    .axis-label {{ font-size: 11px; fill: #4b5563; }}
    .timeline {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .timeline th, .timeline td {{ border: 1px solid #e5e7eb; padding: 6px 8px; text-align: left; }}
    .tree {{ margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.4; }}
    .tree li {{ margin: 2px 0; }}
    .trunc-note {{ color: #b45309; font-size: 12px; margin-top: 8px; }}
    .tree-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Prepared Model Dashboard</h1>
  <p class="subtle">Static visualization generated from model CSV outputs.</p>

  <div id="cards" class="cards"></div>

  <div class="panel">
    <h2>Top tables by fact rows</h2>
    <div class="chart-row"><svg id="factsChart"></svg></div>
  </div>

  <div class="panel">
    <h2>Top tables by category members</h2>
    <div class="chart-row"><svg id="categoriesChart"></svg></div>
  </div>

  <div class="panel">
    <h2>Top measure types by fact rows</h2>
    <div class="chart-row"><svg id="measuresChart"></svg></div>
  </div>

  <div class="panel">
    <h2>Fallback usage by table</h2>
    <div class="chart-row"><svg id="fallbackChart"></svg></div>
    <p class="subtle">Fallback = configured measure columns rejected, inferred columns used.</p>
  </div>

  <div class="panel">
    <h2>Reporting periods timeline</h2>
    <table class="timeline">
      <thead><tr><th>Period key</th><th>Year</th><th>Quarter label</th></tr></thead>
      <tbody id="timelineBody"></tbody>
    </table>
  </div>

  <div class="panel">
    <h2>Sample hierarchy trees</h2>
    <div id="treeGrid" class="tree-grid"></div>
  </div>

  <script>
    const DATA = {json.dumps(dashboard_data, ensure_ascii=False)};

    function addCards() {{
      const order = [
        "files_processed", "facts_rows", "dim_category_rows", "period_rows",
        "measure_types", "data_scopes", "measure_column_fallbacks"
      ];
      const labels = {{
        files_processed: "Files processed",
        facts_rows: "Fact rows",
        dim_category_rows: "Category dim rows",
        period_rows: "Periods",
        measure_types: "Measure types",
        data_scopes: "Data scopes",
        measure_column_fallbacks: "Measure fallbacks",
      }};
      const cards = document.getElementById("cards");
      order.forEach((key) => {{
        const value = DATA.summary[key];
        const el = document.createElement("div");
        el.className = "card";
        el.innerHTML = `<div class="label">${{labels[key] || key}}</div><div class="value">${{value ?? 0}}</div>`;
        cards.appendChild(el);
      }});
    }}

    function drawBarChart(svgId, values, color) {{
      const svg = document.getElementById(svgId);
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      const width = svg.clientWidth || 960;
      const height = svg.clientHeight || 280;
      svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);

      if (!values.length) {{
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", 12);
        text.setAttribute("y", 24);
        text.textContent = "No data";
        svg.appendChild(text);
        return;
      }}

      const margin = {{ top: 20, right: 20, bottom: 80, left: 48 }};
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;
      const maxValue = Math.max(...values.map(v => v.value), 1);
      const barW = innerW / values.length;

      values.forEach((row, idx) => {{
        const h = Math.round((row.value / maxValue) * (innerH - 4));
        const x = margin.left + idx * barW + 8;
        const y = margin.top + innerH - h;

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", Math.max(12, barW - 16));
        rect.setAttribute("height", h);
        rect.setAttribute("fill", color);
        svg.appendChild(rect);

        const valueLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        valueLabel.setAttribute("x", x + Math.max(12, barW - 16) / 2);
        valueLabel.setAttribute("y", y - 6);
        valueLabel.setAttribute("text-anchor", "middle");
        valueLabel.setAttribute("class", "axis-label");
        valueLabel.textContent = String(row.value);
        svg.appendChild(valueLabel);

        const keyLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        keyLabel.setAttribute("x", x + Math.max(12, barW - 16) / 2);
        keyLabel.setAttribute("y", margin.top + innerH + 14);
        keyLabel.setAttribute("text-anchor", "end");
        keyLabel.setAttribute("transform", `rotate(-35 ${{x + Math.max(12, barW - 16) / 2}} ${{margin.top + innerH + 14}})`);
        keyLabel.setAttribute("class", "axis-label");
        keyLabel.textContent = row.key;
        svg.appendChild(keyLabel);
      }});
    }}

    function fillTimeline() {{
      const body = document.getElementById("timelineBody");
      DATA.period_timeline.forEach((row) => {{
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${{row.period}}</td><td>${{row.year}}</td><td>${{row.quarter}}</td>`;
        body.appendChild(tr);
      }});
    }}

    function fillTrees() {{
      const treeGrid = document.getElementById("treeGrid");
      DATA.tree_tables.forEach((row) => {{
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
          <div class="label">${{row.table_key}}</div>
          <div style="margin:6px 0 10px 0;font-size:13px;">Max hierarchy depth: <code>${{row.max_depth}}</code></div>
          ${{row.html}}
        `;
        treeGrid.appendChild(card);
      }});
    }}

    addCards();
    drawBarChart("factsChart", DATA.facts_by_table, "#2563eb");
    drawBarChart("categoriesChart", DATA.categories_by_table, "#059669");
    drawBarChart("measuresChart", DATA.measures_top, "#7c3aed");
    drawBarChart("fallbackChart", DATA.fallbacks_by_table, "#d97706");
    fillTimeline();
    fillTrees();
  </script>
</body>
</html>
"""

    output_dir.mkdir(parents=True, exist_ok=True)
    write_file(output_dir / "index.html", html)
    write_file(
        output_dir / "dashboard_data.json",
        json.dumps(dashboard_data, ensure_ascii=False, indent=2),
    )

    print("Dashboard generated at:", output_dir / "index.html")
    print("Data JSON generated at:", output_dir / "dashboard_data.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
