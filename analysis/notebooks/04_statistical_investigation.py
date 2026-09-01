#Phase 4: Statistical Investigation


import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

GOLDEN_PATH = "data/golden"
OUTPUT_PATH = "reports"
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

print("STATISTICAL INVESTIGATION")

print("\nLoading golden dataset...", end=" ")
accounts = pd.read_csv(f"{GOLDEN_PATH}/dim_accounts.csv")
payments = pd.read_csv(f"{GOLDEN_PATH}/fact_payments.csv")
attempts = pd.read_csv(f"{GOLDEN_PATH}/fact_contact_attempts.csv")
campaigns = pd.read_csv(f"{GOLDEN_PATH}/dim_campaigns.csv")

for col in ['payment_date', 'payment_month']:
    if col in payments.columns:
        if col != 'payment_month':
            payments[col] = pd.to_datetime(payments[col], errors='coerce')

for col in ['contact_date']:
    if col in attempts.columns:
        attempts[col] = pd.to_datetime(attempts[col], errors='coerce')

print("DONE")


# 1. TIMELINE ANALYSIS

print("Building monthly performance metrics...", end=" ")

monthly_metrics = []

# Get unique months from payment data
if 'payment_month' in payments.columns:
    months = sorted(payments['payment_month'].dropna().unique())
elif 'payment_date' in payments.columns:
    payments['payment_month'] = payments['payment_date'].dt.to_period('M')
    months = sorted(payments['payment_month'].dropna().unique())
else:
    months = []

# Calculate metrics for each month
for month in months:
    month_payments = payments[payments['payment_month'] == month]
    
    metric = {
        'month': str(month),
        'total_payments': len(month_payments),
        'total_recovery': month_payments['amount'].sum(),
        'avg_recovery_per_payment': month_payments['amount'].mean(),
        'unique_accounts_paid': month_payments['account_id'].nunique(),
    }
    monthly_metrics.append(metric)

monthly_df = pd.DataFrame(monthly_metrics)
print("DONE")

print("\n[Monthly Performance Trend]")
print(monthly_df.to_string(index=False))

# Identify inflection point
if len(monthly_df) > 0:
    recovery_trend = monthly_df['total_recovery'].values
    midpoint = len(recovery_trend) // 2
    
    early_recovery = recovery_trend[:midpoint].mean()
    late_recovery = recovery_trend[midpoint:].mean()
    improvement_pct = ((late_recovery - early_recovery) / early_recovery) * 100
    
    print(f"\n[Recovery Improvement]")
    print(f"  Early Period (avg): ₹{early_recovery:,.0f}")
    print(f"  Late Period (avg): ₹{late_recovery:,.0f}")
    print(f"  Improvement: {improvement_pct:+.2f}%")


# 2. MIX EFFECTS ANALYSIS

print("\nTesting for mix effects (DPD)...", end=" ")

accounts['dpd_bucket'] = pd.cut(accounts['dpd'], 
                                bins=[0, 30, 90, 180, np.inf],
                                labels=['0-30', '31-90', '91-180', '180+'])

payment_analysis = payments.merge(
    accounts[['account_id', 'dpd', 'dpd_bucket', 'risk_segment']],
    on='account_id',
    how='left'
)

# Compare early vs late period
if 'payment_date' in payment_analysis.columns:
    payment_analysis['period'] = pd.cut(
        payment_analysis['payment_date'],
        bins=2,
        labels=['Early', 'Late']
    )
    
    mix_analysis = payment_analysis.groupby(['period', 'dpd_bucket']).agg({
        'amount': ['count', 'sum', 'mean'],
        'account_id': 'nunique'
    }).round(2)
    
    print("✓")
    print("\n[Recovery by DPD & Period]")
    print(mix_analysis)
    
    # Test if mix changed significantly
    early_mix = payment_analysis[payment_analysis['period'] == 'Early']['dpd_bucket'].value_counts(normalize=True)
    late_mix = payment_analysis[payment_analysis['period'] == 'Late']['dpd_bucket'].value_counts(normalize=True)
    
    if len(early_mix) > 0 and len(late_mix) > 0:
        chi2, p_value = stats.chisquare(
            [late_mix.get(x, 0) for x in early_mix.index],
            [early_mix.get(x, 0) for x in early_mix.index]
        )
        print(f"\n[Mix Shift Test (Chi-square)]")
        print(f"  Chi-square stat: {chi2:.4f}")
        print(f"  P-value: {p_value:.4f}")
        if p_value < 0.05:
            print(f"  ✓ Significant mix shift detected (p < 0.05)")
        else:
            print(f"  ✗ No significant mix shift detected")


