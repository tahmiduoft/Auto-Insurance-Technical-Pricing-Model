# SQL Layer

This folder adds a small, executable SQL layer to the auto insurance pricing project. SQL is not required for the Python model to run, but it demonstrates database-style policy/claims data preparation, QA checks, and segment analysis.

## Purpose

The SQL scripts show how the raw freMTPL2 frequency and severity files could be handled in a relational database:

1. Create policy and claim tables.
2. Aggregate claim amounts by policy ID.
3. Join policy risk features to claim amounts.
4. Create actuarial fields such as observed frequency, severity, and pure premium.
5. Run QA checks for invalid exposure, claim-count mismatches, and unmatched claims.
6. Produce segment-level summaries for pricing analysis.

## Files

- `01_create_tables.sql` — table definitions for the raw policy and claim data.
- `02_model_point_build.sql` — creates a model-point table by joining policy data with aggregated claim amounts.
- `03_qa_checks.sql` — creates a QA check view.
- `04_segment_analysis.sql` — creates segment-level pricing summary views.

## Optional local run

You can run the SQL pipeline through:

```bash
python python/run_sql_pipeline.py
```

This loads the raw CSV files into a local SQLite database, runs the SQL scripts, and exports:

- `data/processed/model_points_fremtpl2_sql.csv`
- `outputs/sql_qa_checks.csv`
- `outputs/sql_segment_analysis_by_area_age_power.csv`
- `outputs/sql_segment_analysis_by_area.csv`

The main Python model can still use its own data-preparation logic. This SQL layer is included to demonstrate SQL proficiency and database-style actuarial data preparation.
