#Phase 7: Investment Recommendation


import pandas as pd
import json

GOLDEN_PATH = "data/golden"
OUTPUT_PATH = "reports"

print("INVESTMENT RECOMMENDATION ANALYSIS")

payments = pd.read_csv(f"{GOLDEN_PATH}/fact_payments.csv")
accounts = pd.read_csv(f"{GOLDEN_PATH}/dim_accounts.csv")

total_recovery_12m = payments['amount'].sum()
num_accounts = len(accounts)
avg_recovery_per_account = total_recovery_12m / num_accounts

print(f"\nBaseline Metrics:")
print(f"  Total Recovery (12-month): ₹{total_recovery_12m:,.0f}")
print(f"  Accounts: {num_accounts:,}")
print(f"  Avg Recovery/Account: ₹{avg_recovery_per_account:,.0f}")

analysis = {}


# OPTION 1: BETTER TELEPHONY INFRASTRUCTURE (₹1 Cr)

print("INVESTMENT ANALYSIS")

print("\n1. Better Telephony Infrastructure (₹1 Cr)")
inv1 = 1_00_00_00_000
# Assumption: 8% improvement in connection rate/recovery
incr1 = total_recovery_12m * 0.08
analysis['telephony'] = {
    'investment': inv1,
    'recovery_improvement': incr1,
    'roi_pct': (incr1 / inv1) * 100,
    'assumption': '8% recovery uplift from infrastructure'
}
print(f"Incremental Recovery: ₹{incr1:,.0f}/year")
print(f"ROI: {analysis['telephony']['roi_pct']:.1f}%")


# OPTION 2: MORE COLLECTION AGENTS (₹10 Cr)

print("\n2. More Collection Agents (₹10 Cr)")
inv2 = 10_00_00_00_000
# Assume ₹5L/agent, get 2000 agents at 70% productivity of existing
num_new_agents = inv2 // 50_00_000  # 2000 agents
# Existing ~1100 agents recovery ~₹1884M annually = ₹1.7M per agent
recovery_per_agent = total_recovery_12m / 1100
incr2 = num_new_agents * recovery_per_agent * 0.70
analysis['agents'] = {
    'investment': inv2,
    'recovery_improvement': incr2,
    'roi_pct': (incr2 / inv2) * 100,
    'assumption': '2000 agents at 70% productivity'
}
print(f"Incremental Recovery: ₹{incr2:,.0f}/year")
print(f"ROI: {analysis['agents']['roi_pct']:.1f}%")


# OPTION 3: AI VOICE AUTOMATION (₹10 Cr)

print("\n3. AI Voice Automation (₹10 Cr)")
inv3 = 10_00_00_00_000
# Conservative: Can automate 30% of calls at 12% success (vs 8% human)
# But recovery per success only 60% of human
# Incremental = 30% * 0.12 / 0.08 * 0.60 = 27% improvement max
incr3 = total_recovery_12m * 0.12  # Very conservative
analysis['ai'] = {
    'investment': inv3,
    'recovery_improvement': incr3,
    'roi_pct': (incr3 / inv3) * 100,
    'assumption': '12% recovery uplift from automation'
}
print(f"Incremental Recovery: ₹{incr3:,.0f}/year")
print(f"ROI: {analysis['ai']['roi_pct']:.1f}%")


# OPTION 4: BETTER BORROWER TARGETING (₹10 Cr)

print("\n4. Better Borrower Targeting (₹10 Cr)")
inv4 = 10_00_00_00_000
# ML-based segmentation can improve contact rate and recovery by 15-20%
# Conservative: 15% improvement
incr4 = total_recovery_12m * 0.15
analysis['targeting'] = {
    'investment': inv4,
    'recovery_improvement': incr4,
    'roi_pct': (incr4 / inv4) * 100,
    'assumption': '15% recovery uplift from ML targeting'
}
print(f"Incremental Recovery: ₹{incr4:,.0f}/year")
print(f"ROI: {analysis['targeting']['roi_pct']:.1f}%")


# OPTION 5: WHATSAPP/DIGITAL ENGAGEMENT (₹10 Cr)

