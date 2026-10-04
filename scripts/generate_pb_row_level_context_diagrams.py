#!/usr/bin/env python3
"""Generate PB row-level context diagrams from report config JSON files."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path("/workspace")
CONFIG_DIR = ROOT / "extracted" / "report_configs" / "report_configs"
MAIN_CONFIG = CONFIG_DIR / "main_config.json"
OUTPUT_MD = ROOT / "pb_row_level_context_diagrams.md"


def normalize(text: str) -> str:
    return " ".join(str(text).split())


def safe_label(text: str) -> str:
    text = normalize(text).replace('"', "'")
    return text[:120] + ("..." if len(text) > 120 else "")


def table_num_from_name(path: Path) -> int:
    match = re.search(r"pb_t(\d+)", path.name)
    if not match:
        raise ValueError(f"Cannot determine table number from {path.name}")
    return int(match.group(1))


def extract_name(rule: dict) -> str:
    for key in ("expected_name_en", "expected_name_ru", "expected_name_tg"):
        value = normalize(rule.get(key, ""))
        if value:
            return value
    return "(unnamed)"


def parent_candidates(code: str) -> list[str]:
    c = normalize(code)
    if not c:
        return []

    has_trailing_dot = c.endswith(".")
    core = c[:-1] if has_trailing_dot else c
    parts = core.split(".")
    candidates: list[str] = []

    if len(parts) > 1:
        for i in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:i])
            candidates.append(prefix + ".")
            if not has_trailing_dot:
                candidates.append(prefix)

    if "." in c:
        first = c.split(".", 1)[0]
        candidates.extend([first + ".", first])

    seen = set()
    deduped: list[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def build_hierarchy(rules: list[dict]) -> tuple[dict[int, int | None], dict[int, list[int]]]:
    # Parent resolution uses nearest previously seen matching code to keep duplicates stable.
    parents: dict[int, int | None] = {}
    children: dict[int, list[int]] = {idx: [] for idx in range(len(rules))}
    code_to_seen_indexes: dict[str, list[int]] = {}

    for idx, rule in enumerate(rules):
        code = normalize(rule.get("code", ""))
        parent_idx = None

        for candidate in parent_candidates(code):
            seen = code_to_seen_indexes.get(candidate, [])
            if seen:
                parent_idx = seen[-1]
                break

        parents[idx] = parent_idx
        if parent_idx is not None:
            children[parent_idx].append(idx)

        code_to_seen_indexes.setdefault(code, []).append(idx)

    return parents, children


def table_titles() -> dict[int, str]:
    if not MAIN_CONFIG.exists():
        return {}

    data = json.loads(MAIN_CONFIG.read_text(encoding="utf-8"))
    output: dict[int, str] = {}
    for entry in data.get("conf_list", []):
        raw_num = str(entry.get("table_number", "")).strip()
        if raw_num.isdigit():
            output[int(raw_num)] = normalize(entry.get("table_name", ""))
    return output


def descendants_count(node: int, children: dict[int, list[int]]) -> int:
    stack = list(children.get(node, []))
    seen = 0
    while stack:
        cur = stack.pop()
        seen += 1
        stack.extend(children.get(cur, []))
    return seen


def to_mermaid_node(node_id: str, label: str) -> str:
    return f'  {node_id}["{safe_label(label)}"]'


def config_files() -> list[Path]:
    files = sorted(CONFIG_DIR.glob("pb_t*.json"), key=table_num_from_name)
    return files


def generate() -> str:
    titles = table_titles()
    files = config_files()
    sections: list[str] = [
        "# PB Row-Level Context Diagrams",
        "",
        "Generated from `extracted/report_configs/report_configs/pb_t*.json`.",
        "",
    ]

    for cfg in files:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        table_no = table_num_from_name(cfg)
        title = titles.get(table_no, f"Table {table_no}")
        sheet_name = normalize(data.get("sheet_name", ""))
        start_row = data.get("data_start_row", "")
        columns = data.get("columns", {})
        value_cols = columns.get("value_cols", {})
        rules: list[dict] = data.get("rules", [])

        parents, children = build_hierarchy(rules)
        roots = [idx for idx, parent in parents.items() if parent is None]

        sections.extend(
            [
                f"## PB {table_no} — {title}",
                "",
                f"- Config: `{cfg.name}`",
                f"- Sheet: `{sheet_name or '(not set)'}`",
                f"- Data start row: `{start_row if start_row != '' else '(not set)'}`",
                (
                    "- Columns: "
                    f"code=`{columns.get('item_code_col', '(n/a)')}`, "
                    f"name=`{columns.get('item_name_col', '(n/a)')}`, "
                    f"prev=`{value_cols.get('prevent_year', '(n/a)')}`, "
                    f"current=`{value_cols.get('current_year', '(n/a)')}`"
                ),
                f"- Rules: `{len(rules)}` total, `{len(roots)}` top-level",
                "",
                "```mermaid",
                "flowchart TD",
            ]
        )

        root_id = f"pb{table_no}_root"
        meta_id = f"pb{table_no}_meta"
        sections.append(to_mermaid_node(root_id, f"PB {table_no} Row-Level Context"))
        sections.append(
            to_mermaid_node(
                meta_id,
                (
                    f"sheet={sheet_name or '(not set)'} | start_row={start_row if start_row != '' else '(not set)'}"
                    f" | rules={len(rules)}"
                ),
            )
        )
        sections.append(f"  {root_id} --> {meta_id}")

        if not rules:
            empty_id = f"pb{table_no}_empty"
            sections.append(to_mermaid_node(empty_id, "No row rules defined"))
            sections.append(f"  {root_id} --> {empty_id}")
        else:
            for local_idx, rule_idx in enumerate(roots, start=1):
                rule = rules[rule_idx]
                label = f"{normalize(rule.get('code', ''))} {extract_name(rule)}"
                node_id = f"pb{table_no}_top_{local_idx}"
                sections.append(to_mermaid_node(node_id, label))
                sections.append(f"  {root_id} --> {node_id}")

                direct_children = children.get(rule_idx, [])
                for child_no, child_idx in enumerate(direct_children, start=1):
                    child = rules[child_idx]
                    nested = descendants_count(child_idx, children)
                    child_label = (
                        f"{normalize(child.get('code', ''))} {extract_name(child)}"
                        + (f" (+{nested} nested)" if nested else "")
                    )
                    child_id = f"pb{table_no}_top_{local_idx}_c_{child_no}"
                    sections.append(to_mermaid_node(child_id, child_label))
                    sections.append(f"  {node_id} --> {child_id}")

        sections.extend(["```", ""])

    return "\n".join(sections)


def main() -> None:
    OUTPUT_MD.write_text(generate(), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
