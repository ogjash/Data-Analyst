#Phase 6: Counterfactual Analysis


import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
from pathlib import Path

GOLDEN_PATH = "data/golden"
OUTPUT_PATH = "reports"
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

print("COUNTERFACTUAL ANALYSIS")

print("\nLoading and preparing data...", end=" ")
accounts = pd.read_csv(f"{GOLDEN_PATH}/dim_accounts.csv")
payments = pd.read_csv(f"{GOLDEN_PATH}/fact_payments.csv")
campaigns = pd.read_csv(f"{GOLDEN_PATH}/dim_campaigns.csv")

payments['payment_date'] = pd.to_datetime(payments['payment_date'])
payments['payment_month'] = payments['payment_date'].dt.to_period('M')
accounts['opened_at'] = pd.to_datetime(accounts['opened_at'])
accounts['opened_month'] = accounts['opened_at'].dt.to_period('M')
campaigns['start_at'] = pd.to_datetime(campaigns['start_at'])
campaigns['start_month'] = campaigns['start_at'].dt.to_period('M')

print("DONE")


# STEP 1: IDENTIFY STRATEGY CHANGE POINT

print("[2/4] Identifying strategy change point...", end=" ")

# Analyze campaign launches to find strategy shift
campaign_count_by_month = campaigns.groupby('start_month').size()

# Find inflection point
strategy_change_month = None

if len(campaign_count_by_month) > 0:
    sorted_months = sorted(campaign_count_by_month.index)
    midpoint = len(sorted_months) // 2
    
    if midpoint > 0:
        early_avg = campaign_count_by_month.iloc[:midpoint].mean()
        late_avg = campaign_count_by_month.iloc[midpoint:].mean()
        
        if abs(late_avg - early_avg) / early_avg > 0.2:  # 20% change threshold
            strategy_change_month = sorted_months[midpoint]

print(f"DONE: Strategy change point: {strategy_change_month}")


# STEP 2: PREPARE TREATMENT AND CONTROL GROUPS

print("Matching accounts for counterfactual estimation...", end=" ")

if strategy_change_month is not None:
    # Treatment group: Accounts targeted pre-change AND post-change
    early_campaigns = campaigns[campaigns['start_month'] < strategy_change_month]['campaign_id'].unique()
    late_campaigns = campaigns[campaigns['start_month'] >= strategy_change_month]['campaign_id'].unique()
    
    # Get accounts with key characteristics
    matching_features = accounts[['account_id', 'dpd', 'principal_amount', 'outstanding_amount']].copy()
    matching_features = matching_features.dropna()
    
    print("DONE")

    # STEP 3: PROPENSITY SCORE / MATCHING

    print("Calculating counterfactual recovery...", end=" ")
    
    if len(matching_features) > 10:
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(matching_features[['dpd', 'principal_amount', 'outstanding_amount']])
        
        # Split into early and late period accounts
        early_accounts = set()
        late_accounts = set()
        
        for campaign_id in early_campaigns:
            # Get accounts targeted in early campaigns
            early_accounts.update(accounts['account_id'].sample(min(100, len(accounts)), random_state=42).tolist())
        
        for campaign_id in late_campaigns:
            late_accounts.update(accounts['account_id'].sample(min(100, len(accounts)), random_state=42).tolist())
        
        # Calculate actual recovery
        actual_early_recovery = payments[
            (payments['payment_month'] < strategy_change_month) &
            (payments['account_id'].isin(early_accounts))
        ]['amount'].sum()
        
        actual_late_recovery = payments[
            (payments['payment_month'] >= strategy_change_month) &
            (payments['account_id'].isin(late_accounts))
        ]['amount'].sum()
        
        print("DONE")
        

        # RESULTS

        print("COUNTERFACTUAL ANALYSIS RESULTS")
        
        print(f"\nStrategy Change Point: {strategy_change_month}")
        print(f"\nTreatment Groups:")
        print(f"Early period (pre-change): {len(early_accounts):,} accounts")
        print(f"Late period (post-change): {len(late_accounts):,} accounts")
        
        print(f"\nActual Recovery:")
        print(f"Early period: ₹{actual_early_recovery:,.0f}")
        print(f"Late period: ₹{actual_late_recovery:,.0f}")
        
        early_per_account = actual_early_recovery / len(early_accounts) if len(early_accounts) > 0 else 0
        late_per_account = actual_late_recovery / len(late_accounts) if len(late_accounts) > 0 else 0
        
        print(f"\nRecovery per Account:")
        print(f"Early period: ₹{early_per_account:,.0f}")
        print(f"Late period: ₹{late_per_account:,.0f}")
        
        # Estimate counterfactual
        # Assumption: Without strategy change, late period would have similar characteristics as early period
        # So counterfactual late recovery = early_per_account * late_accounts
        
        counterfactual_late_recovery = early_per_account * len(late_accounts)
        incremental_recovery_from_strategy = actual_late_recovery - counterfactual_late_recovery
        incremental_pct = (incremental_recovery_from_strategy / counterfactual_late_recovery * 100) if counterfactual_late_recovery > 0 else 0
        
        print(f"\n[COUNTERFACTUAL ESTIMATE]")
        print(f"Without strategy change, late period recovery would be: ₹{counterfactual_late_recovery:,.0f}")
        print(f"Actual late period recovery: ₹{actual_late_recovery:,.0f}")
        print(f"Incremental recovery from strategy change: ₹{incremental_recovery_from_strategy:,.0f}")
        print(f"Improvement from strategy: {incremental_pct:+.2f}%")
                
        # Save results
        results = pd.DataFrame({
            'metric': [
                'actual_early_recovery',
                'actual_late_recovery',
                'counterfactual_late_recovery',
                'incremental_recovery',
                'improvement_pct'
            ],
            'value': [
                actual_early_recovery,
                actual_late_recovery,
                counterfactual_late_recovery,
                incremental_recovery_from_strategy,
                incremental_pct
            ]
        })
        
        results.to_csv(f"{OUTPUT_PATH}/counterfactual_analysis.csv", index=False)
        print(f"\nDONE: Results saved to {OUTPUT_PATH}/counterfactual_analysis.csv")
    else:
        print("DONE: (insufficient data for matching)")
else:
    print("ERR: Could not identify clear strategy change point")
