"""Clean a CSV file: normalize columns, drop duplicates, handle missing values, trim outliers."""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import numpy as np


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    def clean(name: str) -> str:
        name = name.strip().lower()
        name = re.sub(r"[^\w]+", "_", name)
        return name.strip("_")

    df.columns = [clean(c) for c in df.columns]
    return df


STRING_LIKE = ["object", "string", "str"]


def strip_string_cells(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=STRING_LIKE).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"": np.nan, "nan": np.nan, "None": np.nan, "NULL": np.nan})
    return df


def coerce_numeric(df: pd.DataFrame, threshold: float = 0.9) -> pd.DataFrame:
    for col in df.select_dtypes(include=STRING_LIKE).columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        non_null = df[col].notna().sum()
        if non_null and coerced.notna().sum() / non_null >= threshold:
            df[col] = coerced
    return df


def fill_missing(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    if strategy == "drop":
        return df.dropna()
    if strategy == "zero":
        return df.fillna(0)
    if strategy == "median":
        for col in df.select_dtypes(include="number").columns:
            df[col] = df[col].fillna(df[col].median())
        for col in df.select_dtypes(exclude="number").columns:
            mode = df[col].mode()
            if not mode.empty:
                df[col] = df[col].fillna(mode.iloc[0])
        return df
    if strategy == "none":
        return df
    raise ValueError(f"unknown missing strategy: {strategy}")


def remove_outliers(df: pd.DataFrame, z: float) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    if numeric.empty or z <= 0:
        return df
    mask = pd.Series(True, index=df.index)
    for col in numeric.columns:
        std = numeric[col].std()
        if std == 0 or pd.isna(std):
            continue
        scores = (numeric[col] - numeric[col].mean()).abs() / std
        mask &= scores.fillna(0) <= z
    return df[mask]


def clean(
    df: pd.DataFrame,
    missing: str = "median",
    outlier_z: float = 0.0,
    drop_duplicates: bool = True,
) -> pd.DataFrame:
    df = normalize_column_names(df)
    df = strip_string_cells(df)
    df = coerce_numeric(df)
    if drop_duplicates:
        df = df.drop_duplicates()
    df = fill_missing(df, missing)
    df = remove_outliers(df, outlier_z)
    return df.reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input CSV path")
    parser.add_argument("output", type=Path, help="output CSV path")
    parser.add_argument(
        "--missing",
        choices=["median", "zero", "drop", "none"],
        default="median",
        help="how to fill missing values (default: median)",
    )
    parser.add_argument(
        "--outlier-z",
        type=float,
        default=0.0,
        help="drop rows where any numeric column exceeds this z-score (0 disables)",
    )
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="do not drop duplicate rows",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    before = len(df)
    df = clean(
        df,
        missing=args.missing,
        outlier_z=args.outlier_z,
        drop_duplicates=not args.keep_duplicates,
    )
    df.to_csv(args.output, index=False)
    print(f"cleaned {before} -> {len(df)} rows, {len(df.columns)} cols -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
