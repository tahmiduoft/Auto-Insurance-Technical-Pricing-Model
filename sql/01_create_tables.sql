-- 01_create_tables.sql
-- Raw freMTPL2 table definitions.
-- These definitions are SQLite-compatible and can be adapted to PostgreSQL, SQL Server, or Snowflake.

DROP TABLE IF EXISTS freMTPL2freq;
DROP TABLE IF EXISTS freMTPL2sev;

CREATE TABLE freMTPL2freq (
    IDpol INTEGER,
    ClaimNb REAL,
    Exposure REAL,
    Area TEXT,
    VehPower INTEGER,
    VehAge INTEGER,
    DrivAge INTEGER,
    BonusMalus INTEGER,
    VehBrand TEXT,
    VehGas TEXT,
    Density REAL,
    Region TEXT
);

CREATE TABLE freMTPL2sev (
    IDpol INTEGER,
    ClaimAmount REAL
);
