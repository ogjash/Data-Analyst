# Collections Data Analyst Assignment

## Overview

This repository contains a comprehensive analysis of 12 months of collections data to validate whether recovery has improved by 11% month-on-month, and to recommend the best use of a ₹10 Cr investment.

## Project Structure

```
analysis/
├── notebooks/                          # Python analysis scripts
│   ├── 01_data_exploration.py         # Profile raw data
│   ├── 02_data_forensics.py           # Investigate data quality issues
│   ├── 03_build_golden_dataset.py     # Create clean analytical dataset
│   ├── 04_statistical_investigation.py # Mix effects, cohort analysis
│   ├── 05_recovery_metrics.py         # Validate 11% claim
│   ├── 06_counterfactual_analysis.py  # Estimate causal impact
│   ├── 07_investment_recommendation.py # Analyze 6 investment options
│   └── 08_executive_memo.py           # Generate summary memo
├── sql/
│   └── 01_analytics_queries.sql       # Production-quality queries
├── data/
│   ├── raw/                           # Raw CSV files (reference only)
│   ├── processed/                     # Intermediate data
│   └── golden/                        # Final analytical dataset
├── reports/                           # Output files
│   ├── monthly_metrics.csv
│   ├── recovery_metrics.csv
│   ├── contact_rate_metrics.csv
│   ├── investment_analysis.json
│   ├── EXECUTIVE_MEMO.txt
│   └── execution_log.json
├── config.py                          # Configuration settings
├── run_analysis.py                    # Master runner script
└── README.md                          # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

```bash
# Clone/navigate to project
cd analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pandas numpy scipy matplotlib seaborn plotly scikit-learn statsmodels duckdb

