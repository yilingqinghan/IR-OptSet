#!/usr/bin/env python3
"""
generate_class_and_ir.py

Usage:
    python generate_class_and_ir.py \
        --parquet-dir ds \
        --used-csv ds/used_repos_categorized.csv \
        --out-csv file_categories.csv \
        --ir-dir ir_files

This script performs two tasks:
1. Iterates through the Parquet dataset (all .parquet in --parquet-dir) in sorted order,
   reads each row, looks up its `repo_name` in the used_repos_categorized.csv to find its MainCategory,
   and writes a CSV with columns:
       file, category
   where `file` is `<index>.ll` (index starting from 1 in dataset order).
2. Extracts each row's `original_ir` text into a file named `<index>.ll` under --ir-dir.

"""
import argparse
import pandas as pd
from pathlib import Path

def main(parquet_dir: Path, used_csv: Path, out_csv: Path, ir_dir: Path):
    # Load mapping from used repos
    used_df = pd.read_csv(used_csv, dtype=str)
    repo_to_category = dict(zip(used_df['Path'], used_df['MainCategory']))

    # Prepare output directory
    ir_dir.mkdir(parents=True, exist_ok=True)

    # Prepare CSV writer list
    records = []
    idx = 1

    # Iterate over parquet chunks
    for pf in sorted(parquet_dir.glob('*.parquet')):
        df = pd.read_parquet(pf)
        for _, row in df.iterrows():
            file_name = f"{idx}.ll"
            # Lookup category
            repo = row.get('repo_name', '')
            category = repo_to_category.get(repo, 'Unknown')
            # Extract IR
            ir_text = row.get('original_ir', '') or ''
            ir_path = ir_dir / file_name
            try:
                ir_path.write_text(ir_text, encoding='utf-8')
            except Exception as e:
                print(f"[warn] failed to write IR for {file_name}: {e}")
            # Append record
            records.append({'file': file_name, 'category': category})
            idx += 1

    # Write the CSV mapping
    out_df = pd.DataFrame.from_records(records)
    out_df.to_csv(out_csv, index=False)
    print(f"Wrote {len(records)} records to {out_csv}")
    print(f"Generated {idx-1} IR files under {ir_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate file-category CSV and extract original_ir to files.")
    parser.add_argument('--parquet-dir', type=Path, required=True,
                        help='Directory containing .parquet files')
    parser.add_argument('--used-csv', type=Path, required=True,
                        help='CSV mapping repo_name to MainCategory')
    parser.add_argument('--out-csv', type=Path, required=True,
                        help='Output CSV path (columns: file, category)')
    parser.add_argument('--ir-dir', type=Path, required=True,
                        help='Output directory to write individual .ll IR files')
    args = parser.parse_args()
    main(args.parquet_dir, args.used_csv, args.out_csv, args.ir_dir)
