"""DAG 3/4: Intermediate-Schicht mit dbt bauen und testen.

Startet automatisch, sobald qvig_10_staging das Asset QVIG_STAGING
aktualisiert hat. Baut die Intermediate-Views (tag:intermediate) und
testet sie; danach wird das Asset QVIG_INTERMEDIATE gemeldet, was
qvig_30_marts anstoesst.
"""
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from qvig_assets import (
    DBT,
    DBT_PROJECT_DIR,
    DUCKDB_POOL,
    QVIG_INTERMEDIATE,
    QVIG_STAGING,
)

with DAG(
    dag_id="qvig_20_intermediate",
    description="QVIG-Pipeline: dbt Intermediate (Views) bauen und testen",
    schedule=[QVIG_STAGING],
    catchup=False,
    max_active_runs=1,
    tags=["qvig", "dbt", "intermediate"],
):
    run = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=f"{DBT} run --select tag:intermediate",
        cwd=DBT_PROJECT_DIR,
        pool=DUCKDB_POOL,
    )
    test = BashOperator(
        task_id="dbt_test_intermediate",
        bash_command=f"{DBT} test --select tag:intermediate",
        cwd=DBT_PROJECT_DIR,
        pool=DUCKDB_POOL,
        outlets=[QVIG_INTERMEDIATE],
    )
    run >> test
