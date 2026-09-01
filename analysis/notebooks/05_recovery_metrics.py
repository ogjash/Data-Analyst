#Phase 5: Recovery Metrics & Claims Validation


import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

GOLDEN_PATH = "data/golden"
OUTPUT_PATH = "reports"
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

print("RECOVERY METRICS & VALIDATION")

print("\nLoading data...", end=" ")
accounts = pd.read_csv(f"{GOLDEN_PATH}/dim_accounts.csv")
payments = pd.read_csv(f"{GOLDEN_PATH}/fact_payments.csv")
attempts = pd.read_csv(f"{GOLDEN_PATH}/fact_contact_attempts.csv")

payments['payment_date'] = pd.to_datetime(payments['payment_date'])
payments['payment_month'] = payments['payment_date'].dt.to_period('M')
attempts['contact_date'] = pd.to_datetime(attempts['contact_date'])
attempts['contact_month'] = attempts['contact_date'].dt.to_period('M')

print("DONE")


# DEFINE RECOVERY METRICS (Independent Definitions)

print("Calculating recovery metrics...", end=" ")

metrics_results = {
    "timestamp": datetime.now().isoformat(),
    "metrics": {}
}

# Get all months
all_months = sorted(set(list(payments['payment_month'].dropna().unique()) + 
                        list(attempts['contact_month'].dropna().unique())))

# METRIC 1: Contact Rate

print("DONE\n[Contact Rate Analysis]")

contact_metrics = []
for month in all_months:
    month_str = str(month)
    
    # Accounts targeted (from daily_targeting if available)
    targeted = attempts[attempts['contact_month'] == month]['account_id'].nunique()
    
    # Accounts with successful contact (connected calls or successful attempts)
    # Handle both string and numeric attempt_status
    attempts['attempt_status_str'] = attempts['attempt_status'].astype(str).str.lower()
    contacted = attempts[
        (attempts['contact_month'] == month) & 
        ((attempts['attempt_status_str'].str.contains('connected', na=False)) |
         (attempts['attempt_status_str'].str.contains('success', na=False)))
    ]['account_id'].nunique()
    
    contact_rate = (contacted / targeted * 100) if targeted > 0 else 0
    
    contact_metrics.append({
        'month': month_str,
        'accounts_targeted': targeted,
        'accounts_contacted': contacted,
        'contact_rate_pct': round(contact_rate, 2)
    })

contact_df = pd.DataFrame(contact_metrics)
print(contact_df.to_string(index=False))

