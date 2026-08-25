"""DAG 4/4: Marts-Schicht bauen, testen und nach MySQL veroeffentlichen.

Startet automatisch, sobald qvig_20_intermediate das Asset
QVIG_INTERMEDIATE aktualisiert hat. Baut die Marts (tag:marts, Tabellen),
testet sie und schiebt sie anschliessend mit publish_marts.py in die
MySQL-Serving-DB (qvig_mart) fuer Metabase.
"""
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from qvig_assets import (
    DBT,
    DBT_PROJECT_DIR,
    DUCKDB_POOL,
    PYTHON,
    QVIG_INTERMEDIATE,
    QVIG_MARTS,
)

with DAG(
    dag_id="qvig_30_marts",
    description="QVIG-Pipeline: dbt Marts bauen, testen und nach MySQL publishen",
    schedule=[QVIG_INTERMEDIATE],
    catchup=False,
    max_active_runs=1,
    tags=["qvig", "dbt", "marts"],
):
    run = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"{DBT} run --select tag:marts",
        cwd=DBT_PROJECT_DIR,
        pool=DUCKDB_POOL,
    )
    test = BashOperator(
        task_id="dbt_test_marts",
        bash_command=f"{DBT} test --select tag:marts",
        cwd=DBT_PROJECT_DIR,
        pool=DUCKDB_POOL,
        outlets=[QVIG_MARTS],
    )
    publish = BashOperator(
        task_id="publish_marts",
        bash_command=f"{PYTHON} /work/publish_marts.py",
        pool=DUCKDB_POOL,
    )
    run >> test >> publish
