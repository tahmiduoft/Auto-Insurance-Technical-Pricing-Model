# Auto Insurance Technical Pricing Model

### End-to-End Actuarial Pricing Workflow Using Real Motor Insurance Claims Data

## Overview

This project demonstrates an end-to-end actuarial pricing workflow built using the public **freMTPL2** motor insurance dataset. The objective is to estimate technical insurance premiums by combining statistical frequency-severity modeling with modern analytics, reporting, and workflow automation tools.

The project integrates Python, SQL, Excel/VBA, Power BI, and Alteryx into a production-style actuarial pipeline that transforms raw policy and claims data into business-ready pricing insights.

## Project Workflow

Raw Policy & Claim Data
→ Alteryx Data Preparation & QA
→ Model-Point File Creation
→ Python Predictive Modeling (Poisson, Gamma & Tweedie GLMs)
→ Policy-Level Scoring & Technical Premium Estimation
→ Rating Factor Generation
→ Excel/VBA Pricing Calculator
→ Power BI Executive Dashboard

## Technical Stack

* Python
* Pandas
* NumPy
* Statsmodels
* Scikit-learn
* SQL
* Excel
* VBA
* Power BI
* Alteryx
* Git
* Predictive Modeling
* Generalized Linear Models (Poisson, Gamma, Tweedie)

## Modeling Methodology

The project follows a classical actuarial frequency-severity framework.

* Poisson GLM estimates claim frequency.
* Gamma GLM estimates average claim severity.
* Tweedie GLM provides an aggregate pure premium benchmark.
* Predicted pure premium is converted into a technical premium using configurable pricing assumptions including trend, expense load, target loss ratio, and profit margin.

## Features

* Automated data preparation and QA workflow
* Policy-level model-point generation
* Frequency, severity, and pure premium modeling
* Scenario-based technical premium calculation
* Rating factor generation
* Excel/VBA pricing calculator
* Power BI management dashboard
* Alteryx ETL workflow
* AXIS-inspired actuarial model governance

## Key Deliverables

* Cleaned model-point dataset
* Scored policy-level outputs
* Model performance metrics
* Lift chart diagnostics
* Rating factor tables
* Segment-level technical premium indications
* QA and governance reports
* Excel pricing tool
* Interactive Power BI dashboard
* Alteryx workflow

## AXIS-Inspired Governance

Although this project does not use Moody's AXIS directly, it follows an AXIS-inspired governance structure through:

* Model-point files
* Assumption and scenario-control tables
* Reproducible model runs
* QA and validation reports
* Business-facing pricing exhibits

This mirrors the governance principles commonly used in enterprise actuarial modeling environments.

## Repository Contents

* Python modeling pipeline
* SQL scripts
* Excel/VBA pricing tool
* Power BI dashboard
* Alteryx workflow
* Documentation
* Model summaries
* Generated outputs and charts

## Screenshots

### Excel Technical Premium Calculator

Screenshot to be added

### Power BI Executive Dashboard

Screenshot to be added

### Power BI Model Performance

Screenshot to be added

### Power BI Segment Indications

Screenshot to be added

### Alteryx Workflow

Screenshot to be added

## Running the Project

### 1. Clone the repository

### 2. Install Python dependencies

```bash
python3 -m pip install -r requirements.txt
```

On Windows, `python` may be used instead of `python3`.

### 3. Download the freMTPL2 data

```bash
python3 python/download_data.py
```

This downloads the raw policy-level frequency data and claim severity data used by the project.

### 4. Run the SQL data-preparation pipeline

```bash
python3 python/run_sql_pipeline.py
```

This creates the SQL-based model-point, QA, and segment-analysis outputs.

### 5. Run the actuarial pricing models

For a smaller development run:

```bash
python3 python/real_auto_pricing_model.py --sample-size 100000
```

For the full dataset:

```bash
python3 python/real_auto_pricing_model.py --sample-size full
```

The modeling pipeline:

* creates the cleaned model-point dataset;
* fits Poisson, Gamma, and Tweedie GLMs;
* scores policy-level risks;
* generates rating factors;
* evaluates model performance;
* creates lift chart and scenario outputs;
* exports QA, pricing, and governance files.

### 6. Generate the Excel pricing workbook

```bash
python3 python/build_excel_tool.py
```

The generated workbook is saved in:

```text
excel/freMTPL2_Auto_Pricing_Tool.xlsx
```

The macro-enabled version is available as:

```text
excel/freMTPL2_Auto_Pricing_Tool.xlsm
```

### 7. Review the final outputs

Key generated outputs are stored in:

```text
outputs/
charts/
models/
excel/
```

The Power BI dashboard uses the Python-generated files in `outputs/`, while the Excel/VBA calculator uses model-derived rating factors and pricing assumptions.

### 8. Open the Power BI dashboard

Open:

```text
dashboard/freMTPL2_Auto_Pricing_Dashboard.pbix
```

The dashboard presents portfolio KPIs, model performance, technical premium segmentation, lift diagnostics, scenario sensitivity, and QA/governance results.

### 9. Review the Alteryx workflow

Open:

```text
alteryx/freMTPL2_Data_Prep_Workflow.yxmd
```

The Alteryx workflow provides the visual ETL implementation for policy/claims preparation, aggregation, joins, QA checks, and model-point file creation.

Alteryx serves as the primary visual ETL workflow, while companion SQL scripts demonstrate the equivalent database-style joins, aggregations, QA checks, and segment analyses.

## Project Highlights

* Real insurance data
* Production-style actuarial workflow
* End-to-end pricing pipeline
* Business-facing reporting
* Reproducible modeling process
* Modern actuarial analytics stack
