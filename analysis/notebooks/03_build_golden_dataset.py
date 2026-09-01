#Phase 3: Build the Golden Dataset

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

DATASET_PATH = "../collections_30k_dataset"
OUTPUT_PATH = "data/golden"
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

cleaning_log = {
    "timestamp": datetime.now().isoformat(),
    "steps": []
}

print("=" * 100)
print("BUILDING GOLDEN DATASET")
print("=" * 100)

print("\n[Step 1] Loading raw data...", end=" ")
raw_data = {}
for csv_file in sorted(Path(DATASET_PATH).glob("*.csv")):
    table_name = csv_file.stem
    raw_data[table_name] = pd.read_csv(csv_file)
print("DONE")

print("[Step 2] Normalizing timestamps...", end=" ")
for table_name, df in raw_data.items():
    for col in df.columns:
        if 'at' in col or col == 'created_at' or col == 'updated_at':
            df[col] = pd.to_datetime(df[col], errors='coerce')
print("DONE")


# CLEAN ACCOUNTS

print("[Step 3] Cleaning accounts...", end=" ")
accounts = raw_data['accounts'].copy()
accounts_before = len(accounts)

accounts = accounts[accounts['account_id'].notna()]

cleaning_log["steps"].append({
    "table": "accounts",
    "action": "remove_null_account_id",
    "before": accounts_before,
    "after": len(accounts),
    "removed": accounts_before - len(accounts)
})

raw_data['accounts'] = accounts
print("DONE")


# CLEAN PAYMENTS 

print("[Step 4] Deduplicating payments...", end=" ")
payments = raw_data['payments'].copy()
payments_before = len(payments)

payments = payments.sort_values('event_at')

# Mark duplicates: same account, same amount, within 60 seconds
payments['time_key'] = payments.groupby(['account_id', 'amount'])['event_at'].transform(
    lambda x: x.astype(np.int64) // 60_000_000_000
)

duplicate_mask = payments.duplicated(subset=['account_id', 'amount', 'time_key'], keep='first')
payments_removed = duplicate_mask.sum()

# Also remove exact duplicates
payments = payments.drop_duplicates(subset=['payment_id', 'account_id', 'amount', 'event_at'], keep='first')

# Remove time_key column
payments = payments.drop('time_key', axis=1)

cleaning_log["steps"].append({
    "table": "payments",
    "action": "deduplicate_by_account_amount_time",
    "before": payments_before,
    "after": len(payments),
    "removed": payments_before - len(payments),
    "impact_amount": float(payments_removed * payments['amount'].mean())
})

raw_data['payments'] = payments
print(f"DONE: (removed {payments_before - len(payments):,} duplicates)")


# CLEAN AGENTS

print("[Step 5] Resolving agent identities...", end=" ")
agents = raw_data['agents'].copy()

# Create canonical agent ID: use employee_code as source of truth
agent_mapping = agents.drop_duplicates(subset=['employee_code'])[
    ['agent_id', 'employee_code', 'agent_name']
].reset_index(drop=True)

# Merge to get canonical ID
agents = agents.merge(agent_mapping, on='employee_code', how='left', suffixes=('_old', ''))
agents = agents[['agent_id', 'employee_code', 'agent_name', 'vendor_id', 'team', 'status', 'joined_at', 'updated_at']]

raw_data['agents'] = agents.drop_duplicates(subset=['agent_id'])
print(f"DONE ({len(agent_mapping)} unique agents)")


# CLEAN CALLS

print("[Step 6] Cleaning calls...", end=" ")
calls = raw_data['calls'].copy()
calls_before = len(calls)

# Remove rows with null agent_id
calls = calls[calls['agent_id'].notna()]

if 'timezone' in calls.columns:
    pass

raw_data['calls'] = calls
print(f"DONE: (removed {calls_before - len(calls):,})")

# CLEAN CALL ATTEMPTS & DISPOSITIONS

print("[Step 7] Organizing call attempts and dispositions...", end=" ")
call_attempts = raw_data['call_attempts'].copy()
call_dispositions = raw_data['call_dispositions'].copy()

