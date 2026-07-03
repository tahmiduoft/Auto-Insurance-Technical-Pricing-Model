-- 02_model_point_build.sql
-- Build a policy-level model-point table from raw frequency and severity tables.
-- This mirrors the data-preparation layer used before actuarial GLM modeling.

DROP TABLE IF EXISTS claim_amount_by_policy;
DROP TABLE IF EXISTS model_points_sql;

CREATE TABLE claim_amount_by_policy AS
SELECT
    IDpol,
    COUNT(*) AS ClaimCountFromSev,
    SUM(CASE WHEN ClaimAmount < 0 THEN 0 ELSE ClaimAmount END) AS ClaimAmountRaw,
    SUM(CASE
            WHEN ClaimAmount < 0 THEN 0
            WHEN ClaimAmount > 200000 THEN 200000
            ELSE ClaimAmount
        END) AS ClaimAmountCapped
FROM freMTPL2sev
GROUP BY IDpol;

CREATE TABLE model_points_sql AS
SELECT
    f.IDpol,
    CASE
        WHEN f.Exposure IS NULL OR f.Exposure <= 0 THEN NULL
        WHEN f.Exposure > 1 THEN 1.0
        ELSE f.Exposure
    END AS Exposure,
    CASE
        WHEN f.ClaimNb IS NULL OR f.ClaimNb < 0 THEN 0
        WHEN f.ClaimNb > 4 THEN 4
        ELSE f.ClaimNb
    END AS ClaimNb,
    f.Area,
    f.VehPower,
    f.VehAge,
    f.DrivAge,
    f.BonusMalus,
    f.VehBrand,
    f.VehGas,
    f.Density,
    f.Region,
    COALESCE(c.ClaimCountFromSev, 0) AS ClaimCountFromSev,
    COALESCE(c.ClaimAmountRaw, 0) AS ClaimAmountRaw,
    COALESCE(c.ClaimAmountCapped, 0) AS ClaimAmount,
    CASE
        WHEN f.ClaimNb IS NULL THEN 0
        WHEN CAST(f.ClaimNb AS INTEGER) <> COALESCE(c.ClaimCountFromSev, 0) THEN 1
        ELSE 0
    END AS ClaimNbMismatch,
    CASE
        WHEN COALESCE(c.ClaimAmountCapped, 0) <= 0 AND COALESCE(f.ClaimNb, 0) > 0 THEN 1
        ELSE 0
    END AS ZeroAmountPositiveClaim,
    CASE
        WHEN f.DrivAge BETWEEN 18 AND 24 THEN '18-24'
        WHEN f.DrivAge BETWEEN 25 AND 29 THEN '25-29'
        WHEN f.DrivAge BETWEEN 30 AND 39 THEN '30-39'
        WHEN f.DrivAge BETWEEN 40 AND 49 THEN '40-49'
        WHEN f.DrivAge BETWEEN 50 AND 59 THEN '50-59'
        WHEN f.DrivAge BETWEEN 60 AND 69 THEN '60-69'
        WHEN f.DrivAge >= 70 THEN '70+'
        ELSE 'Unknown'
    END AS DrivAgeBand,
    CASE
        WHEN f.VehAge BETWEEN 0 AND 1 THEN '0-1'
        WHEN f.VehAge BETWEEN 2 AND 5 THEN '2-5'
        WHEN f.VehAge BETWEEN 6 AND 10 THEN '6-10'
        WHEN f.VehAge BETWEEN 11 AND 15 THEN '11-15'
        WHEN f.VehAge BETWEEN 16 AND 30 THEN '16-30'
        WHEN f.VehAge >= 31 THEN '31+'
        ELSE 'Unknown'
    END AS VehAgeBand,
    CASE
        WHEN f.BonusMalus < 50 THEN '<50'
        WHEN f.BonusMalus BETWEEN 50 AND 59 THEN '50-59'
        WHEN f.BonusMalus BETWEEN 60 AND 79 THEN '60-79'
        WHEN f.BonusMalus BETWEEN 80 AND 99 THEN '80-99'
        WHEN f.BonusMalus BETWEEN 100 AND 119 THEN '100-119'
        WHEN f.BonusMalus BETWEEN 120 AND 159 THEN '120-159'
        WHEN f.BonusMalus >= 160 THEN '160+'
        ELSE 'Unknown'
    END AS BonusMalusBand,
    CASE
        WHEN f.VehPower BETWEEN 1 AND 5 THEN '1-5'
        WHEN f.VehPower BETWEEN 6 AND 7 THEN '6-7'
        WHEN f.VehPower BETWEEN 8 AND 9 THEN '8-9'
        WHEN f.VehPower BETWEEN 10 AND 12 THEN '10-12'
        WHEN f.VehPower >= 13 THEN '13+'
        ELSE 'Unknown'
    END AS VehPowerBand,
    CASE
        WHEN f.Density BETWEEN 0 AND 100 THEN '0-100'
        WHEN f.Density BETWEEN 101 AND 500 THEN '101-500'
        WHEN f.Density BETWEEN 501 AND 1500 THEN '501-1500'
        WHEN f.Density BETWEEN 1501 AND 5000 THEN '1501-5000'
        WHEN f.Density > 5000 THEN '5001+'
        ELSE 'Unknown'
    END AS DensityBand,
    CASE WHEN f.Density IS NULL OR f.Density < 0 THEN NULL ELSE LOG(1 + f.Density) END AS LogDensity,
    CASE
        WHEN f.Exposure IS NULL OR f.Exposure <= 0 THEN NULL
        ELSE COALESCE(f.ClaimNb, 0) / f.Exposure
    END AS ObservedFrequency,
    CASE
        WHEN f.Exposure IS NULL OR f.Exposure <= 0 THEN NULL
        ELSE COALESCE(c.ClaimAmountCapped, 0) / f.Exposure
    END AS ObservedPurePremium,
    CASE
        WHEN COALESCE(f.ClaimNb, 0) > 0 THEN COALESCE(c.ClaimAmountCapped, 0) / f.ClaimNb
        ELSE NULL
    END AS AverageClaimSeverity
FROM freMTPL2freq f
LEFT JOIN claim_amount_by_policy c
    ON f.IDpol = c.IDpol
WHERE f.Exposure IS NOT NULL
  AND f.Exposure > 0;
