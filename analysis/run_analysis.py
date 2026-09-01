#!/usr/bin/env python3
"""
Master Analysis Runner
======================
Orchestrates all analysis steps in sequence
Run with: python3 run_analysis.py
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

NOTEBOOKS_DIR = "notebooks"
REPORTS_DIR = "../reports"

# List of notebooks to run in order
ANALYSIS_STEPS = [
    ("01_data_exploration.py", "Data Exploration & Profiling"),
    ("02_data_forensics.py", "Data Forensics & Quality Issues"),
    ("03_build_golden_dataset.py", "Build Golden Dataset"),
    ("04_statistical_investigation.py", "Statistical Investigation"),
    ("05_recovery_metrics.py", "Recovery Metrics & Validation"),
    ("06_counterfactual_analysis.py", "Counterfactual Analysis"),
    ("07_investment_recommendation.py", "Investment Recommendation"),
    ("08_executive_memo.py", "Executive Memo"),
]

# Create reports directory
Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("DATA ANALYST ASSIGNMENT - COMPLETE ANALYSIS")
print("=" * 100)
print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Execution log
execution_log = {
    "start_time": datetime.now().isoformat(),
    "steps": []
}

# Run each step
for i, (notebook, description) in enumerate(ANALYSIS_STEPS, 1):
    print(f"\n{'='*100}")
    print(f"[{i}/{len(ANALYSIS_STEPS)}] {description}")
    print(f"{'='*100}")
    
    notebook_path = Path(NOTEBOOKS_DIR) / notebook
    
    if not notebook_path.exists():
        print(f"✗ File not found: {notebook_path}")
        execution_log["steps"].append({
            "step": i,
            "notebook": notebook,
            "status": "FAILED",
            "reason": "File not found"
        })
        continue
    
    try:
        # Run notebook as Python script
        result = subprocess.run(
            [sys.executable, str(notebook_path)],
            cwd=NOTEBOOKS_DIR,
            capture_output=False,
            timeout=600  # 10 minute timeout per step
        )
        
        if result.returncode == 0:
            print(f"\n✓ COMPLETED: {description}")
            execution_log["steps"].append({
                "step": i,
                "notebook": notebook,
                "status": "SUCCESS"
            })
        else:
            print(f"\n✗ FAILED: {description}")
            execution_log["steps"].append({
                "step": i,
                "notebook": notebook,
                "status": "FAILED",
                "returncode": result.returncode
            })
    
    except subprocess.TimeoutExpired:
        print(f"\n✗ TIMEOUT: {description}")
        execution_log["steps"].append({
            "step": i,
            "notebook": notebook,
            "status": "TIMEOUT"
        })
    except Exception as e:
        print(f"\n✗ ERROR: {description}")
        print(f"   Exception: {str(e)}")
        execution_log["steps"].append({
            "step": i,
            "notebook": notebook,
            "status": "ERROR",
            "error": str(e)
        })

# Final summary
print("\n" + "=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)

execution_log["end_time"] = datetime.now().isoformat()

successful = sum(1 for s in execution_log["steps"] if s["status"] == "SUCCESS")
total = len(ANALYSIS_STEPS)

print(f"\nCompleted: {successful}/{total} steps")
print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Save execution log
log_path = Path(REPORTS_DIR) / "execution_log.json"
with open(log_path, 'w') as f:
    json.dump(execution_log, f, indent=2, default=str)

print(f"\n✓ Execution log saved to: {log_path}")

# Print output files
print("\n" + "=" * 100)
print("OUTPUT FILES GENERATED")
print("=" * 100)

output_files = list(Path(REPORTS_DIR).glob("*.*"))
if output_files:
    for f in sorted(output_files):
        print(f"  - {f.name}")
else:
    print("  (No output files found)")

print("\n" + "=" * 100)
print("NEXT STEPS")
print("=" * 100)
print("""
1. Review execution_log.json for any errors
2. Check reports/ directory for:
   - monthly_metrics.csv
   - recovery_metrics.csv
   - contact_rate_metrics.csv
   - investment_analysis.json
   - EXECUTIVE_MEMO.txt
   - counterfactual_analysis.csv

3. Review golden dataset in data/golden/:
   - dim_accounts.csv
   - dim_agents.csv
   - dim_campaigns.csv
   - fact_contact_attempts.csv
   - fact_payments.csv
   - fact_dispositions.csv

4. Run individual notebooks for detailed analysis:
   python3 notebooks/01_data_exploration.py
   python3 notebooks/02_data_forensics.py
   etc.

5. Create visualizations:
   python3 create_dashboard.py

6. Submit git repository with all deliverables
""")
