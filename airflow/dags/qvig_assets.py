"""Gemeinsame Definitionen fuer die QVIG-Orchestrierung.

Enthaelt die Airflow-3-Assets, die die vier DAGs zu einer data-aware
Pipeline verketten, sowie die Pfade zu den ausfuehrbaren Programmen im
dbt-venv (siehe airflow/Dockerfile).

Datenfluss der Assets:

    qvig_00_raw ----[QVIG_RAW]----> qvig_10_staging
    qvig_10_staging --[QVIG_STAGING]--> qvig_20_intermediate
    qvig_20_intermediate --[QVIG_INTERMEDIATE]--> qvig_30_marts
"""
from airflow.sdk import Asset

# ─── Assets: eine logische Schicht der DuckDB-Pipeline pro Asset ─────────
QVIG_RAW = Asset(name="qvig_raw", uri="duckdb://qvig/raw")
QVIG_STAGING = Asset(name="qvig_staging", uri="duckdb://qvig/staging")
QVIG_INTERMEDIATE = Asset(name="qvig_intermediate", uri="duckdb://qvig/intermediate")
QVIG_MARTS = Asset(name="qvig_marts", uri="duckdb://qvig/marts")

# ─── Pfade im dbt-venv (getrennt von Airflow, siehe Dockerfile) ─────────
DBT = "/opt/dbt-venv/bin/dbt"
PYTHON = "/opt/dbt-venv/bin/python"

# Arbeitsverzeichnis des dbt-Projekts im Container (Bind-Mount aus compose).
DBT_PROJECT_DIR = "/dbt_project"

# Ein einzelner Pool-Slot serialisiert alle Schreibzugriffe auf die
# DuckDB-Datei (Single-Writer). Alle dbt-Tasks belegen diesen Pool.
DUCKDB_POOL = "duckdb_write"
