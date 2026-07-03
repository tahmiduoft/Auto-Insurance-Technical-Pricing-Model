-- 03_qa_checks.sql
-- QA and governance checks for raw and model-point data.

DROP VIEW IF EXISTS sql_qa_checks;

CREATE VIEW sql_qa_checks AS
SELECT 'frequency_rows_raw' AS check_name, COUNT(*) AS check_value, 'info' AS status FROM freMTPL2freq
UNION ALL
SELECT 'severity_rows_raw', COUNT(*), 'info' FROM freMTPL2sev
UNION ALL
SELECT 'model_rows_after_sql_cleaning', COUNT(*), 'info' FROM model_points_sql
UNION ALL
SELECT 'duplicate_policy_ids_in_freq', COUNT(*) - COUNT(DISTINCT IDpol), 'warn' FROM freMTPL2freq
UNION ALL
SELECT 'claims_without_policy_record', COUNT(*), 'warn'
FROM freMTPL2sev s
LEFT JOIN freMTPL2freq f
    ON s.IDpol = f.IDpol
WHERE f.IDpol IS NULL
UNION ALL
SELECT 'nonpositive_or_missing_exposure_raw', COUNT(*), 'fail'
FROM freMTPL2freq
WHERE Exposure IS NULL OR Exposure <= 0
UNION ALL
SELECT 'claimnb_mismatch_policy_rows', SUM(ClaimNbMismatch), 'warn' FROM model_points_sql
UNION ALL
SELECT 'zero_claim_amount_positive_claim_count', SUM(ZeroAmountPositiveClaim), 'warn' FROM model_points_sql
UNION ALL
SELECT 'claim_amounts_above_200k_raw', COUNT(*), 'warn' FROM freMTPL2sev WHERE ClaimAmount > 200000
UNION ALL
SELECT 'negative_claim_amounts_raw', COUNT(*), 'warn' FROM freMTPL2sev WHERE ClaimAmount < 0;
