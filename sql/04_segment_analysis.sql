-- 04_segment_analysis.sql
-- Segment-level actuarial summaries for pricing analysis.

DROP VIEW IF EXISTS sql_segment_analysis_by_area_age_power;
DROP VIEW IF EXISTS sql_segment_analysis_by_area;

CREATE VIEW sql_segment_analysis_by_area_age_power AS
SELECT
    DrivAgeBand,
    Area,
    VehPowerBand,
    COUNT(*) AS PolicyCount,
    SUM(Exposure) AS TotalExposure,
    SUM(ClaimNb) AS TotalClaims,
    SUM(ClaimAmount) AS TotalClaimAmount,
    SUM(ClaimNb) / NULLIF(SUM(Exposure), 0) AS ObservedFrequency,
    SUM(ClaimAmount) / NULLIF(SUM(Exposure), 0) AS ObservedPurePremium,
    CASE
        WHEN SUM(ClaimNb) > 0 THEN SUM(ClaimAmount) / SUM(ClaimNb)
        ELSE NULL
    END AS AverageSeverity
FROM model_points_sql
GROUP BY DrivAgeBand, Area, VehPowerBand
ORDER BY TotalExposure DESC;

CREATE VIEW sql_segment_analysis_by_area AS
SELECT
    Area,
    COUNT(*) AS PolicyCount,
    SUM(Exposure) AS TotalExposure,
    SUM(ClaimNb) AS TotalClaims,
    SUM(ClaimAmount) AS TotalClaimAmount,
    SUM(ClaimNb) / NULLIF(SUM(Exposure), 0) AS ObservedFrequency,
    SUM(ClaimAmount) / NULLIF(SUM(Exposure), 0) AS ObservedPurePremium,
    CASE
        WHEN SUM(ClaimNb) > 0 THEN SUM(ClaimAmount) / SUM(ClaimNb)
        ELSE NULL
    END AS AverageSeverity
FROM model_points_sql
GROUP BY Area
ORDER BY ObservedPurePremium DESC;