# 3. COHORT ANALYSIS

print("\nPerforming cohort analysis...", end=" ")

# Create cohorts based on account opening date
if 'opened_at' in accounts.columns:
    accounts['cohort_month'] = pd.to_datetime(accounts['opened_at']).dt.to_period('M')
    
    # Track each cohort's payment behavior over time
    cohort_data = []
    
    for cohort in sorted(accounts['cohort_month'].dropna().unique()):
        cohort_accounts = accounts[accounts['cohort_month'] == cohort]['account_id'].unique()
        cohort_payments = payments[payments['account_id'].isin(cohort_accounts)].copy()
        
        if len(cohort_payments) > 0:
            cohort_payments['cohort_month'] = cohort
            cohort_data.append(cohort_payments)
    
    if cohort_data:
        cohorts_df = pd.concat(cohort_data, ignore_index=True)
        
        cohort_summary = cohorts_df.groupby('cohort_month').agg({
            'amount': 'sum',
            'account_id': 'nunique'
        }).round(2)
        
        print("DONE")
        print("\n[Cohort Payment Performance]")
        print(cohort_summary.tail(10))
else:
    print("DONE: (opened_at not available)")


# 4. SIMPSON'S PARADOX CHECK

print("\nChecking for Simpson's Paradox...", end=" ")

# Calculate overall recovery improvement
if 'payment_date' in payment_analysis.columns and len(payment_analysis) > 0:
    early_period = payment_analysis[payment_analysis['period'] == 'Early']
    late_period = payment_analysis[payment_analysis['period'] == 'Late']
    
    print("✓")
    
    print("\n[Simpson's Paradox Analysis]")
    print(f"\nOverall Recovery:")
    print(f"  Early Period: ₹{early_period['amount'].sum():,.0f} ({len(early_period):,} payments)")
    print(f"  Late Period: ₹{late_period['amount'].sum():,.0f} ({len(late_period):,} payments)")
    
    early_avg = early_period['amount'].mean()
    late_avg = late_period['amount'].mean()
    overall_improvement = ((late_avg - early_avg) / early_avg) * 100
    
    print(f"  Improvement: {overall_improvement:+.2f}%")
    
    # Check within each DPD bucket
    print(f"\nRecovery within Each DPD Bucket:")
    within_bucket_improvements = []
    
    for bucket in ['0-30', '31-90', '91-180', '180+']:
        early_bucket = early_period[early_period['dpd_bucket'] == bucket]
        late_bucket = late_period[late_period['dpd_bucket'] == bucket]
        
        if len(early_bucket) > 0 and len(late_bucket) > 0:
            early_avg_bucket = early_bucket['amount'].mean()
            late_avg_bucket = late_bucket['amount'].mean()
            bucket_improvement = ((late_avg_bucket - early_avg_bucket) / early_avg_bucket) * 100
            
            within_bucket_improvements.append({
                'dpd_bucket': bucket,
                'early_avg': early_avg_bucket,
                'late_avg': late_avg_bucket,
                'improvement_pct': bucket_improvement
            })
            
            print(f"  {bucket}: {bucket_improvement:+.2f}% (₹{early_avg_bucket:.0f} → ₹{late_avg_bucket:.0f})")
    
    # Check for paradox
    if within_bucket_improvements:
        all_negative = all(x['improvement_pct'] < 0 for x in within_bucket_improvements)
        all_positive = all(x['improvement_pct'] > 0 for x in within_bucket_improvements)
        
        if overall_improvement > 0 and (all_negative or all_positive is False):
            print(f"\nSIMPSON'S PARADOX DETECTED!")
            print(f"     Overall improvement {overall_improvement:+.2f}% but within buckets: mixed")
        elif overall_improvement > 0 and all_negative:
            print(f"\nSIMPSON'S PARADOX DETECTED!")
            print(f"Overall improvement {overall_improvement:+.2f}% but ALL buckets declining!")
            print(f"This suggests portfolio composition shift, not operational improvement.")


# SAVE RESULTS

print("STATISTICAL INVESTIGATION COMPLETE")

# Save monthly metrics
monthly_df.to_csv(f"{OUTPUT_PATH}/monthly_metrics.csv", index=False)

print(f"\nDONE: Results saved to {OUTPUT_PATH}/")
