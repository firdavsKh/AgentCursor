#!/usr/bin/env python3
"""Marimo starter: load all prepared_model CSVs as DataFrames.

Edit mode (full toolkit):
  python -m marimo edit apps/pb_load_all_marimo.py

Run mode (app view):
  python -m marimo run apps/pb_load_all_marimo.py
"""

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from pathlib import Path

    return Path, mo, pd


@app.cell
def _(mo):
    mo.md(
        """
# PB prepared model — load all tables

Starter notebook: every CSV under `prepared_model/` is loaded into a DataFrame.
Build charts / filters in new cells on top of these objects.
"""
    )
    return


@app.cell
def _(Path, mo):
    notebook_dir = mo.notebook_dir()
    repo_root = Path(notebook_dir).resolve().parent if notebook_dir else Path.cwd()
    default_model_dir = str(repo_root / "prepared_model")
    model_dir = mo.ui.text(value=default_model_dir, label="Model directory")
    model_dir
    return model_dir, repo_root


@app.cell
def _(Path, mo, model_dir, pd):
    MODEL_TABLES = (
        "fact_rows_long",
        "dim_table",
        "dim_report_period",
        "dim_category_member",
        "dim_measure_type",
        "dim_data_scope",
        "bridge_category_closure",
        "ref_dim_category_last_seen",
        "ref_dim_period_bucket_last_seen",
        "ref_dim_type_last_seen",
    )

    base_dir = Path(model_dir.value).expanduser().resolve()
    tables: dict[str, pd.DataFrame] = {}
    missing: list[str] = []

    for name in MODEL_TABLES:
        path = base_dir / f"{name}.csv"
        if not path.exists():
            missing.append(str(path))
            tables[name] = pd.DataFrame()
            continue
        frame = pd.read_csv(path)
        # Light numeric coercion for common measure/key columns.
        for col in (
            "measure_value",
            "measure_value_signed",
            "balance_contribution_sign",
            "pb_table",
            "hierarchy_level",
            "period_sort_key",
            "report_year",
            "seen_in_files",
            "distance",
            "source_row",
        ):
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
        tables[name] = frame

    if missing:
        status = mo.md(
            "❌ Missing files (run `scripts/prepare_model_pieces.py` first):\n\n"
            + "\n".join(f"- `{p}`" for p in missing)
        )
    else:
        lines = [
            f"| `{name}` | {len(df):,} | {len(df.columns)} |"
            for name, df in tables.items()
        ]
        status = mo.md(
            f"Loaded from `{base_dir}`\n\n"
            "| table | rows | cols |\n|---|---:|---:|\n"
            + "\n".join(lines)
        )

    status
    return MODEL_TABLES, base_dir, missing, tables


@app.cell
def _(tables):
    # Unpack for convenient use in later cells.
    fact_rows_long = tables["fact_rows_long"]
    dim_table = tables["dim_table"]
    dim_report_period = tables["dim_report_period"]
    dim_category_member = tables["dim_category_member"]
    dim_measure_type = tables["dim_measure_type"]
    dim_data_scope = tables["dim_data_scope"]
    bridge_category_closure = tables["bridge_category_closure"]
    ref_dim_category_last_seen = tables["ref_dim_category_last_seen"]
    ref_dim_period_bucket_last_seen = tables["ref_dim_period_bucket_last_seen"]
    ref_dim_type_last_seen = tables["ref_dim_type_last_seen"]
    return (
        bridge_category_closure,
        dim_category_member,
        dim_data_scope,
        dim_measure_type,
        dim_report_period,
        dim_table,
        fact_rows_long,
        ref_dim_category_last_seen,
        ref_dim_period_bucket_last_seen,
        ref_dim_type_last_seen,
    )


@app.cell
def _(MODEL_TABLES, mo, tables):
    preview_name = mo.ui.dropdown(
        options=list(MODEL_TABLES),
        value="fact_rows_long",
        label="Preview table",
    )
    preview_name
    return preview_name,


@app.cell
def _(mo, preview_name, tables):
    df = tables[preview_name.value]
    if df.empty:
        preview = mo.md(f"`{preview_name.value}` is empty or missing.")
    else:
        preview = mo.vstack(
            [
                mo.md(
                    f"### `{preview_name.value}` — "
                    f"{len(df):,} rows × {len(df.columns)} cols"
                ),
                mo.ui.table(df.head(50), page_size=20),
            ]
        )
    preview
    return df, preview


@app.cell
def _(mo):
    mo.md(
        """
### Next steps

In a new cell, use any loaded frame, for example:

```python
fact_rows_long.head()
dim_category_member.query("hierarchy_level == 1")
```

Or join:

```python
fact_rows_long.merge(dim_category_member, on="category_member_key", how="left")
```
"""
    )
    return


if __name__ == "__main__":
    app.run()
