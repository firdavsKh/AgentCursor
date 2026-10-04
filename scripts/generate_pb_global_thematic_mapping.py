#!/usr/bin/env python3
"""Generate global-to-thematic PB mapping diagrams."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
OUTPUT_MD = ROOT / "pb_global_thematic_mapping.md"
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


def safe(text: str, max_len: int = 100) -> str:
    text = normalize(text).replace('"', "'")
    return text[:max_len] + ("..." if len(text) > max_len else "")


def md_cell(value: str | int) -> str:
    return str(value).replace("|", "\\|")


def resolve_config_dir() -> Path:
    for candidate in CONFIG_DIR_CANDIDATES:
        if candidate.exists() and any(candidate.glob("pb_t*.json")):
            return candidate
    raise FileNotFoundError(
        "No report config directory found. Expected one of: "
        + ", ".join(str(x) for x in CONFIG_DIR_CANDIDATES)
    )


def table_no(path: Path) -> int:
    match = re.search(r"pb_t(\d+)", path.name)
    if not match:
        raise ValueError(f"Cannot parse table number from {path.name}")
    return int(match.group(1))


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
    records: list[dict] = []

    for cfg in sorted(config_dir.glob("pb_t*.json"), key=table_no):
        data = json.loads(cfg.read_text(encoding="utf-8"))
        number = table_no(cfg)
        rules = data.get("rules", [])
        records.append(
            {
                "pb": number,
                "title": titles.get(number, f"Table {number}"),
                "rules_count": len(rules),
                "theme": classify_theme(number, len(rules)),
            }
        )
    return records


def generate(records: list[dict], config_dir: Path) -> str:
    if not records:
        raise ValueError("No PB records found to map.")

    records_sorted = sorted(records, key=lambda r: r["pb"])
    global_records = records_sorted[:3]
    global_pbs = {r["pb"] for r in global_records}
    other_records = [r for r in records_sorted if r["pb"] not in global_pbs]

    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in other_records:
        grouped[record["theme"]].append(record)

    lines = [
        "# PB Global-to-Thematic Mapping Diagram",
        "",
        f"Generated from `{config_dir.relative_to(ROOT)}/pb_t*.json`.",
        "",
        "## Global tables mapped to thematic groups",
        "",
        "```mermaid",
        "flowchart LR",
        '  hub["First Global Tables"]',
    ]

    for g in global_records:
        gid = f"g_{g['pb']}"
        glabel = f"PB {g['pb']}: {safe(g['title'], max_len=80)}"
        lines.append(f'  {gid}["{glabel}"]')
        lines.append(f"  hub --> {gid}")

    theme_idx = 0
    for theme in THEME_ORDER:
        members = grouped.get(theme, [])
        if not members:
            continue
        theme_idx += 1
        tid = f"th_{theme_idx}"
        lines.append(f'  {tid}["{safe(theme, max_len=120)} ({len(members)})"]')
        for g in global_records:
            lines.append(f"  g_{g['pb']} --> {tid}")

        for member in members:
            pid = f"pb_{member['pb']}"
            plabel = (
                f"PB {member['pb']}: {safe(member['title'], max_len=70)}"
                f"<br/>rules={member['rules_count']}"
            )
            plabel = plabel.replace('"', "'")
            lines.append(f'  {pid}["{plabel}"]')
            lines.append(f"  {tid} --> {pid}")

    lines.extend(["```", ""])

    lines.append("## Mapping matrix")
    lines.append("")
    lines.append("| Global PB | Global title | Thematic group | Mapped PBs |")
    lines.append("|---:|---|---|---|")

    for g in global_records:
        for theme in THEME_ORDER:
            members = grouped.get(theme, [])
            if not members:
                continue
            mapped_pbs = ", ".join(f"PB{m['pb']}" for m in members)
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(g["pb"]),
                        md_cell(g["title"]),
                        md_cell(theme),
                        md_cell(mapped_pbs),
                    ]
                )
                + " |"
            )
    lines.append("")

    lines.append("## Theme summary")
    lines.append("")
    lines.append("| Theme | PB count | PB list |")
    lines.append("|---|---:|---|")
    for theme in THEME_ORDER:
        members = grouped.get(theme, [])
        if not members:
            continue
        pb_list = ", ".join(f"PB{m['pb']}" for m in members)
        lines.append(f"| {md_cell(theme)} | {len(members)} | {md_cell(pb_list)} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    config_dir = resolve_config_dir()
    records = collect_records(config_dir)
    OUTPUT_MD.write_text(generate(records, config_dir), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
