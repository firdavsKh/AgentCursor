#!/usr/bin/env python3
"""Generate the PB hierarchy: detailed tables allocated under the rows of the high-level tables."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/workspace")
OUTPUT_MD = ROOT / "pb_hierarchy.md"
TOTAL_TABLES = 32

HIGH_LEVEL = {
    1: "Brief analytical BoP presentation",
    2: "Brief standard BoP presentation",
}

# (node id, parent node id, label). Labels follow the row codes of PB1/PB2.
NODES = [
    ("ca", "root", "I. Current account"),
    ("gs", "ca", "1. Goods and services"),
    ("goods", "gs", "1.1 Goods"),
    ("g_adj", "goods", "Trade adjustments and balance"),
    ("g_cty", "goods", "Trade by country"),
    ("g_cmd", "goods", "Trade by commodity"),
    ("g_exp", "g_cmd", "Exports by commodity"),
    ("g_imp", "g_cmd", "Imports by commodity"),
    ("serv", "gs", "1.2 Services"),
    ("pi", "ca", "2. Primary income"),
    ("si", "ca", "3. Secondary income"),
    ("cap", "root", "II. Capital account"),
    ("fa", "root", "III. Financial account"),
    ("di", "fa", "4. Direct investment"),
    ("pf", "fa", "5. Portfolio investment"),
    ("der", "fa", "6. Financial derivatives"),
    ("oi", "fa", "7. Other investment"),
    ("oi_a", "oi", "7.1 Assets"),
    ("oi_l", "oi", "7.2 Liabilities"),
    ("res", "fa", "Reserve assets"),
]

# PB number -> (node id, content basis taken from the PB Excel files in output_files/).
ALLOCATION = {
    3: ("g_adj", "Foreign trade turnover with NBT adjustments (coverage, FOB, processing)"),
    4: ("g_adj", "Trade balance by main commodities with volumes and world prices"),
    5: ("g_cty", "Export / import / surplus by country"),
    6: ("g_cty", "Export / import / surplus by country"),
    24: ("g_cty", "Export / import by country"),
    27: ("g_cty", "Trade by country, weight and cost"),
    10: ("g_cmd", "Trade by commodity section (HS sections)"),
    7: ("g_exp", "Total on export"),
    9: ("g_exp", "Exports: nuts, grapes, dried fruits, oilseeds"),
    11: ("g_exp", "Total on export"),
    13: ("g_exp", "Total on export"),
    15: ("g_exp", "Total on export"),
    17: ("g_exp", "Total on export"),
    19: ("g_exp", "Total on export"),
    21: ("g_exp", "Total on export"),
    8: ("g_imp", "Total on import"),
    12: ("g_imp", "Total on import"),
    14: ("g_imp", "Imports: wheat, oil products, chemicals"),
    16: ("g_imp", "Imports: wheat, flour, vegetable oil"),
    18: ("g_imp", "Total on import"),
    20: ("g_imp", "Total on import"),
    22: ("g_imp", "Total on import"),
    23: ("serv", "Services by type, credits and debits"),
    25: ("pi", "Compensation of employees, investment income"),
    26: ("si", "General government and private transfers, remittances"),
    28: ("di", "Direct investment inflows and outflows"),
    30: ("di", "Direct investment by country, sum and share"),
    29: ("pf", "Titled Portfolio Investments in main_config; rows list industries"),
    31: ("oi_a", "Other investment assets by sector"),
    32: ("oi_l", "Other investment liabilities by sector"),
}


def validate() -> None:
    node_ids = {node_id for node_id, _, _ in NODES}
    unknown = {pb: node for pb, (node, _) in ALLOCATION.items() if node not in node_ids}
    if unknown:
        raise ValueError(f"Allocations point to unknown nodes: {unknown}")

    placed = set(HIGH_LEVEL) | set(ALLOCATION)
    overlap = set(HIGH_LEVEL) & set(ALLOCATION)
    missing = set(range(1, TOTAL_TABLES + 1)) - placed
    if overlap or missing:
        raise ValueError(f"Overlapping PBs: {sorted(overlap)}; unallocated PBs: {sorted(missing)}")


def tables_under(node_id: str) -> list[int]:
    return sorted(pb for pb, (node, _) in ALLOCATION.items() if node == node_id)


def generate() -> str:
    validate()
    high_level = ", ".join(f"PB{pb}" for pb in HIGH_LEVEL)

    lines = [
        "# PB Hierarchy",
        "",
        f"Detailed PB tables allocated under the rows of the high-level tables ({high_level}).",
        "",
        "```mermaid",
        "flowchart LR",
        f'  root["High-level tables<br/>{"<br/>".join(f"PB{pb}: {title}" for pb, title in HIGH_LEVEL.items())}"]',
    ]

    for node_id, parent, label in NODES:
        lines.append(f'  {node_id}["{label}"]')
        lines.append(f"  {parent} --> {node_id}")
        pbs = tables_under(node_id)
        if pbs:
            leaf = f"{node_id}_pb"
            lines.append(f'  {leaf}(["{" · ".join(f"PB{pb}" for pb in pbs)}"])')
            lines.append(f"  {node_id} --> {leaf}")

    empty = [node_id for node_id, _, _ in NODES if not tables_under(node_id) and not any(p == node_id for _, p, _ in NODES)]
    if empty:
        lines.append("  classDef empty stroke-dasharray: 4 4,color:#888")
        lines.append(f"  class {','.join(empty)} empty")
    lines.extend(["```", ""])

    lines.extend(
        [
            "## Allocation",
            "",
            "| PB | BoP item | Basis |",
            "|---:|---|---|",
        ]
    )
    labels = {node_id: label for node_id, _, label in NODES}
    for pb in sorted(HIGH_LEVEL):
        lines.append(f"| {pb} | High-level table | {HIGH_LEVEL[pb]} |")
    for pb in sorted(ALLOCATION):
        node, basis = ALLOCATION[pb]
        lines.append(f"| {pb} | {labels[node]} | {basis} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUTPUT_MD.write_text(generate(), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
