-- Production-Quality SQL Queries for Collections Analytics
-- ========================================================

-- 1. CLEAN PAYMENTS TABLE
-- Remove duplicates and late-arriving events

CREATE TABLE payments_cleaned AS
SELECT 
    payment_id,
    account_id,
    borrower_id,
    event_at,
    amount,
    payment_type,
    ROW_NUMBER() OVER (PARTITION BY account_id, amount, DATE(event_at) ORDER BY event_at) as rn
FROM payments
WHERE 
    payment_id IS NOT NULL
    AND account_id IS NOT NULL
    AND amount > 0
    AND event_at IS NOT NULL
HAVING ROW_NUMBER() = 1;

-- 2. CLEAN CALLS TABLE
-- Remove orphaned calls, standardize agent IDs

CREATE TABLE calls_cleaned AS
SELECT 
    c.call_id,
    c.account_id,
    c.borrower_id,
    c.event_at,
    COALESCE(a.agent_id, c.agent_id) as agent_id,
    c.campaign_id,
    c.direction,
    c.vendor_id,
    c.call_status,
    c.duration_sec,
    c.timezone
FROM calls c
LEFT JOIN agents a ON c.agent_id = a.agent_id
WHERE 
    c.call_id IS NOT NULL
    AND c.account_id IS NOT NULL
    AND c.event_at IS NOT NULL;

-- 3. DEDUPLICATE AGENTS
-- Create agent dimension with canonical ID

CREATE TABLE dim_agents_clean AS
SELECT 
    employee_code,
    MIN(agent_id) as agent_id,
    agent_name,
    vendor_id,
    team,
    status,
    joined_at,
    updated_at
FROM agents
WHERE agent_id IS NOT NULL
GROUP BY employee_code, agent_name, vendor_id, team, status, joined_at, updated_at;

-- 4. CALCULATE MONTHLY CONTACT RATE

SELECT 
    DATE_TRUNC('month', ca.event_at) as contact_month,
    COUNT(DISTINCT ca.account_id) as accounts_contacted,
    COUNT(*) as total_contact_attempts,
    COUNT(DISTINCT ca.account_id) * 100.0 / 
        (SELECT COUNT(DISTINCT account_id) 
         FROM daily_targeting 
         WHERE DATE_TRUNC('month', target_date) = DATE_TRUNC('month', ca.event_at)) as contact_rate_pct
FROM call_attempts_cleaned ca
WHERE ca.attempt_status IN ('connected', 'success')
GROUP BY DATE_TRUNC('month', ca.event_at)
ORDER BY contact_month;

-- 5. CALCULATE MONTHLY RECOVERY RATE

SELECT 
    DATE_TRUNC('month', p.event_at) as recovery_month,
    COUNT(DISTINCT p.account_id) as accounts_recovered,
    SUM(p.amount) as total_recovery,
    AVG(p.amount) as avg_recovery_per_account,
    COUNT(*) as total_payments
FROM payments_cleaned p
GROUP BY DATE_TRUNC('month', p.event_at)
ORDER BY recovery_month;

-- 6. RECOVERY RATE BY DPD (Mix Effects Analysis)

SELECT 
    DATE_TRUNC('month', p.event_at) as month,
    CASE 
        WHEN a.dpd BETWEEN 0 AND 30 THEN '0-30'
        WHEN a.dpd BETWEEN 31 AND 90 THEN '31-90'
        WHEN a.dpd BETWEEN 91 AND 180 THEN '91-180'
        ELSE '180+'
    END as dpd_bucket,
    COUNT(DISTINCT p.account_id) as accounts_recovered,
    SUM(p.amount) as total_recovery,
    AVG(p.amount) as avg_recovery
FROM payments_cleaned p
JOIN accounts a ON p.account_id = a.account_id
GROUP BY 
    DATE_TRUNC('month', p.event_at),
    dpd_bucket
ORDER BY month, dpd_bucket;

-- 7. RECOVERY BY CHANNEL (Contact method)

SELECT 
    DATE_TRUNC('month', p.event_at) as month,
    COALESCE(ast.recommended_channel, 'Unknown') as channel,
    COUNT(DISTINCT p.account_id) as accounts_recovered,
    SUM(p.amount) as total_recovery,
    COUNT(DISTINCT p.account_id) * 100.0 / 
        (SELECT COUNT(DISTINCT account_id) FROM payments_cleaned 
         WHERE DATE_TRUNC('month', event_at) = DATE_TRUNC('month', p.event_at)) as pct_of_monthly_recovery
