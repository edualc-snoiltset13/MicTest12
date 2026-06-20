"""
CSV Cleaning & Summary Statistics

Reads a CSV, imputes missing values (numeric → median, categorical → mode),
and writes cleaned data and summary statistics alongside the input file.

Usage:
    python csv_clean_summary.py path/to/data.csv [--out-dir OUT_DIR]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Impute NaN: numeric → column median, categorical → column mode."""
    out = df.copy()
    skipped = []
    for col in out.columns:
        series = out[col]
        if series.notna().sum() == 0:
            skipped.append(col)
            continue
        if pd.api.types.is_numeric_dtype(series):
            out[col] = series.fillna(series.median())
        else:
            out[col] = series.fillna(series.mode().iloc[0])
    if skipped:
        print(f"Note: columns all-NaN, left unchanged: {skipped}")
    return out


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Return a single long-form DataFrame with numeric describe + categorical value counts."""
    sections = []

    numeric = df.select_dtypes(include=np.number)
    if not numeric.empty:
        desc = numeric.describe().T.reset_index().rename(columns={"index": "column"})
        desc.insert(0, "section", "numeric_describe")
        sections.append(desc)

    categorical = df.select_dtypes(exclude=np.number)
    if not categorical.empty:
        rows = []
        for col in categorical.columns:
            counts = categorical[col].value_counts(dropna=False)
            for value, count in counts.items():
                rows.append({"section": "categorical_counts",
                             "column": col,
                             "value": value,
                             "count": int(count)})
        if rows:
            sections.append(pd.DataFrame(rows))

    if not sections:
        return pd.DataFrame(columns=["section"])
    return pd.concat(sections, ignore_index=True, sort=False)


def main():
    parser = argparse.ArgumentParser(description="Clean a CSV and emit summary statistics.")
    parser.add_argument("input_csv", type=Path, help="Path to the input CSV file.")
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="Directory for output files (default: input file's directory).")
    args = parser.parse_args()

    in_path = args.input_csv
    out_dir = args.out_dir or in_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = in_path.stem

    df = pd.read_csv(in_path)
    print(f"Loaded {in_path}: {len(df)} rows × {len(df.columns)} cols")

    missing_before = df.isna().sum()
    total_missing = int(missing_before.sum())
    print(f"Missing values before cleaning: {total_missing}")
    if total_missing:
        for col, n in missing_before.items():
            if n:
                print(f"  {col}: {n}")

    cleaned = clean(df)
    missing_after = int(cleaned.isna().sum().sum())
    print(f"Missing values after cleaning:  {missing_after}")

    summary = summarize(cleaned)

    cleaned_path = out_dir / f"{stem}_cleaned.csv"
    summary_path = out_dir / f"{stem}_summary.csv"
    cleaned.to_csv(cleaned_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(f"Wrote cleaned data → {cleaned_path}")
    print(f"Wrote summary     → {summary_path}")


if __name__ == "__main__":
    main()
