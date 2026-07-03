"""
Optional SQL pipeline for the freMTPL2 auto pricing project.

This script loads raw freMTPL2 CSV files into a local SQLite database, runs the SQL
scripts in /sql, and exports SQL-generated model-point, QA, and segment outputs.

Usage:
    python python/download_data.py
    python python/run_sql_pipeline.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def execute_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    sql = path.read_text()
    conn.executescript(sql)
    conn.commit()


def main() -> int:
    root = project_root()
    raw_dir = root / "data" / "raw"
    sql_dir = root / "sql"
    processed_dir = root / "data" / "processed"
    outputs_dir = root / "outputs"
    db_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    freq_path = raw_dir / "freMTPL2freq.csv"
    sev_path = raw_dir / "freMTPL2sev.csv"
    if not freq_path.exists() or not sev_path.exists():
        raise FileNotFoundError("Missing raw data. Run `python python/download_data.py` first.")

    db_path = db_dir / "fremtpl2_pricing.sqlite"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        freq = pd.read_csv(freq_path)
        sev = pd.read_csv(sev_path)
        freq.to_sql("freMTPL2freq", conn, index=False, if_exists="replace")
        sev.to_sql("freMTPL2sev", conn, index=False, if_exists="replace")

        # 01_create_tables.sql is included for schema documentation. The CSV loader
        # creates tables directly with pandas to keep this runnable across machines.
        for filename in ["02_model_point_build.sql", "03_qa_checks.sql", "04_segment_analysis.sql"]:
            execute_sql_file(conn, sql_dir / filename)

        pd.read_sql_query("SELECT * FROM model_points_sql", conn).to_csv(processed_dir / "model_points_fremtpl2_sql.csv", index=False)
        pd.read_sql_query("SELECT * FROM sql_qa_checks", conn).to_csv(outputs_dir / "sql_qa_checks.csv", index=False)
        pd.read_sql_query("SELECT * FROM sql_segment_analysis_by_area_age_power", conn).to_csv(outputs_dir / "sql_segment_analysis_by_area_age_power.csv", index=False)
        pd.read_sql_query("SELECT * FROM sql_segment_analysis_by_area", conn).to_csv(outputs_dir / "sql_segment_analysis_by_area.csv", index=False)
    finally:
        conn.close()

    print("SQL pipeline completed successfully.")
    print(f"SQLite database: {db_path}")
    print("Exported SQL outputs to data/processed/ and outputs/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