FROM payments_cleaned p
LEFT JOIN daily_targeting ast ON p.account_id = ast.account_id 
    AND DATE(p.event_at) = DATE(ast.target_date)
GROUP BY 
    DATE_TRUNC('month', p.event_at),
    channel
ORDER BY month, total_recovery DESC;

-- 8. RECOVERY PER AGENT (Performance Attribution)

SELECT 
    DATE_TRUNC('month', p.event_at) as month,
    a.agent_id,
    a.agent_name,
    COUNT(DISTINCT p.account_id) as accounts_recovered,
    SUM(p.amount) as total_recovery,
    COUNT(*) as payment_events,
    SUM(p.amount) / NULLIF(COUNT(*), 0) as avg_payment_amount
FROM payments_cleaned p
JOIN dim_agents_clean a ON p.account_id IN (
    SELECT account_id FROM calls_cleaned c 
    WHERE c.agent_id = a.agent_id
)
GROUP BY 
    DATE_TRUNC('month', p.event_at),
    a.agent_id,
    a.agent_name
ORDER BY month, total_recovery DESC;

-- 9. DUPLICATE PAYMENT DETECTION

SELECT 
    account_id,
    amount,
    COUNT(*) as duplicate_count,
    SUM(amount) as total_duplicate_amount,
    COUNT(*) - 1 as payments_to_remove
FROM payments
WHERE amount > 0
GROUP BY account_id, amount
HAVING COUNT(*) > 1
ORDER BY total_duplicate_amount DESC;

-- 10. PORTFOLIO MIX ANALYSIS (DPD Distribution Over Time)

SELECT 
    DATE_TRUNC('month', dt.target_date) as month,
    CASE 
        WHEN a.dpd BETWEEN 0 AND 30 THEN '0-30'
        WHEN a.dpd BETWEEN 31 AND 90 THEN '31-90'
        WHEN a.dpd BETWEEN 91 AND 180 THEN '91-180'
        ELSE '180+'
    END as dpd_bucket,
    COUNT(DISTINCT dt.account_id) as accounts_targeted,
    COUNT(DISTINCT dt.account_id) * 100.0 / 
        (SELECT COUNT(DISTINCT account_id) 
         FROM daily_targeting 
         WHERE DATE_TRUNC('month', target_date) = DATE_TRUNC('month', dt.target_date)) as pct_of_monthly
FROM daily_targeting dt
JOIN accounts a ON dt.account_id = a.account_id
GROUP BY 
    DATE_TRUNC('month', dt.target_date),
    dpd_bucket
ORDER BY month, dpd_bucket;

-- 11. DENOMINATOR MANIPULATION CHECK
-- Track if accounts are disappearing from denominator

SELECT 
    DATE_TRUNC('month', target_date) as month,
    COUNT(DISTINCT account_id) as accounts_targeted,
    COUNT(DISTINCT CASE WHEN status = 'active' THEN account_id END) as active_accounts,
    COUNT(DISTINCT CASE WHEN status = 'closed' THEN account_id END) as closed_accounts,
    ROUND(COUNT(DISTINCT CASE WHEN status = 'active' THEN account_id END) * 100.0 / 
        COUNT(DISTINCT account_id), 2) as pct_active
FROM daily_targeting dt
JOIN accounts a ON dt.account_id = a.account_id
GROUP BY DATE_TRUNC('month', target_date)
ORDER BY month;

-- 12. ATTRIBUTION QUALITY CHECK
-- Verify payments attributed to campaigns that existed at time of payment

SELECT 
    p.payment_id,
    p.account_id,
    p.event_at,
    p.campaign_id,
    c.start_at,
    c.end_at,
    CASE 
        WHEN p.event_at < c.start_at THEN 'FUTURE_CAMPAIGN'
        WHEN c.end_at < p.event_at THEN 'PAST_CAMPAIGN'
        ELSE 'VALID'
    END as attribution_status
FROM payments p
JOIN campaigns c ON p.campaign_id = c.campaign_id
WHERE p.campaign_id IS NOT NULL
ORDER BY attribution_status, p.event_at DESC
LIMIT 100;
