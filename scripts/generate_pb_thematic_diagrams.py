#!/usr/bin/env python3
"""Generate thematic PB diagrams and per-PB dimensions from report configs."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
OUTPUT_MD = ROOT / "pb_thematic_diagrams.md"
CONFIG_DIR_CANDIDATES = [
    ROOT / "report_configs",
    ROOT / "extracted" / "report_configs" / "report_configs",
]
THEME_ORDER = [
    "Core Balance of Payments",
    "Detailed Services Breakdown",
    "Income Accounts",
    "Investment & Financial Accounts",
    "Reference / Minimal Templates",
    "Supplementary Tables",
]


def normalize(text: str) -> str:
    return " ".join(str(text).split())


def safe(text: str, max_len: int = 120) -> str:
    text = normalize(text).replace('"', "'")
    return text[:max_len] + ("..." if len(text) > max_len else "")


def md_cell(value: str | int) -> str:
    return str(value).replace("|", "\\|")


def table_no(path: Path) -> int:
    match = re.search(r"pb_t(\d+)", path.name)
    if not match:
        raise ValueError(f"Cannot parse table number from {path.name}")
    return int(match.group(1))


def resolve_config_dir() -> Path:
    for candidate in CONFIG_DIR_CANDIDATES:
        if candidate.exists() and any(candidate.glob("pb_t*.json")):
            return candidate
    raise FileNotFoundError(
        "No report config directory found. Expected one of: "
        + ", ".join(str(x) for x in CONFIG_DIR_CANDIDATES)
    )


def load_titles(config_dir: Path) -> dict[int, str]:
    main = config_dir / "main_config.json"
    if not main.exists():
        return {}

    data = json.loads(main.read_text(encoding="utf-8"))
    titles: dict[int, str] = {}
    for item in data.get("conf_list", []):
        raw = str(item.get("table_number", "")).strip()
        if raw.isdigit():
            titles[int(raw)] = normalize(item.get("table_name", ""))
    return titles


def parent_candidates(code: str) -> list[str]:
    code = normalize(code)
    if not code:
        return []

    has_dot = code.endswith(".")
    core = code[:-1] if has_dot else code
    parts = core.split(".")
    out: list[str] = []

    if len(parts) > 1:
        for idx in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:idx])
            out.append(prefix + ".")
            if not has_dot:
                out.append(prefix)

    if "." in code:
        first = code.split(".", 1)[0]
        out.extend([first + ".", first])

    deduped: list[str] = []
    seen = set()
    for item in out:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def top_level_count(rules: list[dict]) -> int:
    seen_codes: dict[str, int] = {}
    roots = 0
    for rule in rules:
        code = normalize(rule.get("code", ""))
        parent = None
        for candidate in parent_candidates(code):
            if candidate in seen_codes:
                parent = seen_codes[candidate]
                break
        if parent is None:
            roots += 1
        seen_codes[code] = 1
    return roots


def classify_theme(pb_number: int, rules_count: int) -> str:
    if pb_number in {1, 2, 3}:
        return "Core Balance of Payments"
    if pb_number == 23:
        return "Detailed Services Breakdown"
    if pb_number in {25, 26}:
        return "Income Accounts"
    if pb_number in {28, 29, 30, 31, 32}:
        return "Investment & Financial Accounts"
    if rules_count <= 1:
        return "Reference / Minimal Templates"
    return "Supplementary Tables"


def collect_records(config_dir: Path) -> list[dict]:
    titles = load_titles(config_dir)
    files = sorted(config_dir.glob("pb_t*.json"), key=table_no)
    records: list[dict] = []

    for cfg in files:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        rules = data.get("rules", [])
        number = table_no(cfg)
        cols = data.get("columns", {})
        values = cols.get("value_cols", {})

        records.append(
            {
                "pb": number,
                "title": titles.get(number, f"Table {number}"),
                "config": cfg.name,
                "sheet": normalize(data.get("sheet_name", "")) or "(not set)",
                "start_row": data.get("data_start_row", "(not set)"),
                "code_col": cols.get("item_code_col", "(n/a)"),
                "name_col": cols.get("item_name_col", "(n/a)"),
                "prev_col": values.get("prevent_year", "(n/a)"),
                "cur_col": values.get("current_year", "(n/a)"),
                "rules_count": len(rules),
                "top_count": top_level_count(rules),
                "theme": classify_theme(number, len(rules)),
            }
        )
    return records


def generate(records: list[dict], config_dir: Path) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        grouped[rec["theme"]].append(rec)

    lines = [
        "# PB Thematic Diagram and Dimensions",
        "",
        f"Generated from `{config_dir.relative_to(ROOT)}/pb_t*.json`.",
        "",
        "## Thematic Diagram",
        "",
        "```mermaid",
        "flowchart LR",
        '  root["PB Reports by Theme"]',
    ]

    for idx, theme in enumerate(THEME_ORDER, start=1):
        members = grouped.get(theme, [])
        if not members:
            continue
        theme_id = f"th_{idx}"
        lines.append(f'  {theme_id}["{safe(theme, max_len=200)} ({len(members)})"]')
        lines.append(f"  root --> {theme_id}")

        for member in members:
            pb_id = f"pb_{member['pb']}"
            pb_label = (
                f"PB {member['pb']}: {safe(member['title'], max_len=72)}<br/>"
                f"code={member['code_col']}, name={member['name_col']}, prev={member['prev_col']}, cur={member['cur_col']}<br/>"
                f"sheet={member['sheet']}, start_row={member['start_row']}, rules={member['rules_count']}, top={member['top_count']}"
            ).replace('"', "'")
            lines.append(f'  {pb_id}["{pb_label}"]')
            lines.append(f"  {theme_id} --> {pb_id}")

    lines.extend(["```", "", "## Dimensions by Theme", ""])

    for theme in THEME_ORDER:
        members = grouped.get(theme, [])
        if not members:
            continue

        lines.append(f"### {theme}")
        lines.append("")
        lines.append(
            "| PB | Title | Sheet | Start row | Code col | Name col | Prev col | Current col | Rules | Top-level |"
        )
        lines.append("|---:|---|---|---:|---|---|---|---|---:|---:|")
        for member in members:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(member["pb"]),
                        md_cell(member["title"]),
                        md_cell(member["sheet"]),
                        md_cell(member["start_row"]),
                        md_cell(member["code_col"]),
                        md_cell(member["name_col"]),
                        md_cell(member["prev_col"]),
                        md_cell(member["cur_col"]),
                        md_cell(member["rules_count"]),
                        md_cell(member["top_count"]),
                    ]
                )
                + " |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    config_dir = resolve_config_dir()
    records = collect_records(config_dir)
    OUTPUT_MD.write_text(generate(records, config_dir), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
