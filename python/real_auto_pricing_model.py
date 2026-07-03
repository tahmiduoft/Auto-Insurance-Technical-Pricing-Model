"""
Real-data auto insurance pricing model using freMTPL2.

Inputs:
- data/raw/freMTPL2freq.csv
- data/raw/freMTPL2sev.csv

Outputs:
- data/processed/model_points_fremtpl2.csv
- outputs/model_performance.csv
- outputs/scored_policies.csv
- outputs/segment_rate_indications.csv
- outputs/rating_factors_*.csv
- outputs/scenario_results.csv
- outputs/qa_report.csv
- charts/*.png

Usage:
    python python/download_data.py
    python python/real_auto_pricing_model.py --sample-size 100000
    python python/build_excel_tool.py
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt

import statsmodels.api as sm
import statsmodels.formula.api as smf

RANDOM_STATE = 42


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_raw(root: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    freq_path = root / "data" / "raw" / "freMTPL2freq.csv"
    sev_path = root / "data" / "raw" / "freMTPL2sev.csv"
    if not freq_path.exists() or not sev_path.exists():
        raise FileNotFoundError(
            "Missing raw data. Run `python python/download_data.py` first, or manually place "
            "freMTPL2freq.csv and freMTPL2sev.csv in data/raw/."
        )
    return pd.read_csv(freq_path), pd.read_csv(sev_path)


def make_bands(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DrivAgeBand"] = pd.cut(out["DrivAge"], [17, 24, 29, 39, 49, 59, 69, 120], labels=["18-24", "25-29", "30-39", "40-49", "50-59", "60-69", "70+"], include_lowest=True).astype(str)
    out["VehAgeBand"] = pd.cut(out["VehAge"], [-1, 1, 5, 10, 15, 30, 120], labels=["0-1", "2-5", "6-10", "11-15", "16-30", "31+"], include_lowest=True).astype(str)
    out["BonusMalusBand"] = pd.cut(out["BonusMalus"], [0, 49, 59, 79, 99, 119, 159, 400], labels=["<50", "50-59", "60-79", "80-99", "100-119", "120-159", "160+"], include_lowest=True).astype(str)
    out["VehPowerBand"] = pd.cut(out["VehPower"], [0, 5, 7, 9, 12, 99], labels=["1-5", "6-7", "8-9", "10-12", "13+"], include_lowest=True).astype(str)
    out["DensityBand"] = pd.cut(out["Density"], [0, 100, 500, 1500, 5000, 100000], labels=["0-100", "101-500", "501-1500", "1501-5000", "5001+"], include_lowest=True).astype(str)
    out["LogDensity"] = np.log1p(out["Density"].clip(lower=0))

    # Preserve full category levels so statsmodels can predict on levels that may be
    # rare in the training split but present in scoring data.
    fixed_categories = {
        "Area": list("ABCDEF"),
        "VehGas": ["Regular", "Diesel"],
        "DrivAgeBand": ["18-24", "25-29", "30-39", "40-49", "50-59", "60-69", "70+"],
        "VehAgeBand": ["0-1", "2-5", "6-10", "11-15", "16-30", "31+"],
        "BonusMalusBand": ["<50", "50-59", "60-79", "80-99", "100-119", "120-159", "160+"],
        "VehPowerBand": ["1-5", "6-7", "8-9", "10-12", "13+"],
        "DensityBand": ["0-100", "101-500", "501-1500", "1501-5000", "5001+"],
    }
    for col, cats in fixed_categories.items():
        out[col] = pd.Categorical(out[col].astype(str), categories=cats)
    return out


def clean_and_join(freq: pd.DataFrame, sev: pd.DataFrame, sample_size: int | None) -> pd.DataFrame:
    freq = freq.copy()
    sev = sev.copy()
    freq["IDpol"] = freq["IDpol"].astype(int)
    sev["IDpol"] = sev["IDpol"].astype(int)
    sev_agg = sev.groupby("IDpol", as_index=False).agg(ClaimAmount=("ClaimAmount", "sum"), ClaimCountFromSev=("ClaimAmount", "size"))
    df = freq.merge(sev_agg, on="IDpol", how="left")
    df["ClaimAmount"] = df["ClaimAmount"].fillna(0.0)
    df["ClaimCountFromSev"] = df["ClaimCountFromSev"].fillna(0).astype(int)
    df["ClaimNbRecorded"] = df["ClaimNb"].astype(float)
    df["ClaimNbMismatch"] = df["ClaimNbRecorded"].astype(int) != df["ClaimCountFromSev"].astype(int)
    df = df[df["Exposure"].notna() & (df["Exposure"] > 0)].copy()
    df["Exposure"] = df["Exposure"].clip(lower=1e-6, upper=1.0)
    df["ClaimNb"] = df["ClaimNbRecorded"].clip(lower=0, upper=4)
    df["ClaimAmount"] = df["ClaimAmount"].clip(lower=0, upper=200000)
    df["ZeroAmountPositiveClaim"] = (df["ClaimAmount"] <= 0) & (df["ClaimNb"] > 0)
    df = make_bands(df)
    df["Frequency"] = df["ClaimNb"] / df["Exposure"]
    df["AvgClaimAmount"] = df["ClaimAmount"] / np.maximum(df["ClaimNb"], 1)
    df["PurePremiumObserved"] = df["ClaimAmount"] / df["Exposure"]

    if sample_size is not None and sample_size < len(df):
        rng = np.random.default_rng(RANDOM_STATE)
        claim_rows = df[df["ClaimNb"] > 0]
        non_claim_rows = df[df["ClaimNb"] == 0]
        n_claim = min(len(claim_rows), max(500, int(sample_size * 0.15)))
        n_non = max(0, sample_size - n_claim)
        parts = []
        if n_claim > 0:
            parts.append(claim_rows.sample(n=n_claim, random_state=RANDOM_STATE) if n_claim < len(claim_rows) else claim_rows)
        if n_non > 0:
            parts.append(non_claim_rows.sample(n=min(n_non, len(non_claim_rows)), random_state=RANDOM_STATE))
        df = pd.concat(parts, ignore_index=True).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    return df


MODEL_FORMULA = "C(Area) + C(VehPowerBand) + C(VehGas) + C(DrivAgeBand) + C(VehAgeBand) + C(BonusMalusBand) + LogDensity"


def split_train_test(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(RANDOM_STATE)
    mask = rng.random(len(df)) < 0.75
    return df.loc[mask].copy(), df.loc[~mask].copy()


def fit_models(df: pd.DataFrame) -> Dict[str, object]:
    train_df, test_df = split_train_test(df)
    # Frequency: Poisson count model with log exposure offset.
    freq_formula = f"ClaimNb ~ {MODEL_FORMULA}"
    freq_model = smf.glm(
        formula=freq_formula,
        data=train_df,
        family=sm.families.Poisson(),
        offset=np.log(train_df["Exposure"]),
    ).fit(maxiter=100, disp=0)

    # Severity: Gamma model only on positive losses.
    sev_train = train_df[(train_df["ClaimAmount"] > 0) & (train_df["ClaimNb"] > 0)].copy()
    sev_test = test_df[(test_df["ClaimAmount"] > 0) & (test_df["ClaimNb"] > 0)].copy()
    sev_formula = f"AvgClaimAmount ~ {MODEL_FORMULA}"
    sev_model = smf.glm(
        formula=sev_formula,
        data=sev_train,
        family=sm.families.Gamma(link=sm.families.links.Log()),
        freq_weights=sev_train["ClaimNb"].clip(lower=1),
    ).fit(maxiter=100, disp=0)

    # Tweedie pure premium benchmark.
    tw_formula = f"PurePremiumObserved ~ {MODEL_FORMULA}"
    tweedie_model = smf.glm(
        formula=tw_formula,
        data=train_df,
        family=sm.families.Tweedie(var_power=1.5, link=sm.families.links.Log()),
        freq_weights=train_df["Exposure"],
    ).fit(maxiter=100, disp=0)

    return {"train_df": train_df, "test_df": test_df, "freq_model": freq_model, "sev_model": sev_model, "tweedie_model": tweedie_model, "sev_test": sev_test}


def weighted_mae(y, pred, w):
    return float(np.average(np.abs(np.asarray(y) - np.asarray(pred)), weights=np.asarray(w)))


def weighted_rmse(y, pred, w):
    return float(math.sqrt(np.average((np.asarray(y) - np.asarray(pred)) ** 2, weights=np.asarray(w))))


def evaluate_models(models: Dict[str, object]) -> pd.DataFrame:
    test = models["test_df"]
    rows = []
    freq_pred_count = models["freq_model"].predict(test, offset=np.log(test["Exposure"]))
    freq_pred = freq_pred_count / test["Exposure"]
    rows.append({"model": "Frequency - Poisson GLM", "mae": weighted_mae(test["Frequency"], freq_pred, test["Exposure"]), "rmse": weighted_rmse(test["Frequency"], freq_pred, test["Exposure"]), "target": "Claim frequency"})

    tw_pred = models["tweedie_model"].predict(test)
    rows.append({"model": "Aggregate Pure Premium - Tweedie GLM", "mae": weighted_mae(test["PurePremiumObserved"], tw_pred, test["Exposure"]), "rmse": weighted_rmse(test["PurePremiumObserved"], tw_pred, test["Exposure"]), "target": "Pure premium"})

    sev_test = models["sev_test"]
    if len(sev_test) > 0:
        sev_pred = models["sev_model"].predict(sev_test)
        rows.append({"model": "Severity - Gamma GLM", "mae": weighted_mae(sev_test["AvgClaimAmount"], sev_pred, sev_test["ClaimNb"].clip(lower=1)), "rmse": weighted_rmse(sev_test["AvgClaimAmount"], sev_pred, sev_test["ClaimNb"].clip(lower=1)), "target": "Average claim amount"})
    return pd.DataFrame(rows)


def score_policies(df: pd.DataFrame, models: Dict[str, object], scenarios: dict) -> pd.DataFrame:
    scored = df.copy()
    pred_count = models["freq_model"].predict(scored, offset=np.log(scored["Exposure"]))
    scored["PredFrequency"] = pred_count / scored["Exposure"]
    scored["PredSeverity"] = models["sev_model"].predict(scored)
    scored["PredPurePremiumFreqSev"] = scored["PredFrequency"] * scored["PredSeverity"]
    scored["PredPurePremiumTweedie"] = models["tweedie_model"].predict(scored)
    scored["SelectedPurePremium"] = 0.70 * scored["PredPurePremiumFreqSev"] + 0.30 * scored["PredPurePremiumTweedie"]
    base = scenarios["base"]
    scored["TechnicalPremium_Base"] = scored["SelectedPurePremium"] * (1 + base["loss_trend"]) * (1 + base["expense_load"]) / base["target_loss_ratio"] * (1 + base["profit_load"])
    return scored


def make_qa(freq: pd.DataFrame, sev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {"check": "frequency_rows_raw", "value": len(freq), "status": "info"},
        {"check": "severity_rows_raw", "value": len(sev), "status": "info"},
        {"check": "model_rows_after_cleaning", "value": len(df), "status": "info"},
        {"check": "duplicate_policy_ids_in_freq", "value": int(freq["IDpol"].duplicated().sum()), "status": "warn"},
        {"check": "claims_without_policy_record", "value": int((~sev["IDpol"].isin(freq["IDpol"])).sum()), "status": "warn"},
        {"check": "claimnb_mismatch_policy_rows", "value": int(df["ClaimNbMismatch"].sum()), "status": "warn"},
        {"check": "zero_claim_amount_positive_claim_count", "value": int(df["ZeroAmountPositiveClaim"].sum()), "status": "warn"},
        {"check": "nonpositive_exposure_after_cleaning", "value": int((df["Exposure"] <= 0).sum()), "status": "fail" if int((df["Exposure"] <= 0).sum()) else "pass"},
        {"check": "claim_amount_clipped_at_200k", "value": int((df["ClaimAmount"] >= 200000).sum()), "status": "warn"},
    ])


def weighted_segment_summary(scored: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for keys, g in scored.groupby(group_cols, dropna=False, observed=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        exposure = g["Exposure"].sum()
        if exposure <= 0:
            continue
        row = {col: val for col, val in zip(group_cols, keys)}
        row.update({
            "policies": len(g),
            "exposure": exposure,
            "claim_count": g["ClaimNb"].sum(),
            "observed_frequency": g["ClaimNb"].sum() / exposure,
            "observed_pure_premium": g["ClaimAmount"].sum() / exposure,
            "predicted_frequency": np.average(g["PredFrequency"], weights=g["Exposure"]),
            "predicted_severity": np.average(g["PredSeverity"], weights=g["Exposure"]),
            "selected_pure_premium": np.average(g["SelectedPurePremium"], weights=g["Exposure"]),
            "technical_premium_base": np.average(g["TechnicalPremium_Base"], weights=g["Exposure"]),
        })
        rows.append(row)
    return pd.DataFrame(rows).sort_values("exposure", ascending=False)


def rating_factor_table(scored: pd.DataFrame, variable: str) -> pd.DataFrame:
    base_pp = np.average(scored["SelectedPurePremium"], weights=scored["Exposure"])
    seg = weighted_segment_summary(scored, [variable])
    seg["relativity"] = seg["selected_pure_premium"] / base_pp
    seg["variable"] = variable
    return seg[["variable", variable, "policies", "exposure", "observed_frequency", "observed_pure_premium", "selected_pure_premium", "relativity"]]


def make_lift(scored: pd.DataFrame) -> pd.DataFrame:
    out = scored.copy()
    out["decile"] = pd.qcut(out["SelectedPurePremium"].rank(method="first"), 10, labels=False) + 1
    return weighted_segment_summary(out, ["decile"]).sort_values("decile")


def scenario_results(scored: pd.DataFrame, scenarios: dict) -> pd.DataFrame:
    rows = []
    avg_pp = np.average(scored["SelectedPurePremium"], weights=scored["Exposure"])
    for name, a in scenarios.items():
        avg_premium = avg_pp * (1 + a["loss_trend"]) * (1 + a["expense_load"]) / a["target_loss_ratio"] * (1 + a["profit_load"])
        rows.append({"scenario": name, "description": a.get("description", ""), "expense_load": a["expense_load"], "target_loss_ratio": a["target_loss_ratio"], "profit_load": a["profit_load"], "loss_trend": a["loss_trend"], "portfolio_selected_pure_premium": avg_pp, "portfolio_technical_premium": avg_premium})
    return pd.DataFrame(rows)


def make_charts(scored: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    area = weighted_segment_summary(scored, ["Area"]).sort_values("Area")
    plt.figure(figsize=(8, 5))
    plt.bar(area["Area"].astype(str), area["selected_pure_premium"])
    plt.title("Selected Pure Premium by Area")
    plt.xlabel("Area (A=rural, F=urban)")
    plt.ylabel("Selected pure premium")
    plt.tight_layout()
    plt.savefig(out_dir / "selected_pure_premium_by_area.png", dpi=160)
    plt.close()

    age = weighted_segment_summary(scored, ["DrivAgeBand"]).sort_values("DrivAgeBand")
    plt.figure(figsize=(9, 5))
    plt.plot(age["DrivAgeBand"].astype(str), age["observed_frequency"], marker="o", label="Observed")
    plt.plot(age["DrivAgeBand"].astype(str), age["predicted_frequency"], marker="o", label="Predicted")
    plt.title("Observed vs Predicted Frequency by Driver Age Band")
    plt.xlabel("Driver age band")
    plt.ylabel("Claim frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "frequency_by_driver_age_band.png", dpi=160)
    plt.close()

    lift = make_lift(scored)
    plt.figure(figsize=(8, 5))
    plt.plot(lift["decile"], lift["observed_pure_premium"], marker="o", label="Observed")
    plt.plot(lift["decile"], lift["selected_pure_premium"], marker="o", label="Predicted")
    plt.title("Pure Premium Lift Chart")
    plt.xlabel("Model decile, low to high predicted risk")
    plt.ylabel("Pure premium")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "pure_premium_lift_chart.png", dpi=160)
    plt.close()


def save_outputs(root: Path, freq: pd.DataFrame, sev: pd.DataFrame, df: pd.DataFrame, models: Dict[str, object], scored: pd.DataFrame, scenarios: dict) -> None:
    processed = root / "data" / "processed"
    outputs = root / "outputs"
    charts = root / "charts"
    model_dir = root / "models"
    for p in [processed, outputs, charts, model_dir]:
        p.mkdir(parents=True, exist_ok=True)

    df.to_csv(processed / "model_points_fremtpl2.csv", index=False)
    scored.to_csv(outputs / "scored_policies.csv", index=False)
    evaluate_models(models).to_csv(outputs / "model_performance.csv", index=False)
    make_qa(freq, sev, df).to_csv(outputs / "qa_report.csv", index=False)
    for variable in ["DrivAgeBand", "VehAgeBand", "BonusMalusBand", "Area", "VehGas", "VehPowerBand", "DensityBand"]:
        rating_factor_table(scored, variable).to_csv(outputs / f"rating_factors_{variable}.csv", index=False)
    weighted_segment_summary(scored, ["DrivAgeBand", "Area", "VehPowerBand"]).to_csv(outputs / "segment_rate_indications.csv", index=False)
    make_lift(scored).to_csv(outputs / "lift_chart_data.csv", index=False)
    scenario_results(scored, scenarios).to_csv(outputs / "scenario_results.csv", index=False)
    summary = {
        "rows_modelled": int(len(scored)),
        "total_exposure": float(scored["Exposure"].sum()),
        "total_claims_recorded": float(scored["ClaimNb"].sum()),
        "total_claim_amount": float(scored["ClaimAmount"].sum()),
        "portfolio_observed_frequency": float(scored["ClaimNb"].sum() / scored["Exposure"].sum()),
        "portfolio_observed_pure_premium": float(scored["ClaimAmount"].sum() / scored["Exposure"].sum()),
        "portfolio_selected_pure_premium": float(np.average(scored["SelectedPurePremium"], weights=scored["Exposure"])),
        "portfolio_technical_premium_base": float(np.average(scored["TechnicalPremium_Base"], weights=scored["Exposure"])),
        "note": "freMTPL2 does not include actual charged premium; technical premium is calculated from modelled pure premium and selected assumptions.",
    }
    (outputs / "portfolio_summary.json").write_text(json.dumps(summary, indent=2))
    make_charts(scored, charts)
    (model_dir / "frequency_poisson_glm_summary.txt").write_text(str(models["freq_model"].summary()))
    (model_dir / "severity_gamma_glm_summary.txt").write_text(str(models["sev_model"].summary()))
    (model_dir / "pure_premium_tweedie_glm_summary.txt").write_text(str(models["tweedie_model"].summary()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", default="100000", help="Number of policies to model for faster run, or 'full'.")
    parser.add_argument("--root", type=Path, default=project_root())
    args = parser.parse_args()

    root = args.root
    sample_size = None if str(args.sample_size).lower() == "full" else int(args.sample_size)
    scenarios = yaml.safe_load((root / "config" / "scenarios.yaml").read_text())
    freq, sev = load_raw(root)
    df = clean_and_join(freq, sev, sample_size)
    print(f"Model rows: {len(df):,}; exposure: {df['Exposure'].sum():,.1f}; claims: {df['ClaimNb'].sum():,.0f}", flush=True)
    models = fit_models(df)
    scored = score_policies(df, models, scenarios)
    save_outputs(root, freq, sev, df, models, scored, scenarios)
    print("Real-data auto pricing model outputs rebuilt successfully.")
    print("Next run: python python/build_excel_tool.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
