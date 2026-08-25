"""DAG 2/4: Staging-Schicht mit dbt bauen und testen.

Startet automatisch, sobald qvig_00_raw das Asset QVIG_RAW aktualisiert
hat (schedule=[QVIG_RAW]). Baut die Staging-Views (tag:staging) und testet
sie. Erst wenn die Tests gruen sind, meldet der Test-Task das Asset
QVIG_STAGING - so wird qvig_20_intermediate nur bei sauberen Daten
angestossen.
"""
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from qvig_assets import DBT, DBT_PROJECT_DIR, DUCKDB_POOL, QVIG_RAW, QVIG_STAGING

with DAG(
    dag_id="qvig_10_staging",
    description="QVIG-Pipeline: dbt Staging (Views) bauen und testen",
    schedule=[QVIG_RAW],
    catchup=False,
    max_active_runs=1,
    tags=["qvig", "dbt", "staging"],
):
    run = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"{DBT} run --select tag:staging",
        cwd=DBT_PROJECT_DIR,
        pool=DUCKDB_POOL,
    )
    test = BashOperator(
        task_id="dbt_test_staging",
        bash_command=f"{DBT} test --select tag:staging",
        cwd=DBT_PROJECT_DIR,
        pool=DUCKDB_POOL,
        outlets=[QVIG_STAGING],
    )
    run >> test
