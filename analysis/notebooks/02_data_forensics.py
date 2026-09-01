#Phase 2: Data Forensics & Quality Issues

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

DATASET_PATH = "../collections_30k_dataset"

print("=" * 100)
print("DATA FORENSICS ANALYSIS")
print("=" * 100)

print("\nLoading data...", end=" ")
payments = pd.read_csv(f"{DATASET_PATH}/payments.csv")
calls = pd.read_csv(f"{DATASET_PATH}/calls.csv")
call_attempts = pd.read_csv(f"{DATASET_PATH}/call_attempts.csv")
agents = pd.read_csv(f"{DATASET_PATH}/agents.csv")
campaigns = pd.read_csv(f"{DATASET_PATH}/campaigns.csv")
accounts = pd.read_csv(f"{DATASET_PATH}/accounts.csv")
daily_targeting = pd.read_csv(f"{DATASET_PATH}/daily_targeting.csv")
call_dispositions = pd.read_csv(f"{DATASET_PATH}/call_dispositions.csv")
print("DONE")

# Convert timestamp columns
timestamp_cols_map = [
    (payments, ['event_at']),
    (calls, ['event_at']),
    (call_attempts, ['event_at']),
    (agents, ['joined_at', 'updated_at']),
    (campaigns, ['start_at', 'end_at']),
    (accounts, ['opened_at']),
    (daily_targeting, ['target_date']),
    (call_dispositions, ['event_at'])
]

for df, cols in timestamp_cols_map:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')


# A. DUPLICATE PAYMENTS

print("A. DUPLICATE PAYMENTS ANALYSIS")

print(f"\nTotal payment records: {len(payments):,}")
print(f"Unique payment IDs: {payments['payment_id'].nunique():,}")
print(f"Duplicate payment IDs: {len(payments) - payments['payment_id'].nunique():,}")

# Check for exact duplicates
exact_dupes = payments.duplicated(subset=['payment_id', 'account_id', 'amount'], keep=False)
print(f"\nExact duplicates (same ID, account, amount): {exact_dupes.sum():,}")

# Check for near-duplicates (same amount, same account, within 1 minute)
payments_sorted = payments.sort_values(['account_id', 'amount', 'event_at'])
payments_sorted['time_diff'] = payments_sorted.groupby(['account_id', 'amount'])['event_at'].diff()
near_dupes = payments_sorted[payments_sorted['time_diff'] <= timedelta(minutes=1)]
print(f"Near-duplicates (same acct/amount, <1min apart): {len(near_dupes):,}")

if len(near_dupes) > 0:
    print(f"\n  Sample near-duplicates:")
    print(near_dupes[['payment_id', 'account_id', 'amount', 'event_at']].head(10).to_string())
    
    # Impact calculation
    duplicate_recovery = near_dupes['amount'].sum()
    total_recovery = payments['amount'].sum()
    print(f"\n  Recovery amount from duplicates: ₹{duplicate_recovery:,.0f}")
    print(f"  Total recovery: ₹{total_recovery:,.0f}")
    print(f"  % of total: {(duplicate_recovery/total_recovery)*100:.2f}%")


# B. ATTRIBUTION ERRORS

print("B. ATTRIBUTION ERRORS")

# Check if payments are being attributed to campaigns that don't exist yet
payment_campaign_issues = 0
for idx, row in payments.iterrows():
    if pd.notna(row.get('campaign_id')):
        campaign_filter = campaigns[campaigns['campaign_id'] == row['campaign_id']]
        if len(campaign_filter) > 0:
            campaign_start = campaign_filter['start_at'].iloc[0]
            if pd.notna(campaign_start) and row['event_at'] < campaign_start:
                payment_campaign_issues += 1

print(f"Payments attributed to future campaigns: {payment_campaign_issues:,}")

# Check for multiple campaigns targeting same account on same day
if 'campaign_id' in daily_targeting.columns:
    multi_campaign_days = daily_targeting.groupby(['account_id', 'target_date'])['campaign_id'].nunique()
    print(f"Account-days with multiple campaigns: {(multi_campaign_days > 1).sum():,}")
    print(f"  Max campaigns per account-day: {multi_campaign_days.max()}")


# C. TIMEZONE PROBLEMS

print("C. TIMEZONE ANALYSIS")

if 'timezone' in calls.columns:
    print(f"\nUnique timezones in calls: {calls['timezone'].nunique()}")
    print(calls['timezone'].value_counts().to_string())

if 'timezone' in accounts.columns:
    print(f"\nUnique timezones in accounts: {accounts['timezone'].nunique()}")
    print(accounts['timezone'].value_counts().head(10).to_string())

# Check for hour level anomalies that might indicate timezone issues
if 'event_at' in calls.columns:
    calls['hour'] = calls['event_at'].dt.hour
    calls['hour_utc'] = calls['event_at'].dt.hour
    
    print(f"\nCall distribution by hour (sample):")
    hour_dist = calls['hour'].value_counts().sort_index()
    print(hour_dist.to_string())
    
    outlier_hours = hour_dist[hour_dist < hour_dist.mean() * 0.1].index
    if len(outlier_hours) > 0:
        print(f"\n  WARNING: Unusual call concentration in hours: {list(outlier_hours)}")


