# National Airfare Price Index Engine (SkyCPI)

An automated, high-frequency macroeconomic data pipeline and index calculation engine engineered for the Ministry of Statistics and Programme Implementation (MoSPI) and the Reserve Bank of India (RBI). 

Developed for **Smart India Hackathon (Problem Statement 26056)**.

## System Overview
Currently, the 'Transport and Communication' sub-group of the Indian Consumer Price Index (CPI) relies on manual, delayed price collection. This architecture replaces manual surveys with a zero-cost, automated data lake that captures real-time airline pricing dynamics across DGCA-mandated trunk routes. 

The system autonomously extracts, sanitizes, and aggregates flight quotes across five advance-purchase windows (T+1, T+7, T+15, T+30, T+45) to calculate a daily median-based, Laspeyres-style inflation index (Base=100).

## Core Architecture
1. **Ingestion Layer (Playwright + GitHub Actions):** Headless automated workers bypass Anti-Bot/WAF systems ethically using rate-limited, asynchronous cron jobs.
2. **Sanitization Layer (Pandas + NumPy):** Applies a macroeconomic price floor (> ₹2,500) to instantly drop promotional web glitches, isolates base fares from airport taxes (UDF/CUTE), and resolves sparse matrix gaps via NSO-approved Forward-Fill Imputation.
3. **Index Computation (Two-Tier Aggregation):** 
   * **Deduplication:** Utilizes Canonical Flight Keys (Carrier + Flight No + Date) to identify cross-OTA duplicates and log the true market-clearing minimum fare.
   * **Outlier Rejection:** Calculates the localized route median (rather than mean) to mathematically neutralize premium-cabin pricing anomalies, ensuring the index represents the true consumer market floor.
4. **Presentation Layer (Streamlit + FastAPI):** Serves lead-time price elasticity curves, sector-wise heatmaps, and a secure JSON API endpoint for direct MoSPI integration.

## Repository Structure
```text
├── .github/workflows/       # CI/CD pipelines and 6-hour cron automation
├── core/
│   ├── cleaner.py           # Data sanitization and imputation logic
│   └── cpi_calculator.py    # Median-based index mathematics and route weighting
├── data/                    # CSV Data Lake (Raw batch quotes and Timeseries aggregates)
├── app.py                   # Streamlit dashboard and data visualization
└── requirements.txt         # Dependency tree
