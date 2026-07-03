"""
Download real public freMTPL2 motor insurance data.

This script tries two sources:
1) Hugging Face mirror CSV files
2) OpenML via scikit-learn fetch_openml

Expected raw files after success:
- data/raw/freMTPL2freq.csv
- data/raw/freMTPL2sev.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

HF_FREQ_URLS = [
    "https://huggingface.co/datasets/mabilton/fremtpl2/resolve/main/freMTPL2freq.csv?download=true",
    "https://huggingface.co/datasets/mabilton/fremtpl2/resolve/main/freMTPL2freq.csv",
]
HF_SEV_URLS = [
    "https://huggingface.co/datasets/mabilton/fremtpl2/resolve/main/freMTPL2sev.csv?download=true",
    "https://huggingface.co/datasets/mabilton/fremtpl2/resolve/main/freMTPL2sev.csv",
]

OPENML_FREQ_ID = 41214
OPENML_SEV_ID = 41215


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def try_download_csv(urls: list[str], out_path: Path) -> bool:
    for url in urls:
        try:
            print(f"Trying CSV download: {url}")
            df = pd.read_csv(url)
            if len(df) == 0:
                raise ValueError("Downloaded file has zero rows")
            df.to_csv(out_path, index=False)
            print(f"Saved {out_path} with {len(df):,} rows")
            return True
        except Exception as exc:
            print(f"  failed: {exc}")
    return False


def try_openml(data_id: int, out_path: Path) -> bool:
    try:
        print(f"Trying OpenML data_id={data_id}")
        from sklearn.datasets import fetch_openml

        bunch = fetch_openml(data_id=data_id, as_frame=True, parser="auto")
        df = bunch["data"].copy()
        if len(df) == 0:
            raise ValueError("OpenML returned zero rows")
        df.to_csv(out_path, index=False)
        print(f"Saved {out_path} with {len(df):,} rows")
        return True
    except Exception as exc:
        print(f"  OpenML failed: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=project_root() / "data" / "raw")
    args = parser.parse_args()

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    freq_path = args.raw_dir / "freMTPL2freq.csv"
    sev_path = args.raw_dir / "freMTPL2sev.csv"

    freq_ok = freq_path.exists() and freq_path.stat().st_size > 0
    sev_ok = sev_path.exists() and sev_path.stat().st_size > 0

    if not freq_ok:
        freq_ok = try_download_csv(HF_FREQ_URLS, freq_path) or try_openml(OPENML_FREQ_ID, freq_path)
    else:
        print(f"Frequency file already exists: {freq_path}")

    if not sev_ok:
        sev_ok = try_download_csv(HF_SEV_URLS, sev_path) or try_openml(OPENML_SEV_ID, sev_path)
    else:
        print(f"Severity file already exists: {sev_path}")

    if not (freq_ok and sev_ok):
        print("\nCould not download one or both files automatically.")
        print("Manual fallback:")
        print("1. Go to https://huggingface.co/datasets/mabilton/fremtpl2")
        print("2. Download freMTPL2freq.csv and freMTPL2sev.csv")
        print(f"3. Place them in {args.raw_dir}")
        return 1

    print("\nDownload complete. Next run:")
    print("python python/real_auto_pricing_model.py --sample-size 100000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
