# Phase 1: Data Exploration & Profiling

import pandas as pd
import numpy as np
import os
from pathlib import Path
from collections import Counter
import json

DATASET_PATH = "../collections_30k_dataset"
OUTPUT_PATH = "data/raw_profile.json"

csv_files = list(Path(DATASET_PATH).glob("*.csv"))
print(f"Found {len(csv_files)} CSV files\n")

profile = {}

for csv_file in sorted(csv_files):
    file_name = csv_file.stem
    print(f"Profiling {file_name}...", end=" ")
    
    try:
        df = pd.read_csv(csv_file)
        
        profile[file_name] = {
            "shape": df.shape,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": df.memory_usage(deep=True).sum() / 1024**2,
            "columns_info": {},
            "duplicates": {
                "total_rows": len(df),
                "unique_rows": len(df.drop_duplicates()),
                "duplicate_rows": len(df) - len(df.drop_duplicates()),
            }
        }
        
        # Column level profiling
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "nulls": int(df[col].isnull().sum()),
                "null_pct": float(df[col].isnull().sum() / len(df) * 100),
                "unique": int(df[col].nunique()),
            }
            
            # stat for numeric column
            if df[col].dtype in ['int64', 'float64']:
                col_info["min"] = float(df[col].min()) if df[col].notna().any() else None
                col_info["max"] = float(df[col].max()) if df[col].notna().any() else None
                col_info["mean"] = float(df[col].mean()) if df[col].notna().any() else None
            
            if df[col].dtype == 'object' and df[col].nunique() <= 20:
                col_info["top_values"] = df[col].value_counts().head(5).to_dict()
            
            profile[file_name]["columns_info"][col] = col_info
        
        print(f"✓ ({df.shape[0]:,} rows, {df.shape[1]} cols)")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        profile[file_name] = {"error": str(e)}

with open(OUTPUT_PATH, 'w') as f:
    json.dump(profile, f, indent=2, default=str)

print(f"\DONE: Profile saved to {OUTPUT_PATH}")

# Summary
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total_rows = sum(p.get("rows", 0) for p in profile.values())
total_duplicates = sum(p.get("duplicates", {}).get("duplicate_rows", 0) for p in profile.values())
total_nulls = 0

for table, data in profile.items():
    if "columns_info" in data:
        for col, info in data["columns_info"].items():
            total_nulls += info.get("nulls", 0)

print(f"Total rows across all tables: {total_rows:,}")
print(f"Total duplicate rows found: {total_duplicates:,}")
print(f"Total null values across all columns: {total_nulls:,}")
print(f"\nTables with most duplicates:")

dup_table = [(name, p.get("duplicates", {}).get("duplicate_rows", 0)) 
             for name, p in profile.items()]
for name, dups in sorted(dup_table, key=lambda x: x[1], reverse=True)[:5]:
    if dups > 0:
        print(f"  - {name}: {dups:,} duplicate rows")