if len(contact_df) >= 2:
    early = contact_df['contact_rate_pct'].iloc[:len(contact_df)//2].mean()
    late = contact_df['contact_rate_pct'].iloc[len(contact_df)//2:].mean()
    improvement = ((late - early) / early) * 100
    print(f"\n  Contact Rate Improvement: {improvement:+.2f}%")
    metrics_results["metrics"]["contact_rate_improvement"] = round(improvement, 2)


# METRIC 2: PTP Rate (Promise To Pay)

print("\n[Promise To Pay (PTP) Rate Analysis]")

# Assuming disposition codes contain "PTP" for promises to pay
ptp_metrics = []
for month in all_months:
    month_str = str(month)
    
    
    ptp_metrics.append({
        'month': month_str,
        'ptps_made': 0, 
        'accounts_contacted': contact_df[contact_df['month'] == month_str]['accounts_contacted'].values[0] if any(contact_df['month'] == month_str) else 0,
        'ptp_rate_pct': 0.0
    })

ptp_df = pd.DataFrame(ptp_metrics)
print("[Note: Requires disposition code mapping - adjust based on actual codes]")


# METRIC 3: Recovery Rate (The Critical One!)

print("\n[Recovery Rate Analysis - THREE DEFINITIONS]")

recovery_metrics = []

for month in all_months:
    month_str = str(month)
    month_payments = payments[payments['payment_month'] == month]
    
    # Definition 1: Recovery as % of targeted accounts (most conservative)
    targeted = attempts[attempts['contact_month'] == month]['account_id'].nunique()
    recovered = month_payments['account_id'].nunique()
    recovery_rate_targeted = (recovered / targeted * 100) if targeted > 0 else 0
    
    # Definition 2: Recovery as % of contacted accounts (middle ground)
    attempts['attempt_status_str'] = attempts['attempt_status'].astype(str).str.lower()
    contacted = attempts[
        (attempts['contact_month'] == month) & 
        ((attempts['attempt_status_str'].str.contains('connected', na=False)) |
         (attempts['attempt_status_str'].str.contains('success', na=False)))
    ]['account_id'].nunique()
    recovery_rate_contacted = (recovered / contacted * 100) if contacted > 0 else 0
    
    # Definition 3: Recovery amount per account
    recovery_per_account = (month_payments['amount'].sum() / recovered) if recovered > 0 else 0
    
    recovery_metrics.append({
        'month': month_str,
        'recovery_rate_vs_targeted_pct': round(recovery_rate_targeted, 2),
        'recovery_rate_vs_contacted_pct': round(recovery_rate_contacted, 2),
        'recovery_per_account': round(recovery_per_account, 2),
        'total_recovery': int(month_payments['amount'].sum()),
        'accounts_recovered': recovered,
    })

recovery_df = pd.DataFrame(recovery_metrics)
print("\n" + recovery_df.to_string(index=False))

# Calculate improvements
if len(recovery_df) >= 2:
    print("\n[Recovery Improvement Calculation]")
    
    # By Definition 1 (vs Targeted)
    early_def1 = recovery_df['recovery_rate_vs_targeted_pct'].iloc[:len(recovery_df)//2].mean()
    late_def1 = recovery_df['recovery_rate_vs_targeted_pct'].iloc[len(recovery_df)//2:].mean()
    improvement_def1 = ((late_def1 - early_def1) / early_def1) * 100
    
    # By Definition 2 (vs Contacted)
    early_def2 = recovery_df['recovery_rate_vs_contacted_pct'].iloc[:len(recovery_df)//2].mean()
    late_def2 = recovery_df['recovery_rate_vs_contacted_pct'].iloc[len(recovery_df)//2:].mean()
    improvement_def2 = ((late_def2 - early_def2) / early_def2) * 100
    
    # By Definition 3 (per account)
    early_def3 = recovery_df['recovery_per_account'].iloc[:len(recovery_df)//2].mean()
    late_def3 = recovery_df['recovery_per_account'].iloc[len(recovery_df)//2:].mean()
    improvement_def3 = ((late_def3 - early_def3) / early_def3) * 100
    
    print(f"  Definition 1 (vs Targeted Accounts): {improvement_def1:+.2f}%")
    print(f"    Early: {early_def1:.2f}% | Late: {late_def1:.2f}%")
    
    print(f"\n  Definition 2 (vs Contacted Accounts): {improvement_def2:+.2f}%")
    print(f"    Early: {early_def2:.2f}% | Late: {late_def2:.2f}%")
    
    print(f"\n  Definition 3 (Recovery per Account): {improvement_def3:+.2f}%")
    print(f"    Early: ₹{early_def3:.0f} | Late: ₹{late_def3:.0f}")
    
    metrics_results["metrics"]["recovery_improvement_def1"] = round(improvement_def1, 2)
    metrics_results["metrics"]["recovery_improvement_def2"] = round(improvement_def2, 2)
    metrics_results["metrics"]["recovery_improvement_def3"] = round(improvement_def3, 2)


# COMPARISON TO 11% CLAIM

print("VALIDATION OF 11% RECOVERY IMPROVEMENT CLAIM")

if "recovery_improvement_def1" in metrics_results["metrics"]:
    claim = 11.0
    actual_def1 = metrics_results["metrics"]["recovery_improvement_def1"]
    actual_def2 = metrics_results["metrics"]["recovery_improvement_def2"]
    actual_def3 = metrics_results["metrics"]["recovery_improvement_def3"]
    
    print(f"\nReported Claim: {claim}% month-on-month improvement")
    
    print(f"\nActual Results:")
    print(f"Definition 1 (vs Targeted): {actual_def1:+.2f}%")
    print(f"Definition 2 (vs Contacted): {actual_def2:+.2f}%")
    print(f"Definition 3 (Per Account): {actual_def3:+.2f}%")
    
    if abs(actual_def1 - claim) < 1:
        print(f"\nDONE: CLAIM VALIDATED (Definition 1)")
    elif abs(actual_def2 - claim) < 1:
        print(f"\nDONE: CLAIM VALIDATED (Definition 2)")
    elif abs(actual_def3 - claim) < 1:
        print(f"\nDONE: CLAIM VALIDATED (Definition 3)")
    else:
        max_actual = max(actual_def1, actual_def2, actual_def3)
        if max_actual > claim:
            print(f"\nERR: CLAIM UNDERSTATED (Best case: {max_actual:+.2f}%)")
        else:
            print(f"\nERR: CLAIM OVERSTATED (Best case: {max_actual:+.2f}%)")



contact_df.to_csv(f"{OUTPUT_PATH}/contact_rate_metrics.csv", index=False)
recovery_df.to_csv(f"{OUTPUT_PATH}/recovery_metrics.csv", index=False)

with open(f"{OUTPUT_PATH}/metrics_summary.json", 'w') as f:
    json.dump(metrics_results, f, indent=2, default=str)

print(f"DONE: Metrics saved to {OUTPUT_PATH}/")