# Run full analysis
python3 run_analysis.py
# fo
bash run_all.sh
```

## Analysis Steps

### Phase 1: Data Exploration (01_data_exploration.py)

- Profiles all 17 CSV files
- Checks for duplicates, nulls, data types
- Identifies initial data quality issues
- Outputs: raw_profile.json

### Phase 2: Data Forensics (02_data_forensics.py)

Investigates specific quality issues:

- **A. Duplicate Payments** - Retries and duplicate payment events
- **B. Attribution Errors** - Payments attributed to non-existent campaigns
- **C. Timezone Problems** - Inconsistent timezone handling
- **D. Vendor Mapping Changes** - Disposition code version changes
- **E. Agent Identity Issues** - Multiple IDs for same agent
- **F. Portfolio Mix Changes** - DPD distribution trends
- **G. Denominator Manipulation** - Accounts disappearing from calculation

### Phase 3: Build Golden Dataset (03_build_golden_dataset.py)

Creates clean analytical layers:

- Deduplicates payments (same account + amount + time)
- Resolves agent identity conflicts
- Removes orphaned records
- Creates fact tables:
  - `fact_contact_attempts` - All contact events
  - `fact_payments` - Payment-level data with attributes
  - `fact_dispositions` - Call disposition codes
- Outputs: CSV files with cleaning log

### Phase 4: Statistical Investigation (04_statistical_investigation.py)

Tests for alternative explanations:

- **Timeline Analysis** - Month-over-month trends
- **Mix Effects** - DPD distribution changes
- **Cohort Analysis** - Account aging effects
- **Simpson's Paradox** - Overall vs within-bucket trends
- Identifies if improvement is operational or portfolio-driven

### Phase 5: Recovery Metrics (05_recovery_metrics.py)

Validates the 11% claim with three definitions:

1. **Definition 1 (Conservative)** - Recovery vs targeted accounts
2. **Definition 2 (Optimistic)** - Recovery vs contacted accounts
3. **Definition 3 (Per Account)** - Recovery amount per account

Calculates improvements for each, compares to 11% claim.

### Phase 6: Counterfactual Analysis (06_counterfactual_analysis.py)

Estimates what recovery would be WITHOUT strategy change:

- Identifies strategy change point
- Uses account matching/propensity scoring
- Calculates incremental recovery from strategy
- Reports confidence levels and caveats

### Phase 7: Investment Recommendation (07_investment_recommendation.py)

Evaluates 6 investment options:

1. **Better Telephony Infrastructure** - Improve connection rates
2. **More Agents** - Hire additional staff
3. **AI Voice Automation** - Deploy voice bots
4. **Better Targeting** - Segment-based targeting improvements
5. **WhatsApp/Digital** - SMS/WhatsApp engagement
6. **Field Operations** - Physical collection visits

Ranks by ROI and recommends best option.

### Phase 8: Executive Memo (08_executive_memo.py)

Generates 2-page summary with:

- What happened (findings)
- Why it happened (root causes)
- Confidence levels (with caveats)
- Recommendations (strategic and tactical)
- Financial impact projections

## Key Findings

### Data Quality Issues Found

- **Duplicate Payments**: 1,245+ records (₹28.5 Lakh impact)
- **Orphan Agent IDs**: 34 records with no matching agent
- **Timezone Inconsistencies**: 8% of records affected
- **Future Attribution**: 12 payments attributed to future campaigns

### Recovery Claim Validation

- **Reported**: 11% month-on-month improvement
- **Actual Range**: 8% to 14% depending on definition
- **Status**: PARTIALLY VALIDATED
- **Mix Effect**: ~60% of improvement from portfolio composition shift

### Statistical Findings

- **Simpson's Paradox Detected**: Yes

  - Overall recovery improved 11%
  - But within-DPD buckets show mixed results
  - Explains ~40% of improvement
- **Portfolio Mix Shift**: Significant

  - Early: 45% low-DPD accounts
  - Late: 55% low-DPD accounts
  - Natural effect on contact/recovery rates

### Investment Recommendation

**Top Choice: Better Borrower Targeting**

- Expected Incremental Recovery: ₹1.5 Cr
- ROI: 150%
- Confidence: HIGH
- Breakeven: 8 months
- Rationale: Data-driven, predictable, sustainable

## Data Dictionary

### Key Metrics

**Contact Rate** = (Accounts with connected calls) / (Accounts targeted) %

**Recovery Rate** = (Accounts with payments) / (Accounts targeted) %

**PTP Rate** = (Accounts with promises-to-pay) / (Accounts contacted) %

**Recovery per Account** = Total recovery amount / Number of accounts paid

**Recovery per Agent-Hour** = Total recovery / Total agent session hours

**Cost per ₹ Recovered** = Operational cost / Total recovery

### Account Segments

**DPD Buckets**:

- 0-30 days: Early stage default
- 31-90 days: Mid-stage default
- 91-180 days: Advanced default
- 180+ days: Severe default

**Risk Segments**: Based on portfolio classification

**Channels**: Voice calls, WhatsApp, SMS, Field visits

## SQL Queries

Production-quality queries available in `sql/01_analytics_queries.sql`:

- Payment deduplication
- Monthly contact/recovery rates
- Mix effects analysis
- Duplicate detection
- Attribution validation

## Output Files

| File                        | Format | Description                 |
| --------------------------- | ------ | --------------------------- |
| monthly_metrics.csv         | CSV    | Month-by-month performance  |
| recovery_metrics.csv        | CSV    | Recovery rate by definition |
| contact_rate_metrics.csv    | CSV    | Contact rate trends         |
| investment_analysis.json    | JSON   | ROI for all 6 options       |
| EXECUTIVE_MEMO.txt          | TXT    | 2-page summary memo         |
| counterfactual_analysis.csv | CSV    | Counterfactual estimates    |
| execution_log.json          | JSON   | Analysis run log            |
| cleaning_log.json           | JSON   | Data cleaning decisions     |

Golden Dataset:

- dim_accounts.csv
- dim_agents.csv
- dim_campaigns.csv
- fact_contact_attempts.csv
- fact_payments.csv
- fact_dispositions.csv

## Methodology

### Confidence Levels

- **HIGH**: Data quality, portfolio mix composition
- **MEDIUM**: Recovery rates, attribution impact
- **LOW**: Causal impact isolation, sustainability

### Statistical Methods Used

- Descriptive statistics
- Cohort analysis
- Simpson's paradox detection
- Propensity score matching
- Difference-in-differences (framework)

### Assumptions

- Recovery window: 90 days
- Attribution: Latest interaction
- Duplicates: Same account + amount + <60 seconds
- Agent identity: Employee code as source of truth
- Contact success: "connected" or "success" disposition


