#!/usr/bin/env python3
"""Break the leaf PB tables of the BoP hierarchy down into their row-level indicators."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_pb_hierarchy import ALLOCATION, NODES  # noqa: E402

ROOT = Path("/workspace")
DATA_DIR = ROOT / "output_files"
OUTPUT_MD = ROOT / "pb_leaf_indicators.md"

MAX_LEAF_CHILDREN = 12

BRANCHES = [
    ("Goods: trade adjustments and trade by country", ["g_adj", "g_cty"]),
    ("Goods: exports by commodity", ["g_exp"]),
    ("Goods: commodity sections and imports by commodity", ["g_cmd", "g_imp"]),
    ("Services", ["serv"]),
    ("Primary and secondary income", ["pi", "si"]),
    ("Financial account", ["di", "pf", "oi_a", "oi_l"]),
]

LABEL_COLUMNS = ["names_en", "item_name_en", "names", "names_ru", "item_name_ru", "item_name_taj", "names_tg"]
CODE_COLUMNS = ["code", "item_code"]
WIDE_VALUE_COLUMNS = {
    "prev_year_quantity_thous_tons": "quantity, thous. tons (previous year)",
    "prev_year_val_thous_usd": "value, thous. USD (previous year)",
    "curr_year_quantity_thous_tons": "quantity, thous. tons (current year)",
    "curr_year_val_thous_usd": "value, thous. USD (current year)",
    "prev_year": "previous year",
    "curr_year": "current year",
}
PERIOD_LABELS = {
    "prevent_year": "previous year",
    "prev_year": "previous year",
    "prevent_cis": "previous year, CIS",
    "prevent_far": "previous year, far abroad",
    "current_year": "current year",
    "curr_year": "current year",
    "current_cis": "current year, CIS",
    "current_far": "current year, far abroad",
}

DATA_TYPE_LABELS = {
    "cis_countries": "CIS",
    "fa_countries": "far abroad",
    "far_abroad": "far abroad",
    "share_percent": "share %",
    "cost (in thousand of usd)": "cost, thous. USD",
    "quantity (tones)": "quantity, tons",
}

MEASURE_NAMES = {
    "credit": "Credit",
    "credits": "Credit",
    "кредит": "Credit",
    "debit": "Debit",
    "debits": "Debit",
    "debet": "Debit",
    "дебет": "Debit",
    "proceeds": "Proceeds",
    "inflow": "Proceeds",
    "outflow": "Outflow",
}

# PB25/PB26 ship Russian-only labels below the first level; English follows BPM6 terminology.
TRANSLATIONS = {
    25: {
        "1": "Compensation of employees",
        "2": "Investment income",
        "2.1": "Direct investment",
        "2.1.1": "Income on equity and investment fund shares",
        "2.1.1.1": "Dividends and withdrawals from income of quasi-corporations (D42D)",
        "2.1.1.1.1": "Direct investor in direct investment enterprises",
        "2.1.1.2": "Reinvested earnings (D43D)",
        "2.1.2": "Interest",
        "2.1.2.1": "Direct investor in direct investment enterprises",
        "2.2": "Portfolio investment",
        "2.2.1": "Investment income on equity and investment fund shares",
        "2.2.1.2": "Investment income attributable to investment fund shareholders",
        "2.2.1.2.1": "Dividends",
        "2.2.2": "Interest",
        "2.2.2.1": "Short-term",
        "2.2.2.2": "Long-term",
        "2.3": "Other investment",
        "2.3.1": "Withdrawals from income of quasi-corporations",
        "2.3.2": "Interest (D41O)",
        "2.4": "Reserve assets",
        "2.4.1": "Income on equity and investment fund shares",
        "2.4.2": "Interest (D41R)",
    },
    26: {
        "1": "General government",
        "1.1": "Current taxes on income, wealth, etc.",
        "1.2": "Social contributions",
        "1.3": "Social benefits",
        "1.4": "Current international cooperation",
        "1.4.1": "Humanitarian aid",
        "1.4.2": "Technical assistance",
        "1.4.3": "Contributions to international organizations",
        "1.5": "Miscellaneous current transfers of general government",
        "1.5.1": "Current transfers to NPISHs",
        "1.5.2": "Other",
        "2": "Financial corporations, nonfinancial corporations, households, and NPISHs",
        "2.1": "Personal transfers (current transfers between resident and nonresident households)",
        "2.1.1": "Workers' remittances",
        "2.2": "Other current transfers",
        "2.2.1": "Current taxes on income, wealth, etc.",
        "2.2.2": "Social contributions",
        "2.2.3": "Social benefits",
        "2.2.4": "Net non-life insurance premiums",
        "2.2.5": "Non-life insurance claims",
        "2.2.6": "Current international cooperation",
        "2.2.7": "Miscellaneous current transfers",
        "2.2.7.1": "Current transfers to NPISHs",
        "2.2.7.2": "Gifts",
    },
}

ROOT_LABELS = {
    23: "Services",
    25: "Primary income",
    26: "Secondary income",
}

# Source codes are shifted (PB28) or flattened to "1.1.1." (PB32), so depth comes from the label position.
DEPTH_BY_LABEL = {
    28: {
        "direct investments": 1,
        "abroad": 2,
        "in republic of tajikistan": 2,
        "in share capital": 3,
        "reinvested earnings": 3,
        "other capital": 3,
        "credit from direct investments": 4,
    },
}
DEPTH_BY_POSITION = {
    32: [1, 2, 3, 4, 4, 4, 2, 2, 3, 3, 3, 3, 2],
}

# Rows at or below this depth are measures of their parent (PB4: valuation, volume, price per commodity).
MEASURE_DEPTH = {4: 4}

TRANSPORT_MODE = re.compile(r"(transport|modes of transport|postal)", re.IGNORECASE)
TRANSPORT_FLOW = {"passenger", "freight", "other"}

HOMOGLYPHS = str.maketrans("АВЕКМНОРСТХаеорсху", "ABEKMHOPCTXaeopcxy")
LATIN = re.compile(r"[A-Za-z]")
CYRILLIC = re.compile(r"[\u0400-\u04FF]")


@dataclass
class Node:
    code: str
    label: str
    depth: int
    measures: list[str] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)

    def add_measure(self, measure: str) -> None:
        if measure and measure not in self.measures:
            self.measures.append(measure)

    def descendants(self) -> int:
        return sum(1 + child.descendants() for child in self.children)


@dataclass
class Table:
    pb: int
    source: str
    root: Node
    breakdown: list[str]
    value_columns: list[str]


def file_year(path: Path) -> int:
    years = re.findall(r"20\d\d", path.name)
    return int(years[0]) if years else 0


def latest_file(pb: int) -> Path:
    files = [p for p in DATA_DIR.glob(f"PB{pb}.*.xlsx")]
    if not files:
        raise FileNotFoundError(f"No Excel file for PB{pb} in {DATA_DIR}")
    return max(files, key=lambda p: (file_year(p), p.name))


def split_code(raw: object) -> tuple[list[str], str]:
    if raw is None:
        return [], ""
    text = str(raw).strip().strip(".")
    numeric: list[str] = []
    parts = text.split(".")
    for index, part in enumerate(parts):
        if part.strip().isdigit():
            numeric.append(part.strip())
        else:
            return numeric, ".".join(parts[index:]).strip()
    return numeric, ""


def fix_np_corruption(text: str) -> str:
    """PB23 English labels have r/t replaced by N/P inside words (e.g. 'PNanspoNP')."""

    def fix(token: str) -> str:
        if re.search(r"[a-z]", token) and re.search(r".[NP]", token):
            fixed = token.replace("N", "r").replace("P", "t")
            return fixed[0].upper() + fixed[1:] if token[0].isupper() and token[0] not in "NP" else fixed
        return token

    return " ".join(fix(token) for token in text.split(" "))


def clean_label(text: str, pb: int) -> str:
    text = re.sub(r"_x000D_", " ", text)
    text = re.split(r"\s{10,}", text.strip())[0]
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^reference:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\d+(\.\d+)*\.?\s*(?=\D)", "", text)
    text = text.strip(" *:").replace("**", "").replace("*", "").strip()
    if pb == 23:
        text = fix_np_corruption(text)
        if text.lower().startswith(("в т.ч. оплачиваемый", "аз ҷумла аз ҷониби коргарони")):
            text = "payable by border, seasonal and other short-term workers"
    if LATIN.search(text) and len(LATIN.findall(text)) > len(CYRILLIC.findall(text)):
        text = text.translate(HOMOGLYPHS)
    return text


def pick_label(row: dict, pb: int, numeric: list[str]) -> str:
    candidates = [str(row[col]) for col in LABEL_COLUMNS if col in row and row[col] not in (None, "")]

    def score(text: str) -> tuple[int, int]:
        latin, cyrillic = len(LATIN.findall(text)), len(CYRILLIC.findall(text))
        return (1, latin) if latin > cyrillic else (0, 0)

    best = max(candidates, key=score, default="")
    if candidates and score(best)[0] == 0:
        translated = TRANSLATIONS.get(pb, {}).get(".".join(numeric))
        if translated:
            return translated
        russian = [str(row[col]) for col in ("item_name_ru", "names_ru") if row.get(col)]
        best = russian[0] if russian else best
    return clean_label(best, pb)


def measure_name(suffix: str, label: str) -> str | None:
    for key in (suffix.lower(), label.lower()):
        if key in MEASURE_NAMES:
            return MEASURE_NAMES[key]
    return None


def normalize_measure(label: str) -> str:
    text = re.sub(r"\s+", " ", label.lower()).strip()
    text = text.replace("for 1 ton", "per 1 ton").replace("price world change", "world price change")
    text = re.sub(r"world price \(?\s*per 1 ton\)", "world price (per 1 ton)", text)
    return re.sub(r"average price \(\s*per", "average price (per", text)


def placeholder(label: str) -> bool:
    return label.lower() in {"category name en", "наименование категории", "название категории на тдж"}


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    sheet = openpyxl.load_workbook(path, read_only=True).active
    rows = list(sheet.iter_rows(values_only=True))
    header = [str(cell) for cell in rows[0]]
    return header, [dict(zip(header, row)) for row in rows[1:] if any(cell is not None for cell in row)]


def build_table(pb: int) -> Table:
    path = latest_file(pb)
    header, rows = read_rows(path)
    code_col = next(col for col in CODE_COLUMNS if col in header)

    breakdown = sorted({str(r["data_type"]) for r in rows if r.get("data_type")}, key=str.lower)
    order = list(PERIOD_LABELS)
    periods = sorted(
        {str(r["period"]) for r in rows if r.get("period")},
        key=lambda period: (order.index(period) if period in order else len(order), period),
    )
    value_columns = [label for col, label in WIDE_VALUE_COLUMNS.items() if col in header]
    if periods:
        value_columns = [PERIOD_LABELS.get(p, p) for p in periods]

    root = Node("", ROOT_LABELS.get(pb, f"PB{pb}"), 0)
    stack: list[Node] = [root]
    by_code: dict[str, Node] = {}
    seen: set[tuple] = set()
    occurrences: Counter = Counter()
    position = 0
    last = root

    for row in rows:
        numeric, suffix = split_code(row.get(code_col))
        label = pick_label(row, pb, numeric)
        group = (row.get("data_type"), row.get("period"), row.get(code_col), label)
        occurrences[group] += 1
        key = (row.get(code_col), label, occurrences[group])
        if key in seen:
            continue
        seen.add(key)

        measure = measure_name(suffix, label)
        if measure:
            target = by_code.get(".".join(numeric)) if suffix and numeric else (root if suffix else last)
            (target or last).add_measure(measure)
            continue
        if not label:
            continue
        if not numeric and suffix and last is root:
            continue

        if not numeric and not suffix:
            if label.lower().startswith("total"):
                depth = 1
            elif last is root:
                continue
            else:
                depth = last.depth
        else:
            depth = len(numeric) + (1 if suffix else 0)

        if pb in DEPTH_BY_LABEL:
            depth = DEPTH_BY_LABEL[pb].get(label.lower(), depth)
        if position < len(DEPTH_BY_POSITION.get(pb, [])):
            depth = DEPTH_BY_POSITION[pb][position]
        if pb == 23 and numeric[:1] == ["3"] and label != "Transport":
            if TRANSPORT_MODE.search(label) or label.lower().startswith("for all modes"):
                depth = 2
            elif label.lower() in TRANSPORT_FLOW:
                depth = 3
            elif suffix:
                depth = 4
        position += 1

        if pb in MEASURE_DEPTH and depth >= MEASURE_DEPTH[pb]:
            owner = next(node for node in reversed(stack) if node.depth < MEASURE_DEPTH[pb])
            owner.add_measure(normalize_measure(label))
            continue

        if placeholder(label):
            hs = row.get("tnved_code") or row.get("product_code")
            label = f"HS {hs} (name missing in source)" if hs else "(name missing in source)"

        code = ".".join(numeric + ([suffix] if suffix else []))
        node = Node(code, label, depth)
        parent_code = ".".join(numeric[:-1])
        implied = TRANSLATIONS.get(pb, {}).get(parent_code)
        if implied and not suffix and parent_code not in by_code:
            while stack[-1].depth >= depth - 1:
                stack.pop()
            parent = Node(parent_code, f"{implied} (implied by row codes)", depth - 1)
            stack[-1].children.append(parent)
            stack.append(parent)
            by_code[parent_code] = parent
        while stack[-1].depth >= depth:
            stack.pop()
        stack[-1].children.append(node)
        stack.append(node)
        by_code[code] = node
        last = node

    nest_under_total(root)
    return Table(pb, path.name, root, breakdown, value_columns)


def nest_under_total(root: Node) -> None:
    totals = [child for child in root.children if child.label.lower().startswith("total") and not child.children]
    if len(totals) != 1 or len(root.children) == 1:
        return
    total = totals[0]
    total.children = [child for child in root.children if child is not total]
    root.children = [total]

    def shift(node: Node) -> None:
        node.depth += 1
        for child in node.children:
            shift(child)

    for child in total.children:
        shift(child)


def mermaid_text(text: str, limit: int = 60) -> str:
    text = text.replace('"', "'").replace("#", "No.")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


class Diagram:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.counter = 0

    def new_id(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}_{self.counter}"

    def node(self, node_id: str, label: str, shape: str = "box") -> None:
        if shape == "stadium":
            self.lines.append(f'  {node_id}(["{label}"])')
        elif shape == "note":
            self.lines.append(f'  {node_id}>"{label}"]')
        else:
            self.lines.append(f'  {node_id}["{label}"]')

    def edge(self, parent: str, child: str) -> None:
        self.lines.append(f"  {parent} --> {child}")

    def subtree(self, parent_id: str, node: Node) -> None:
        children = node.children
        if not children:
            return
        if all(not child.children for child in children) and len(children) > MAX_LEAF_CHILDREN:
            examples = ", ".join(mermaid_text(child.label, 28) for child in children[:3])
            summary = self.new_id(parent_id)
            self.node(summary, f"{len(children)} items<br/>e.g. {examples}, …", "note")
            self.edge(parent_id, summary)
            return
        for child in children:
            child_id = self.new_id(parent_id)
            self.node(child_id, mermaid_text(child.label))
            self.edge(parent_id, child_id)
            self.subtree(child_id, child)


def table_measures(table: Table) -> list[str]:
    found: list[str] = []

    def walk(node: Node) -> None:
        for measure in node.measures:
            if measure not in found:
                found.append(measure)
        for child in node.children:
            walk(child)

    walk(table.root)
    return found


def pb_caption(table: Table, wrapper: Node | None = None) -> str:
    parts = [f"PB{table.pb}" + (f" · {wrapper.label}" if wrapper else "")]
    measures = table_measures(table)
    if table.pb in MEASURE_DEPTH:
        parts.append(f"per item: {len(measures)} measures")
    elif measures:
        parts.append(" / ".join(measures))
    if table.breakdown:
        parts.append(" · ".join(DATA_TYPE_LABELS.get(item.lower(), item) for item in table.breakdown))
    return "<br/>".join(mermaid_text(part, 70) for part in parts)


def node_path(node_id: str) -> str:
    labels = {nid: (parent, label) for nid, parent, label in NODES}
    chain = []
    while node_id in labels:
        parent, label = labels[node_id]
        chain.append(label)
        node_id = parent
    return " › ".join(reversed(chain))


def overview_diagram(title: str, node_ids: list[str], tables: dict[int, Table]) -> list[str]:
    diagram = Diagram()
    labels = {nid: label for nid, _, label in NODES}
    for node_id in node_ids:
        diagram.node(node_id, mermaid_text(labels[node_id]))
        for pb in sorted(pb for pb, (target, _) in ALLOCATION.items() if target == node_id):
            pb_id = f"pb{pb}"
            start, wrapper = tables[pb].root, None
            if len(start.children) == 1 and start.children[0].children:
                start = wrapper = start.children[0]
            diagram.node(pb_id, pb_caption(tables[pb], wrapper), "stadium")
            diagram.edge(node_id, pb_id)
            diagram.subtree(pb_id, start)
    return [f"### {title}", "", "```mermaid", "flowchart LR", *diagram.lines, "```", ""]


def detail_section(table: Table) -> list[str]:
    node_id = ALLOCATION[table.pb][0]
    diagram = Diagram()
    root_id = f"pb{table.pb}"
    diagram.node(root_id, pb_caption(table), "stadium")
    diagram.subtree(root_id, table.root)

    measures = table_measures(table)
    lines = [
        f"### PB{table.pb} · {node_path(node_id)}",
        "",
        f"- Source: `output_files/{table.source}`",
        f"- Indicators: {table.root.descendants()}",
    ]
    if measures:
        lines.append(f"- Row measures: {', '.join(measures)}")
    if table.breakdown:
        lines.append(f"- Breakdown (`data_type`): {', '.join(table.breakdown)}")
    if table.value_columns:
        lines.append(f"- Values: {'; '.join(table.value_columns)}")
    lines.extend(["", "```mermaid", "flowchart LR", *diagram.lines, "```", ""])

    lines.extend(
        [
            "<details>",
            f"<summary>All PB{table.pb} indicators</summary>",
            "",
            "| Code | Indicator | Measures |",
            "|---|---|---|",
        ]
    )

    def walk(node: Node) -> None:
        for child in node.children:
            indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * (child.depth - 1)
            label = child.label.replace("|", "/")
            lines.append(f"| {child.code or ''} | {indent}{label} | {', '.join(child.measures)} |")
            walk(child)

    walk(table.root)
    lines.extend(["", "</details>", ""])
    return lines


def validate(tables: dict[int, Table]) -> None:
    missing = sorted(set(ALLOCATION) - set(tables))
    empty = sorted(pb for pb, table in tables.items() if not table.root.children)
    if missing or empty:
        raise ValueError(f"Leaf PBs without tables: {missing}; leaf PBs without indicators: {empty}")
    branch_nodes = {node for _, nodes in BRANCHES for node in nodes}
    unbranched = sorted(pb for pb, (node, _) in ALLOCATION.items() if node not in branch_nodes)
    if unbranched:
        raise ValueError(f"Leaf PBs outside the overview branches: {unbranched}")


def generate() -> str:
    tables = {pb: build_table(pb) for pb in sorted(ALLOCATION)}
    validate(tables)

    lines = [
        "# PB Leaf Indicators",
        "",
        "Row-level indicators of every leaf table in the PB hierarchy (`pb_hierarchy.md`),",
        "read from the latest Excel file of each table in `output_files/`.",
        "",
        "- Credit / Debit / Proceeds / Outflow rows are shown as measures of the indicator they belong to.",
        "- Charts show every indicator and sub-indicator; only flat lists of more than 12 countries or commodities"
        " are collapsed (they are listed in full in the tables).",
        "- PB25 and PB26 only carry Russian labels below the first level; they are shown in English (BPM6 terms).",
        "",
        "## Overview by BoP branch",
        "",
    ]
    for title, node_ids in BRANCHES:
        lines.extend(overview_diagram(title, node_ids, tables))

    lines.extend(["## Leaf tables", ""])
    order = [node_id for _, node_ids in BRANCHES for node_id in node_ids]
    for node_id in order:
        for pb in sorted(pb for pb, (target, _) in ALLOCATION.items() if target == node_id):
            lines.extend(detail_section(tables[pb]))

    lines.extend(
        [
            "## Coverage",
            "",
            "| PB | BoP item | Indicators | Row measures | Breakdown | Values |",
            "|---:|---|---:|---|---|---|",
        ]
    )
    labels = {nid: label for nid, _, label in NODES}
    for pb in sorted(tables):
        table = tables[pb]
        lines.append(
            f"| {pb} | {labels[ALLOCATION[pb][0]]} | {table.root.descendants()} | "
            f"{', '.join(table_measures(table)) or '-'} | {', '.join(table.breakdown) or '-'} | "
            f"{'; '.join(table.value_columns) or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUTPUT_MD.write_text(generate(), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