print("\n5. WhatsApp/Digital Engagement (₹10 Cr)")
inv5 = 10_00_00_00_000
# Lower cost per touch (~₹1.50 vs ₹50 voice), but lower conversion (5% vs 8%)
# Can reach 6.7x more borrowers but with lower success
# Net incremental: ~8% improvement
incr5 = total_recovery_12m * 0.08
analysis['digital'] = {
    'investment': inv5,
    'recovery_improvement': incr5,
    'roi_pct': (incr5 / inv5) * 100,
    'assumption': '8% recovery uplift from digital channels'
}
print(f"Incremental Recovery: ₹{incr5:,.0f}/year")
print(f"ROI: {analysis['digital']['roi_pct']:.1f}%")


# OPTION 6: FIELD OPERATIONS (₹10 Cr)

print("\n6. Field Operations (₹10 Cr)")
inv6 = 10_00_00_00_000
# High touch at ~₹500/visit, 35% success rate
# 20M visits possible, each worth ₹1200 recovery
# But capacity-constrained - can only do 200k visits/year realistically
# Incremental recovery: 200k * 0.35 * 3k = ₹210M (11% of total)
incr6 = total_recovery_12m * 0.11
analysis['field'] = {
    'investment': inv6,
    'recovery_improvement': incr6,
    'roi_pct': (incr6 / inv6) * 100,
    'assumption': '11% recovery uplift from field visits'
}
print(f"  Incremental Recovery: ₹{incr6:,.0f}/year")
print(f"  ROI: {analysis['field']['roi_pct']:.1f}%")


# RANKING AND RECOMMENDATION

print("RANKING (by ROI)")

ranked = sorted(analysis.items(), key=lambda x: x[1]['roi_pct'], reverse=True)
for i, (name, details) in enumerate(ranked, 1):
    inv = details['investment'] / 10_00_00_00_000
    print(f"{i}. {name.upper():<30} ROI: {details['roi_pct']:>6.1f}%  Recovery: ₹{details['recovery_improvement']:>13,.0f}  Invest: ₹{inv:.1f}Cr")

# Optimal allocation
print("\n" + "=" * 100)
print("RECOMMENDED ALLOCATION: ₹10 Cr")
print("=" * 100)

# Multi-option approach
recommendations = [
    ('targeting', 5_00_00_00_000, 'Primary - highest ROI, data-driven'),
    ('agents', 2_50_00_00_000, 'Secondary - proven scalability'),
    ('telephony', 1_50_00_00_000, 'Tertiary - infrastructure'),
    ('digital', 1_00_00_00_000, 'Experimental - low cost, learn-and-grow')
]

total_allocated = 0
total_incremental = 0

print("\nProposed Split:")
for strategy, amount, rationale in recommendations:
    details = analysis[strategy]
    incremental = details['recovery_improvement'] * (amount / details['investment'])
    total_allocated += amount
    total_incremental += incremental
    roi = (incremental / amount) * 100
    print(f"\n  {strategy.upper()}")
    print(f"Allocation: ₹{amount/10_00_00_00_000:.2f} Cr")
    print(f"Expected Recovery: ₹{incremental:,.0f}/year")
    print(f"ROI: {roi:.1f}%")
    print(f"Rationale: {rationale}")

print(f"\n" + "-" * 100)
print(f"Total Allocation: ₹{total_allocated/10_00_00_00_000:.2f} Cr")
print(f"Total Expected Recovery: ₹{total_incremental:,.0f}/year")
print(f"Blended ROI: {(total_incremental/total_allocated)*100:.1f}%")
print(f"Payback Period: {total_allocated/total_incremental*12:.0f} months")

with open(f"{OUTPUT_PATH}/investment_analysis.json", 'w') as f:
    json.dump({
        'baseline': {
            'total_recovery_12m': float(total_recovery_12m),
            'accounts': num_accounts,
            'avg_per_account': float(avg_recovery_per_account)
        },
        'options': analysis,
        'recommendation': {
            'allocation': {opt: float(amt) for opt, amt, _ in recommendations},
            'total_expected_recovery': float(total_incremental),
            'blended_roi_pct': float((total_incremental/total_allocated)*100),
            'payback_months': float(total_allocated/total_incremental*12)
        }
    }, f, indent=2)

print(f"\nDONE: Analysis saved to {OUTPUT_PATH}/investment_analysis.json")
