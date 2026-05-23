"""Clean a tabular data file: normalize columns, drop duplicates, fill missing, trim outliers."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

STRING_DTYPES = ["object", "string", "str"]
NULL_TOKENS = {"", "nan", "none", "null", "n/a", "na", "-"}


@dataclass
class Report:
    rows_in: int = 0
    rows_out: int = 0
    duplicates_dropped: int = 0
    outliers_dropped: int = 0
    missing_filled: int = 0
    columns_renamed: dict[str, str] = field(default_factory=dict)
    columns_coerced: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"rows {self.rows_in} -> {self.rows_out} "
            f"(duplicates: {self.duplicates_dropped}, "
            f"outliers: {self.outliers_dropped}, "
            f"missing filled: {self.missing_filled}, "
            f"coerced: {len(self.columns_coerced)})"
        )


def _slug(name: str) -> str:
    return re.sub(r"[^\w]+", "_", name.strip().lower()).strip("_")


def _normalize_columns(df: pd.DataFrame, report: Report) -> pd.DataFrame:
    renamed = {c: _slug(c) for c in df.columns if c != _slug(c)}
    report.columns_renamed = renamed
    return df.rename(columns={c: _slug(c) for c in df.columns})


def _normalize_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=STRING_DTYPES).columns:
        s = df[col].astype("string").str.strip()
        df[col] = s.where(~s.str.lower().isin(NULL_TOKENS), pd.NA)
    return df


def _coerce_numeric(df: pd.DataFrame, report: Report, threshold: float = 0.9) -> pd.DataFrame:
    for col in df.select_dtypes(include=STRING_DTYPES).columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        non_null = df[col].notna().sum()
        if non_null and coerced.notna().sum() / non_null >= threshold:
            df[col] = coerced
            report.columns_coerced.append(col)
    return df


def _fill_missing(df: pd.DataFrame, strategy: str, report: Report) -> pd.DataFrame:
    if strategy == "none":
        return df
    if strategy == "drop":
        before = len(df)
        df = df.dropna()
        report.missing_filled = 0
        return df

    missing_before = int(df.isna().sum().sum())
    if strategy == "zero":
        df = df.fillna(0)
    elif strategy == "median":
        for col in df.select_dtypes(include="number").columns:
            df[col] = df[col].fillna(df[col].median())
        for col in df.select_dtypes(exclude="number").columns:
            mode = df[col].mode(dropna=True)
            if not mode.empty:
                df[col] = df[col].fillna(mode.iloc[0])
    else:
        raise ValueError(f"unknown missing strategy: {strategy}")

    report.missing_filled = missing_before - int(df.isna().sum().sum())
    return df


def _drop_outliers(df: pd.DataFrame, z: float, report: Report) -> pd.DataFrame:
    if z <= 0:
        return df
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return df
    mask = pd.Series(True, index=df.index)
    for col in numeric.columns:
        std = numeric[col].std()
        if not std or pd.isna(std):
            continue
        scores = (numeric[col] - numeric[col].mean()).abs() / std
        mask &= scores.fillna(0) <= z
    report.outliers_dropped = int((~mask).sum())
    return df[mask]


def clean(
    df: pd.DataFrame,
    *,
    missing: str = "median",
    outlier_z: float = 0.0,
    drop_duplicates: bool = True,
) -> tuple[pd.DataFrame, Report]:
    report = Report(rows_in=len(df))
    df = _normalize_columns(df, report)
    df = _normalize_strings(df)
    df = _coerce_numeric(df, report)

    if drop_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        report.duplicates_dropped = before - len(df)

    df = _fill_missing(df, missing, report)
    df = _drop_outliers(df, outlier_z, report)

    df = df.reset_index(drop=True)
    report.rows_out = len(df)
    return df, report


READERS = {
    ".csv": pd.read_csv,
    ".tsv": lambda p: pd.read_csv(p, sep="\t"),
    ".json": pd.read_json,
    ".parquet": pd.read_parquet,
}

WRITERS = {
    ".csv": lambda df, p: df.to_csv(p, index=False),
    ".tsv": lambda df, p: df.to_csv(p, sep="\t", index=False),
    ".json": lambda df, p: df.to_json(p, orient="records", indent=2),
    ".parquet": lambda df, p: df.to_parquet(p, index=False),
}


def _read(path: Path) -> pd.DataFrame:
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise ValueError(f"unsupported input format: {path.suffix}")
    return reader(path)


def _write(df: pd.DataFrame, path: Path) -> None:
    writer = WRITERS.get(path.suffix.lower())
    if writer is None:
        raise ValueError(f"unsupported output format: {path.suffix}")
    writer(df, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input file (csv, tsv, json, parquet)")
    parser.add_argument("output", type=Path, help="output file (csv, tsv, json, parquet)")
    parser.add_argument(
        "--missing",
        choices=["median", "zero", "drop", "none"],
        default="median",
        help="strategy for missing values (default: median)",
    )
    parser.add_argument(
        "--outlier-z",
        type=float,
        default=0.0,
        metavar="Z",
        help="drop rows where any numeric column exceeds this z-score (0 disables)",
    )
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="do not drop duplicate rows",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the summary report",
    )
    args = parser.parse_args(argv)

    df = _read(args.input)
    cleaned, report = clean(
        df,
        missing=args.missing,
        outlier_z=args.outlier_z,
        drop_duplicates=not args.keep_duplicates,
    )
    _write(cleaned, args.output)
    if not args.quiet:
        print(report.summary(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
