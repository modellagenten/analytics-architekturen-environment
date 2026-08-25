"""DAG 1/4: Rohschicht laden (Extract/Load).

Laedt die Seed-Dateien in die DuckDB-Rohschicht (raw.*) und meldet
anschliessend das Asset QVIG_RAW als aktualisiert. Dadurch startet die
DAG qvig_10_staging automatisch.

Diese DAG traegt den Zeitplan der Pipeline (@daily); die nachgelagerten
Schichten haengen ausschliesslich an den Assets.
"""
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from qvig_assets import DUCKDB_POOL, PYTHON, QVIG_RAW

with DAG(
    dag_id="qvig_00_raw",
    description="QVIG-Pipeline: Rohschicht in DuckDB laden (Extract/Load)",
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["qvig", "dbt", "raw"],
):
    BashOperator(
        task_id="load_raw",
        bash_command=f"{PYTHON} /work/load_raw.py",
        pool=DUCKDB_POOL,
        outlets=[QVIG_RAW],
    )