valid_call_ids = set(calls['call_id'].unique())
call_attempts = call_attempts[call_attempts['call_id'].isin(valid_call_ids)]
call_dispositions = call_dispositions[call_dispositions['call_id'].isin(valid_call_ids)]

raw_data['call_attempts'] = call_attempts
raw_data['call_dispositions'] = call_dispositions
print("DONE")


# CLEAN CAMPAIGNS

print("[Step 8] Organizing campaigns...", end=" ")
campaigns = raw_data['campaigns'].copy()

# Ensure start_at <= end_at
invalid_campaigns = campaigns[campaigns['start_at'] > campaigns['end_at']]
if len(invalid_campaigns) > 0:
    print(f"\n  Warning: {len(invalid_campaigns)} campaigns with start > end")
    campaigns = campaigns[campaigns['start_at'] <= campaigns['end_at']]

raw_data['campaigns'] = campaigns
print("DONE")


# CREATE FACT TABLES

print("[Step 9] Creating analytical fact tables...", end=" ")

# Fact: Contact Attempts by Day
contact_attempts = call_attempts.merge(
    accounts[['account_id', 'dpd', 'risk_segment']],
    on='account_id',
    how='left'
).copy()

contact_attempts['contact_date'] = contact_attempts['event_at'].dt.date
contact_attempts['contact_hour'] = contact_attempts['event_at'].dt.hour
contact_attempts['contact_dow'] = contact_attempts['event_at'].dt.day_name()

# Fact: Payments by Account by Day
payments_fact = payments.merge(
    accounts[['account_id', 'dpd', 'risk_segment', 'loan_type']],
    on='account_id',
    how='left'
).copy()

payments_fact['payment_date'] = payments_fact['event_at'].dt.date
payments_fact['payment_month'] = payments_fact['event_at'].dt.to_period('M')

# Fact: Disposition by Call
dispositions_fact = call_dispositions.merge(
    calls[['call_id', 'agent_id', 'campaign_id']],
    on='call_id',
    how='left'
).copy()

# Use event_at from call_dispositions instead
if 'event_at' in dispositions_fact.columns:
    dispositions_fact['disposition_date'] = dispositions_fact['event_at'].dt.date

print("DONE")


# SAVE GOLDEN DATASET

print("[Step 10] Saving golden dataset tables...", end=" ")

golden_tables = {
    'dim_accounts': accounts,
    'dim_agents': agents,
    'dim_campaigns': campaigns,
    'fact_contact_attempts': contact_attempts,
    'fact_payments': payments_fact,
    'fact_dispositions': dispositions_fact,
}

for table_name, df in golden_tables.items():
    df.to_csv(f"{OUTPUT_PATH}/{table_name}.csv", index=False)

print("DONE")


# DATA QUALITY SUMMARY

print("DATA QUALITY REPORT")

summary = {
    "total_accounts": len(accounts),
    "total_agents": len(agents),
    "total_payments": len(payments),
    "total_payment_amount": float(payments['amount'].sum()),
    "total_contact_attempts": len(contact_attempts),
    "date_range": {
        "start": str(pd.concat([
            contact_attempts['event_at'],
            payments['event_at'],
            calls['event_at']
        ]).min()),
        "end": str(pd.concat([
            contact_attempts['event_at'],
            payments['event_at'],
            calls['event_at']
        ]).max())
    }
}

print(f"\nFinal Dataset Sizes:")
print(f"Accounts: {summary['total_accounts']:,}")
print(f"Agents: {summary['total_agents']:,}")
print(f"Payments: {summary['total_payments']:,}")
print(f"Total Payment Amount: ₹{summary['total_payment_amount']:,.0f}")
print(f"Contact Attempts: {summary['total_contact_attempts']:,}")
print(f"\nDate Range: {summary['date_range']['start']} to {summary['date_range']['end']}")

cleaning_log["summary"] = summary
with open(f"{OUTPUT_PATH}/cleaning_log.json", 'w') as f:
    json.dump(cleaning_log, f, indent=2, default=str)

print(f"\nDONE: Golden dataset created in {OUTPUT_PATH}/")
print(f"DONE: Cleaning log saved")

