#!/usr/bin/env python3
"""Marimo app for PB skeleton-level visualizations.

This app reads prepared model outputs and visualizes only top-level
hierarchy members (skeleton level: hierarchy_level == 1).
"""

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from pathlib import Path

    return Path, mo, pd, px


@app.cell
def _(mo):
    mo.md("""
    # PB Skeleton Visualizations
    Interactive views for top-level PB categories (`hierarchy_level == 1`).
    """)
    return


@app.cell
def _(Path, mo):
    # Prefer notebook location so the default works regardless of process cwd.
    notebook_dir = mo.notebook_dir()
    repo_root = Path(notebook_dir).resolve().parent if notebook_dir else Path.cwd()
    default_model_dir = str(repo_root / "prepared_model")
    model_dir = mo.ui.text(value=default_model_dir, label="Model directory")
    top_n = mo.ui.slider(3, 12, value=6, step=1, label="Top N categories in trend")
    mo.hstack([model_dir, top_n], justify="start")
    return model_dir, top_n


@app.cell
def _(Path, mo, model_dir, pd):
    base_dir = Path(model_dir.value).expanduser().resolve()
    fact_path = base_dir / "fact_rows_long.csv"
    category_path = base_dir / "dim_category_member.csv"
    period_path = base_dir / "dim_report_period.csv"

    missing = [
        str(path) for path in (fact_path, category_path, period_path) if not path.exists()
    ]
    load_error = ""
    if missing:
        fact_df = pd.DataFrame()
        category_df = pd.DataFrame()
        period_df = pd.DataFrame()
        load_error = "Missing files:\n- " + "\n- ".join(missing)
        status = mo.md(f"❌ {load_error}\n\nRun `prepare_model_pieces.py` first.")
    else:
        fact_df = pd.read_csv(fact_path)
        category_df = pd.read_csv(category_path)
        period_df = pd.read_csv(period_path)
        status = mo.md(
            f"Loaded from `{base_dir}` — "
            f"**{len(fact_df):,}** fact rows, **{len(category_df):,}** categories."
        )

    if not fact_df.empty:
        fact_df["measure_value"] = pd.to_numeric(
            fact_df["measure_value"], errors="coerce"
        ).fillna(0.0)
        fact_df["pb_table"] = (
            pd.to_numeric(fact_df["pb_table"], errors="coerce").fillna(0).astype(int)
        )

    if not category_df.empty:
        category_df["pb_table"] = (
            pd.to_numeric(category_df["pb_table"], errors="coerce").fillna(0).astype(int)
        )
        category_df["hierarchy_level"] = (
            pd.to_numeric(category_df["hierarchy_level"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    if not period_df.empty:
        period_df["period_sort_key"] = (
            pd.to_numeric(period_df["period_sort_key"], errors="coerce")
            .fillna(-1)
            .astype(int)
        )

    status
    return category_df, fact_df, period_df


@app.cell
def _(category_df, fact_df, pd):
    if category_df.empty or fact_df.empty:
        skeleton_dim = pd.DataFrame()
        fact_skeleton = pd.DataFrame()
    else:
        skeleton_dim = category_df[category_df["hierarchy_level"] == 1].copy()
        skeleton_dim["skeleton_label"] = (
            skeleton_dim["category_code"].fillna("").astype(str).str.strip()
            + " — "
            + skeleton_dim["category_name_primary"].fillna("").astype(str).str.strip()
        ).str.strip(" —")

        fact_skeleton = fact_df.merge(
            skeleton_dim[
                ["category_member_key", "pb_table", "skeleton_label"]
            ],
            on=["category_member_key", "pb_table"],
            how="inner",
        )
    return fact_skeleton, skeleton_dim


@app.cell
def _(fact_skeleton, mo, period_df):
    if fact_skeleton.empty:
        pb_selector = mo.ui.dropdown(options=["(no data)"], value="(no data)", label="PB table")
        measure_selector = mo.ui.dropdown(
            options=["(no data)"], value="(no data)", label="Measure type"
        )
        period_selector = mo.ui.dropdown(options=["latest"], value="latest", label="Period")
    else:
        pb_options = sorted(fact_skeleton["table_key"].dropna().unique().tolist())
        measure_options = sorted(fact_skeleton["measure_type_key"].dropna().unique().tolist())
        period_options = ["latest"]
        if not period_df.empty:
            ordered_periods = (
                period_df.sort_values("period_sort_key")["report_period_key"]
                .dropna()
                .astype(str)
                .tolist()
            )
            period_options.extend(ordered_periods)
        pb_selector = mo.ui.dropdown(options=pb_options, value=pb_options[0], label="PB table")
        preferred_measures = ["current_year", "prevent_year", "curr_year", "prev_year"]
        default_measure = next(
            (m for m in preferred_measures if m in measure_options),
            measure_options[0],
        )
        measure_selector = mo.ui.dropdown(
            options=measure_options,
            value=default_measure,
            label="Measure type",
        )
        period_selector = mo.ui.dropdown(options=period_options, value="latest", label="Period")

    mo.hstack([pb_selector, measure_selector, period_selector], justify="start")
    return measure_selector, pb_selector, period_selector


@app.cell
def _(
    fact_skeleton,
    measure_selector,
    pb_selector,
    pd,
    period_df,
    period_selector,
):
    if fact_skeleton.empty:
        plot_df = pd.DataFrame()
        filtered_df = pd.DataFrame()
    else:
        filtered_df = fact_skeleton[
            (fact_skeleton["table_key"] == pb_selector.value)
            & (fact_skeleton["measure_type_key"] == measure_selector.value)
        ].copy()

        if not period_df.empty:
            filtered_df = filtered_df.merge(
                period_df[["report_period_key", "period_sort_key"]],
                on="report_period_key",
                how="left",
            )
            filtered_df["period_sort_key"] = pd.to_numeric(
                filtered_df["period_sort_key"], errors="coerce"
            ).fillna(-1)
        else:
            filtered_df["period_sort_key"] = -1

        if not filtered_df.empty:
            if period_selector.value == "latest":
                latest_sort = filtered_df["period_sort_key"].max()
                period_slice = filtered_df[filtered_df["period_sort_key"] == latest_sort]
            else:
                period_slice = filtered_df[
                    filtered_df["report_period_key"] == period_selector.value
                ]
        else:
            period_slice = filtered_df

        plot_df = (
            period_slice.groupby(["skeleton_label"], as_index=False)["measure_value"]
            .sum()
            .sort_values("measure_value", ascending=False)
        )
    return filtered_df, plot_df


@app.cell
def _(plot_df):
    print (plot_df.columns)
    return


@app.cell
def _(mo, pb_selector, period_selector, plot_df, px):
    if plot_df.empty:
        chart_bar = mo.md("No skeleton-level records for selected filters.")
    else:
        fig = px.bar(
            plot_df,
            x="measure_value",
            y="skeleton_label",
            orientation="h",
            title=f"{pb_selector.value}: skeleton categories ({period_selector.value})",
            labels={
                "measure_value": "Measure value",
                "skeleton_label": "Top-level category",
            },
        )
        fig.update_layout(height=520, yaxis={"categoryorder": "total ascending"})
        chart_bar = mo.ui.plotly(fig)
    chart_bar
    return


@app.cell
def _(filtered_df, mo, px, top_n):
    if filtered_df.empty:
        chart_trend = mo.md("No trend data for selected table/measure.")
    else:
        totals = (
            filtered_df.groupby("skeleton_label", as_index=False)["measure_value"]
            .sum()
            .assign(abs_value=lambda frame: frame["measure_value"].abs())
            .sort_values("abs_value", ascending=False)
            .head(top_n.value)
        )
        selected_labels = set(totals["skeleton_label"].tolist())
        trend = filtered_df[filtered_df["skeleton_label"].isin(selected_labels)].copy()

        if "period_sort_key" in trend.columns:
            trend = trend.sort_values("period_sort_key")

        trend_grouped = (
            trend.groupby(["report_period_key", "skeleton_label"], as_index=False)[
                "measure_value"
            ].sum()
        )

        fig_trend = px.line(
            trend_grouped,
            x="report_period_key",
            y="measure_value",
            color="skeleton_label",
            markers=True,
            title="Skeleton-level trend by period",
            labels={
                "report_period_key": "Reporting period",
                "measure_value": "Measure value",
                "skeleton_label": "Top-level category",
            },
        )
        fig_trend.update_layout(height=520)
        chart_trend = mo.ui.plotly(fig_trend)
    chart_trend
    return


@app.cell
def _(mo, skeleton_dim):
    if skeleton_dim.empty:
        coverage = mo.md("No skeleton dimension rows found.")
    else:
        summary = (
            skeleton_dim.groupby("pb_table", as_index=False)["category_member_key"]
            .count()
            .rename(columns={"category_member_key": "top_level_categories"})
            .sort_values("pb_table")
        )
        coverage = mo.vstack(
            [mo.md("### PB skeleton coverage"), mo.ui.table(summary)]
        )
    coverage
    return


if __name__ == "__main__":
    app.run()