# D. VENDOR MAPPING CHANGES

print("D. VENDOR & DISPOSITION CODE CHANGES")

if 'disposition_version' in call_dispositions.columns:
    print(f"\nDisposition versions found: {call_dispositions['disposition_version'].nunique()}")
    print(call_dispositions['disposition_version'].value_counts().sort_index().to_string())
    
    # Check if disposition codes differ by version
    for version in call_dispositions['disposition_version'].unique():
        if pd.notna(version):
            codes = call_dispositions[call_dispositions['disposition_version'] == version]['disposition_code'].unique()
            print(f"\n  Version {version}: {len(codes)} unique codes")
            print(f"    Examples: {list(codes[:5])}")

if 'vendor_id' in calls.columns:
    calls_by_date = calls.copy()
    calls_by_date['date'] = calls_by_date['event_at'].dt.date
    
    vendor_trend = calls_by_date.groupby('date')['vendor_id'].nunique()
    print(f"\nVendors active by date:")
    print(f"  Min vendors per day: {vendor_trend.min()}")
    print(f"  Max vendors per day: {vendor_trend.max()}")
    print(f"  Avg vendors per day: {vendor_trend.mean():.1f}")


# E. AGENT IDENTITY PROBLEMS

print("E. AGENT IDENTITY ISSUES")

print(f"\nTotal agent IDs: {agents['agent_id'].nunique()}")
print(f"Total employee codes: {agents['employee_code'].nunique()}")

# Check for multiple agent_ids per employee_code
agent_mapping = agents.groupby('employee_code')['agent_id'].nunique()
multi_id_agents = agent_mapping[agent_mapping > 1]
print(f"\nEmployee codes with multiple agent_ids: {len(multi_id_agents)}")
if len(multi_id_agents) > 0:
    print(f"  Examples:")
    for emp_code in multi_id_agents.head(3).index:
        agent_ids = agents[agents['employee_code'] == emp_code]['agent_id'].unique()
        print(f"    {emp_code}: {list(agent_ids)}")

# Check for orphan agent_ids in calls
calls_agent_ids = set(calls['agent_id'].dropna().unique())
agents_agent_ids = set(agents['agent_id'].dropna().unique())
orphan_agents = calls_agent_ids - agents_agent_ids
print(f"\nAgent IDs in calls but not in agents table: {len(orphan_agents)}")


# F. PORTFOLIO MIX CHANGES

print("F. PORTFOLIO MIX ANALYSIS")

# DPD distribution over time
if 'dpd' in accounts.columns:
    print(f"\nDPD Statistics:")
    print(f"  Min: {accounts['dpd'].min()}")
    print(f"  Max: {accounts['dpd'].max()}")
    print(f"  Mean: {accounts['dpd'].mean():.1f}")
    print(f"  Median: {accounts['dpd'].median():.1f}")
    
    # DPD buckets
    accounts['dpd_bucket'] = pd.cut(accounts['dpd'], 
                                    bins=[0, 30, 90, 180, np.inf],
                                    labels=['0-30', '31-90', '91-180', '180+'])
    print(f"\nDPD Distribution:")
    print(accounts['dpd_bucket'].value_counts().sort_index().to_string())

# Risk segment distribution
if 'risk_segment' in accounts.columns:
    print(f"\nRisk Segment Distribution:")
    print(accounts['risk_segment'].value_counts().to_string())

# Account status distribution
if 'status' in accounts.columns:
    print(f"\nAccount Status Distribution:")
    print(accounts['status'].value_counts().to_string())


# G. DENOMINATOR MANIPULATION

print("G. DENOMINATOR MANIPULATION CHECK")

# Check if accounts are disappearing
daily_targeting_accounts = daily_targeting.groupby('target_date')['account_id'].nunique()
print(f"\nAccounts targeted by date:")
print(f"  Min: {daily_targeting_accounts.min():,}")
print(f"  Max: {daily_targeting_accounts.max():,}")
print(f"  Mean: {daily_targeting_accounts.mean():.0f}")

if len(daily_targeting_accounts) > 30:
    early_period = daily_targeting_accounts.iloc[:len(daily_targeting_accounts)//2].mean()
    late_period = daily_targeting_accounts.iloc[len(daily_targeting_accounts)//2:].mean()
    change_pct = ((late_period - early_period) / early_period) * 100
    print(f"\nTrend from early to late period: {change_pct:+.1f}%")
    if abs(change_pct) > 10:
        print(f"WARNING: Significant change in denominator!")

# Check if contacted accounts exist
if 'event_at' in call_attempts.columns:
    contacted_accounts = call_attempts['account_id'].nunique()
    targeted_accounts = daily_targeting['account_id'].nunique()
    contacted_pct = (contacted_accounts / targeted_accounts) * 100
    print(f"\nAccounts contacted: {contacted_accounts:,} / {targeted_accounts:,} ({contacted_pct:.1f}%)")

print("DONE: FORENSICS ANALYSIS COMPLETE")
