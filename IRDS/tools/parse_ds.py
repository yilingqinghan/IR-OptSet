# show_dataset_sample.py
"""Utility to peek at the Hugging Face Parquet dataset created by mkdataset.py.

Example usage:

    python show_dataset_sample.py --parquet-dir hf_parquet --row 10

This will load the first parquet chunk found in the directory, print its
shape, column names, and the specified row so you can confirm the content.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd  # already present
import math


def _truncate(value, length=120):
    s = str(value)
    return s if len(s) <= length else s[:length] + '…'


def show_row(parquet_dir: Path, row_index: int) -> None:
    parquet_files = sorted(parquet_dir.glob("*.parquet"))
    if not parquet_files:
        print(f"[!] No .parquet files found in {parquet_dir}")
        return

    first_file = parquet_files[0]
    print(f"Loading {first_file} …")
    df = pd.read_parquet(first_file)
    total_rows = len(df)
    if row_index < 0 or row_index >= total_rows:
        print(f"[!] Row index {row_index} is out of bounds for dataset with {total_rows} rows.")
        return

    row = df.iloc[row_index]
    print(f"\nColumns: {list(df.columns)}")
    print(f"Total rows in this chunk: {total_rows:,}\n")
    print(f"Row #{row_index}\n" + "-"*40)
    for col, val in row.items():
        print(f"{col:<25}: {_truncate(val)}")

# New function to check for empty fields in all parquet chunks
def check_empty(parquet_dir: Path) -> None:
    """Scan all parquet chunks, count total rows and list rows with empty fields."""
    parquet_files = sorted(parquet_dir.glob("*.parquet"))
    if not parquet_files:
        print(f"[!] No .parquet files found in {parquet_dir}")
        return
    total_rows = 0
    problems = []  # list of tuples (file_name, row_index, repo_name, func_name, missing_columns)
    for pf in parquet_files:
        df = pd.read_parquet(pf)
        n = len(df)
        total_rows += n
        for idx, row in df.iterrows():
            missing = [col for col, val in row.items()
                       if pd.isna(val) or (isinstance(val, str) and val == "")]
            if missing:
                repo_name = row.get("repo_name", "")
                func_name = row.get("function_name", "")
                problems.append((pf.name, idx, repo_name, func_name, missing))
    print(f"Total rows across all chunks: {total_rows}")
    print(f"Rows with missing fields: {len(problems)}")
    for fname, idx, repo_name, func_name, missing in problems:
        identifier = f"{repo_name}/{func_name}"
        print(f"{fname} [row {idx}, id={identifier}]: missing columns -> {missing}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preview a single row from a Parquet dataset chunk.")
    parser.add_argument("--parquet-dir", required=True, type=Path, help="Directory containing .parquet chunks")
    parser.add_argument("--row", type=int, default=0, help="Row index to display")
    parser.add_argument("--check-empty", action="store_true",
                        help="Check for empty fields across all parquet chunks")
    args = parser.parse_args()

    if args.check_empty:
        check_empty(args.parquet_dir)
    else:
        show_row(args.parquet_dir, args.row)

