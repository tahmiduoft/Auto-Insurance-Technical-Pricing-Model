"""
Build a refreshable/static Excel pricing calculator from real-data model outputs.

Run after:
    python python/real_auto_pricing_model.py --sample-size 100000

Creates:
    excel/freMTPL2_Auto_Pricing_Tool.xlsx
"""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

import pandas as pd
import xlsxwriter


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_required(root: Path):
    outputs = root / "outputs"
    needed = [
        outputs / "rating_factors_DrivAgeBand.csv",
        outputs / "rating_factors_VehAgeBand.csv",
        outputs / "rating_factors_BonusMalusBand.csv",
        outputs / "rating_factors_Area.csv",
        outputs / "rating_factors_VehGas.csv",
        outputs / "rating_factors_VehPowerBand.csv",
        outputs / "rating_factors_DensityBand.csv",
        outputs / "model_performance.csv",
        outputs / "segment_rate_indications.csv",
        outputs / "qa_report.csv",
        outputs / "scenario_results.csv",
        outputs / "portfolio_summary.json",
    ]
    missing = [str(p) for p in needed if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing model outputs. Run real_auto_pricing_model.py first. Missing:\n" + "\n".join(missing))
    return needed


def write_df(ws, df: pd.DataFrame, start_row: int, start_col: int, wb, table_name: str | None = None):
    header_fmt = wb.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E78", "border": 1})
    body_fmt = wb.add_format({"border": 1})
    for c, col in enumerate(df.columns):
        ws.write(start_row, start_col + c, col, header_fmt)
    for r, row in enumerate(df.itertuples(index=False), start=start_row + 1):
        for c, val in enumerate(row):
            ws.write(r, start_col + c, val, body_fmt)
    if table_name and len(df) > 0:
        ws.add_table(start_row, start_col, start_row + len(df), start_col + len(df.columns) - 1, {"name": table_name, "columns": [{"header": col} for col in df.columns]})
    for c, col in enumerate(df.columns):
        width = min(max(12, len(str(col)) + 2, int(df[col].astype(str).str.len().quantile(0.95)) + 2 if len(df) else 12), 32)
        ws.set_column(start_col + c, start_col + c, width)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=project_root())
    args = parser.parse_args()
    root = args.root
    load_required(root)
    outputs = root / "outputs"
    excel_dir = root / "excel"
    excel_dir.mkdir(exist_ok=True)
    xlsx_path = excel_dir / "freMTPL2_Auto_Pricing_Tool.xlsx"

    summary = json.loads((outputs / "portfolio_summary.json").read_text())
    factors = {
        "DrivAgeBand": pd.read_csv(outputs / "rating_factors_DrivAgeBand.csv"),
        "VehAgeBand": pd.read_csv(outputs / "rating_factors_VehAgeBand.csv"),
        "BonusMalusBand": pd.read_csv(outputs / "rating_factors_BonusMalusBand.csv"),
        "Area": pd.read_csv(outputs / "rating_factors_Area.csv"),
        "VehGas": pd.read_csv(outputs / "rating_factors_VehGas.csv"),
        "VehPowerBand": pd.read_csv(outputs / "rating_factors_VehPowerBand.csv"),
        "DensityBand": pd.read_csv(outputs / "rating_factors_DensityBand.csv"),
    }
    model_perf = pd.read_csv(outputs / "model_performance.csv")
    segment = pd.read_csv(outputs / "segment_rate_indications.csv")
    qa = pd.read_csv(outputs / "qa_report.csv")
    scenarios = pd.read_csv(outputs / "scenario_results.csv")

    wb = xlsxwriter.Workbook(xlsx_path)
    fmt_title = wb.add_format({"bold": True, "font_size": 18, "font_color": "#1F4E78"})
    fmt_section = wb.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E78", "border": 1})
    fmt_label = wb.add_format({"bold": True, "border": 1, "bg_color": "#D9EAF7"})
    fmt_input = wb.add_format({"bg_color": "#FFF2CC", "border": 1})
    fmt_output = wb.add_format({"bg_color": "#E2F0D9", "border": 1, "num_format": "€#,##0"})
    fmt_pct = wb.add_format({"bg_color": "#E2F0D9", "border": 1, "num_format": "0.0%"})
    fmt_num = wb.add_format({"border": 1, "num_format": "#,##0.00"})
    fmt_note = wb.add_format({"italic": True, "font_color": "#666666", "text_wrap": True})

    # Cover
    ws = wb.add_worksheet("Cover")
    ws.write("A1", "freMTPL2 Auto Insurance Pricing Model", fmt_title)
    ws.write("A3", "Purpose", fmt_section)
    ws.write("A4", "Real-data actuarial pricing workflow using public French motor third-party liability data. The workbook is generated from Python model outputs.", fmt_note)
    ws.write("A6", "Important limitation", fmt_section)
    ws.write("A7", "freMTPL2 contains claim counts, exposure, risk features, and claim amounts, but not actual charged premiums. This tool calculates a technical/indicated premium from predicted pure premium and selected assumptions; it does not calculate a true rate change against actual current premium unless you supply your own current premium benchmark.", fmt_note)
    ws.write("A9", "Run order", fmt_section)
    for i, cmd in enumerate([
        "python python/download_data.py",
        "python python/real_auto_pricing_model.py --sample-size 100000",
        "python python/build_excel_tool.py",
        "Open excel/freMTPL2_Auto_Pricing_Tool.xlsx",
    ], start=10):
        ws.write(i, 0, cmd)
    ws.set_column("A:A", 110)

    # Calculator
    calc = wb.add_worksheet("Pricing Calculator")
    calc.write("A1", "Technical Premium Calculator", fmt_title)
    calc.write("A3", "Inputs", fmt_section)
    inputs = [
        ("Driver age band", "30-39", "DrivAgeBand"),
        ("Vehicle age band", "2-5", "VehAgeBand"),
        ("Bonus-Malus band", "50-59", "BonusMalusBand"),
        ("Area", "D", "Area"),
        ("Vehicle gas", "Regular", "VehGas"),
        ("Vehicle power band", "6-7", "VehPowerBand"),
        ("Density band", "501-1500", "DensityBand"),
    ]
    calc.write_row("A4", ["Input", "Selected value", "Factor source"], fmt_label)
    for idx, (label, default, source) in enumerate(inputs, start=5):
        calc.write(idx - 1, 0, label, fmt_label)
        calc.write(idx - 1, 1, default, fmt_input)
        calc.write(idx - 1, 2, source, fmt_label)
    # assumptions
    calc.write("A13", "Scenario assumptions", fmt_section)
    assumption_rows = [("Loss trend", 0.04), ("Expense load", 0.30), ("Target loss ratio", 0.65), ("Profit load", 0.03), ("Optional supplied current premium", 0)]
    calc.write_row("A14", ["Assumption", "Value"], fmt_label)
    for i, (label, val) in enumerate(assumption_rows, start=15):
        calc.write(i - 1, 0, label, fmt_label)
        calc.write(i - 1, 1, val, fmt_input)
        if i < 19:
            calc.set_row(i - 1, None, None)
    calc.write("A22", "Outputs", fmt_section)
    outputs_rows = [
        "Portfolio base selected pure premium",
        "Combined rating relativity",
        "Selected pure premium",
        "Trended pure premium",
        "Technical / indicated premium",
        "Rate change vs optional supplied current premium",
        "Recommendation",
    ]
    for i, label in enumerate(outputs_rows, start=23):
        calc.write(i - 1, 0, label, fmt_label)
    base_pp = summary["portfolio_selected_pure_premium"]
    calc.write("B23", base_pp, fmt_output)
    # VLOOKUP formulas by Factor Tables sheet positions
    lookup_formulas = []
    # approximate ranges will point at the consolidated factor table in Factor Tables (columns A:C variable, level, relativity)
    for row in range(5, 12):
        lookup_formulas.append(f'SUMIFS(\'Factor Tables\'!$C:$C,\'Factor Tables\'!$A:$A,C{row},\'Factor Tables\'!$B:$B,B{row})')
    calc.write_formula("B24", "=" + "*".join(lookup_formulas), fmt_num)
    calc.write_formula("B25", "=B23*B24", fmt_output)
    calc.write_formula("B26", "=B25*(1+B15)", fmt_output)
    calc.write_formula("B27", "=B26*(1+B16)/B17*(1+B18)", fmt_output)
    calc.write_formula("B28", '=IF(B19>0,B27/B19-1,"N/A")', fmt_pct)
    calc.write_formula("B29", '=IF(B19=0,"No current premium supplied",IF(B28>0.05,"Consider increase",IF(B28<-0.05,"Consider decrease","Near adequate")))', fmt_output)
    calc.write("A31", "Interpretation", fmt_section)
    calc.write("A32", "Changing inputs changes a quote/scenario using model-derived relativities. It does not retrain the Python model. To update the factor tables, rerun Python and regenerate this workbook.", fmt_note)
    calc.set_column("A:A", 42)
    calc.set_column("B:B", 24)
    calc.set_column("C:C", 22)

    # Factor Tables consolidated
    fws = wb.add_worksheet("Factor Tables")
    fws.write("A1", "Model-derived rating factors", fmt_title)
    consolidated = []
    for var, df in factors.items():
        level_col = var
        part = df[["variable", level_col, "relativity", "policies", "exposure", "selected_pure_premium"]].copy()
        part.columns = ["variable", "level", "relativity", "policies", "exposure", "selected_pure_premium"]
        consolidated.append(part)
    con = pd.concat(consolidated, ignore_index=True)
    write_df(fws, con, 2, 0, wb, "FactorTable")
    fws.set_column("A:F", 20)

    # Model Performance
    perf_ws = wb.add_worksheet("Model Performance")
    perf_ws.write("A1", "Model performance", fmt_title)
    write_df(perf_ws, model_perf, 2, 0, wb, "ModelPerformance")

    # Segment Indications
    seg_ws = wb.add_worksheet("Segment Indications")
    seg_ws.write("A1", "Segment technical premium indications", fmt_title)
    write_df(seg_ws, segment.head(500), 2, 0, wb, "SegmentIndications")

    # QA
    qa_ws = wb.add_worksheet("QA Checks")
    qa_ws.write("A1", "Data QA and governance checks", fmt_title)
    write_df(qa_ws, qa, 2, 0, wb, "QAChecks")

    # Scenarios
    sc_ws = wb.add_worksheet("Scenarios")
    sc_ws.write("A1", "Scenario controls", fmt_title)
    write_df(sc_ws, scenarios, 2, 0, wb, "Scenarios")

    # Data dictionary / sources
    dd = wb.add_worksheet("Data Dictionary")
    dd.write("A1", "Data dictionary and sources", fmt_title)
    dd.write("A3", "Dataset", fmt_section)
    dd.write("A4", "freMTPL2: public French motor third-party liability insurance dataset from CASdatasets / Hugging Face mirror.", fmt_note)
    dd.write("A6", "Source URLs", fmt_section)
    for i, url in enumerate([
        "https://dutangc.github.io/CASdatasets/reference/freMTPL.html",
        "https://huggingface.co/datasets/mabilton/fremtpl2",
        "https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html",
    ], start=7):
        dd.write(i - 1, 0, url)
    dd.write("A11", "AXIS-inspired governance", fmt_section)
    dd.write("A12", "This is not actual Moody's AXIS. The project borrows an AXIS-style structure: model-point file, assumption/scenario tables, model run outputs, QA/audit checks, and reproducible run sequence.", fmt_note)
    dd.set_column("A:A", 120)

    for sheet in wb.worksheets():
        sheet.freeze_panes(3, 0)
    wb.close()
    print(f"Saved {xlsx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
