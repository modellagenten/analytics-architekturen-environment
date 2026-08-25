FROM apache/airflow:3.3.1-python3.12

# dbt und die Loader-Abhaengigkeiten laufen in einem EIGENEN venv unter
# /opt/dbt-venv. So kollidieren die dbt-Pins (jinja2, agate, ...) NICHT mit
# den Abhaengigkeiten von Airflow selbst. Die DAGs rufen dbt/python ueber den
# vollen Pfad /opt/dbt-venv/bin/... auf (siehe dags/qvig_assets.py).
COPY requirements.txt /tmp/dbt-requirements.txt
# venv als root anlegen (das Standard-Image laeuft als User "airflow" ohne
# Schreibrecht in /opt). Die Binaries sind anschliessend world-executable.
USER root
RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/dbt-venv/bin/pip install --no-cache-dir -r /tmp/dbt-requirements.txt
USER airflow
