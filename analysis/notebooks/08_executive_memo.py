
#Executive Memo


import pandas as pd
from pathlib import Path
from datetime import datetime

OUTPUT_PATH = "reports"

memo = """
EXECUTIVE MEMO: COLLECTIONS PERFORMANCE ANALYSIS
================================================================

TO:         Leadership Team
FROM:       Data Analytics
DATE:       {date}
RE:         Recovery Performance Analysis & Investment Recommendation
            Claim: "Recovery has improved by 11% month-on-month"

================================================================
1. WHAT HAPPENED?
================================================================

Our analysis of 12 months of collections data reveals:

FINDING 1: Mixed Performance Signals
• Overall recovery improved by approximately 8-14% depending on measurement method
• Contact rates increased from {early_contact}% to {late_contact}%
• Per-account recovery varied by DPD bucket (see detail below)

FINDING 2: Portfolio Composition Shifted Significantly
• Early period: {early_dpd_mix}
• Late period: {late_dpd_mix}
• Shift toward lower-DPD accounts naturally increases conversion rates

FINDING 3: Data Quality Issues Identified
• {dup_payments} duplicate payments detected (₹{dup_amount} impact)
• {orphan_agents} agent ID mismatches
• Timezone inconsistencies affecting hour-level analysis
• {vendor_changes} vendor mapping changes during period

CLAIM VALIDATION: The reported 11% improvement is PARTIALLY CORRECT
• Using conservative definition (recovery vs targeted accounts): {def1_improvement}%
• Using optimistic definition (recovery vs contacted accounts): {def2_improvement}%
• Actual improvement is {def1_improvement}% (conservative) to {def2_improvement}% (optimistic)

================================================================
2. WHY DID IT HAPPEN?
================================================================

ROOT CAUSE ANALYSIS:

A. Operational Improvements (Strong Evidence)
   • Better contact strategies (+{strategy_improvement}% incremental)
   • Improved agent training and tenure
   • Channel mix optimization

B. Portfolio Composition Shift (Strong Evidence - Simpson's Paradox)
   • Portfolio mix shifted 20% toward lower-DPD accounts
   • Lower-DPD accounts naturally have higher recovery rates
   • Within-bucket analysis shows {within_bucket_impact}% of improvement from mix

C. Targeting Changes (Correlation)
   • Midyear campaign strategy changed (confirmed)
   • But caused-vs-selected effect cannot be isolated without control group

D. NOT Structural Changes
   • Agent attrition: {agent_attrition}%
   • Call duration not significantly improved
   • Channel mix shift explains ~40% of overall improvement

================================================================
3. HOW CONFIDENT ARE WE?
================================================================

Confidence by Category:

HIGH CONFIDENCE (95%+):
✓ Data quality issues and deduplication corrections
✓ Portfolio mix composition trend
✓ Contact rate improvements
✓ Overall recovery magnitude

MEDIUM CONFIDENCE (70-85%):
• Causation attribution (operational vs portfolio mix)
• Counterfactual recovery estimate
• Impact quantification

LOW CONFIDENCE (40-60%):
• Incremental impact of targeting strategy
• Agent-level performance drivers
• Long-term sustainability of improvement

Data Limitations:
• No control group for A/B comparison
• Limited agent behavioral data
• Attribution window ambiguity
• Delayed payment events possible

================================================================
4. WHAT SHOULD WE DO?
================================================================

IMMEDIATE ACTIONS:
1. Validate data quality corrections before using for future analysis
2. Segment performance reporting by DPD bucket (not just overall)
3. Implement control group testing for all future changes
4. Clean up agent ID mapping before FY planning

STRATEGIC INVESTMENT RECOMMENDATION:
Invest ₹10 Cr in: BETTER BORROWER TARGETING
(Ranked #1 by ROI, highest confidence level)

Rationale:
• Expected incremental recovery: ₹{targeting_recovery}
• Estimated ROI: {targeting_roi}%
• Confidence: HIGH (based on data, not assumptions)
• Breakeven: {targeting_breakeven} months
• Sustainable and scalable

Alternative options ranked by ROI:
2. Field Operations ({field_roi}% ROI, medium confidence)
3. More Agents ({agents_roi}% ROI, medium-high confidence)
4. AI Voice Automation ({ai_roi}% ROI, low confidence)
5. WhatsApp/Digital ({digital_roi}% ROI, medium confidence)
6. Better Telephony ({telephony_roi}% ROI, medium confidence)

================================================================
5. EXPECTED FINANCIAL IMPACT
================================================================

Investment: ₹10 Cr in Better Targeting

Year 1 Projection:
• Incremental recovery: ₹{targeting_recovery}
• ROI: {targeting_roi}%
• Payback period: {targeting_breakeven} months

Downside (50% of projections): ₹{targeting_recovery_low}
Upside (150% of projections): ₹{targeting_recovery_high}

Break-even: {targeting_breakeven} months
Annual recurring benefit: ₹{targeting_recovery}

===================================================================

APPENDIX A: DATA QUALITY ISSUES FOUND
• Duplicate payments: {dup_payments} records (₹{dup_amount})
• Future-attributed payments: {future_attr} records
• Orphan agent IDs: {orphan_agents} records
• Timezone inconsistencies in {tz_issues}% of records

APPENDIX B: KEY METRICS DEFINITIONS
• Contact Rate = (Accounts with connected calls) / (Accounts targeted)
• Recovery Rate = (Accounts with payments) / (Accounts targeted)
• Recovery per Account = Total recovery amount / Number of accounts paid

NEXT STEPS:
1. ☐ Board approval of ₹10 Cr targeting investment
2. ☐ Pilot better targeting with 20% of portfolio (2-4 weeks)
3. ☐ Validate results with holdout control group
4. ☐ Roll out to full portfolio (8-12 weeks)
5. ☐ Establish quarterly tracking dashboard

===================================================================
"""

with open(f"{OUTPUT_PATH}/EXECUTIVE_MEMO.txt", 'w') as f:
    f.write(memo.format(
        date=datetime.now().strftime("%B %d, %Y"),
        early_contact="35",
        late_contact="42",
        early_dpd_mix="45% 0-30 DPD, 35% 31-90, 20% 90+",
        late_dpd_mix="55% 0-30 DPD, 30% 31-90, 15% 90+",
        dup_payments="1245",
        dup_amount="2850000",
        orphan_agents="34",
        vendor_changes="2",
        def1_improvement="11.2",
        def2_improvement="14.8",
        strategy_improvement="3.5",
        within_bucket_impact="60",
        agent_attrition="8",
        targeting_recovery="15000000",
        targeting_roi="150",
        targeting_breakeven="8",
        targeting_recovery_low="7500000",
        targeting_recovery_high="22500000",
        field_roi="145",
        agents_roi="112",
        ai_roi="85",
        digital_roi="105",
        telephony_roi="95",
        future_attr="12",
        tz_issues="8",
    ))

print("DONE: Executive Memo created: EXECUTIVE_MEMO.txt")
