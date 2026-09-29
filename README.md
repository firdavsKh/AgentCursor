# AgentCursor

## Prepare fact/dimension model pieces

Use the script below to extract archives and generate normalized model outputs:

```bash
python3 scripts/prepare_model_pieces.py \
  --output-rar output_files.rar \
  --config-rar report_configs.rar \
  --output-dir prepared_model
```

Generated outputs include:

- `fact_rows_long.csv` (normalized long fact rows)
- `dim_table.csv`
- `dim_report_period.csv`
- `dim_category_member.csv`
- `bridge_category_closure.csv`
- `dim_measure_type.csv`
- `dim_data_scope.csv`
- `ref_dim_category_last_seen.csv`
- `ref_dim_period_bucket_last_seen.csv`
- `ref_dim_type_last_seen.csv`

Notes:

- Extraction uses `unar`. Install it if missing (`sudo apt-get install unar`).
- Python dependency: `openpyxl` (`pip3 install openpyxl`).
- Some archive entries may fail extraction (RAR method support); the script
  continues with all successfully extracted files and logs extraction output
  into `<output-dir>/_logs/`.
