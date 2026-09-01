#!/bin/bash
# Complete Analysis Execution Script

cd /home/jashan/Desktop/data_analyst/analysis

echo "========================================================================="
echo "DATA ANALYST ASSIGNMENT"
echo "========================================================================="
echo ""

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    venv/bin/pip install -U pip setuptools wheel pandas numpy scipy matplotlib seaborn plotly scikit-learn statsmodels -q
fi

# Activate venv
source venv/bin/activate 2>/dev/null || . venv/bin/activate

echo ""
echo "========================================================================="
echo "RUNNING ANALYSIS PHASES"
echo "========================================================================="
echo ""

# Run all phases
echo "[1/7] Data Exploration..."
venv/bin/python3 notebooks/01_data_exploration.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo "[2/7] Data Forensics..."
venv/bin/python3 notebooks/02_data_forensics.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo "[3/7] Build Golden Dataset..."
venv/bin/python3 notebooks/03_build_golden_dataset.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo "[4/7] Statistical Investigation..."
venv/bin/python3 notebooks/04_statistical_investigation.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo "[5/7] Recovery Metrics..."
venv/bin/python3 notebooks/05_recovery_metrics.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo "[6/7] Investment Recommendation..."
venv/bin/python3 notebooks/07_investment_recommendation.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo "[7/7] Executive Memo..."
venv/bin/python3 notebooks/08_executive_memo.py > /dev/null 2>&1 && echo "✓ Complete" || echo "✗ Failed"

echo ""
echo "========================================================================="
echo "DELIVERABLES GENERATED"
echo "========================================================================="
echo ""

echo "Golden Dataset (data/golden/):"
ls -lh data/golden/*.csv 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

echo ""
echo "Reports (reports/):"
ls -lh reports/* 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

echo ""
echo "SQL Queries (sql/):"
ls -lh sql/*.sql 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

echo ""
echo "========================================================================="
echo "ANALYSIS COMPLETE"
echo "========================================================================="
echo ""
echo "Next steps:"
echo "1. Review reports/EXECUTIVE_MEMO.txt for summary findings"
echo "2. Check reports/investment_analysis.json for ROI recommendations"
echo "3. Review data/golden/ for clean analytical datasets"
echo "4. Share git repository with all deliverables"
