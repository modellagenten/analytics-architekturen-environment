# Schulungsumgebung - Analytics-Architekturen (QVIG, lokal)

Lokale Teilnehmenden-Umgebung fuer das 3-Tage-Training. Alles laeuft
**on-premise in Docker** auf den Windows-VMs - keine Cloud-Accounts.

Roter Faden: das fiktive **QVIG** ("Qualitaetsinstitut fuer Versorgung im
Gesundheitswesen"), QS-Verfahren **Hueftendoprothetik**. Alle Daten sind
synthetisch und reproduzierbar (Seed=42).

## Der lokale Stack

| Komponente | Rolle | Uebung |
|---|---|---|
| **Datengenerator** (Python) | erzeugt synthetische QVIG-Rohdaten | Grundlage |
| **MySQL 8** | operatives Quellsystem (`qvig_op`) + Serving-DB (`qvig_mart`) | 3, 5 |
| **DuckDB + dbt Core** | analytische Engine (Spaltenspeicher), Transformation | 3, 4, 2b |
| **MinIO + Lakekeeper + Trino** | OSS-Lakehouse (Iceberg): Storage, Catalog, Compute | 6 |
| **Metabase** | Self-Service BI (MySQL `qvig_mart`) | 5 |
| **Python-Werkbank** | Loader, Data Science (scikit-learn) | 4, 7 |
| **Apache Airflow 3** | Orchestrierung der dbt-Pipeline (getrennte DAGs pro Schicht) | 4 |

## Verzeichnislayout

```
analytics-architekturen-environment/
├── docker-compose.yml
├── datengenerator/
│   └── generate.py            <- erzeugt seed-data/ (reproduzierbar)
├── seed-data/                 <- generierte QVIG-Rohdaten (CSV/JSON/XML/Parquet)
├── mysql/init/                <- legt qvig_op + qvig_mart an
├── dbt_project/               <- dbt Core (Adapter duckdb)
│   ├── dbt_project.yml, profiles.yml
│   ├── macros/                <- hashkey/hashdiff (Data Vault)
│   ├── models/staging|intermediate|marts|data_vault/
│   └── snapshots/             <- SCD2-Beispiel
├── scripts/                   <- Loader (-> /work im Container)
│   ├── load_raw.py            <- Seeds -> DuckDB raw.*
│   ├── load_mysql.py          <- Seeds -> MySQL qvig_op
│   ├── publish_marts.py       <- DuckDB-Marts -> MySQL qvig_mart
│   ├── load_lake.py           <- Seeds -> Iceberg Bronze (Lakehouse)
│   └── ds_indikator.py        <- Data-Science-Mini (Uebung 7)
├── warehouse/                 <- DuckDB-Datei (wird lokal erzeugt)
├── trino/etc/                 <- Trino-Konfiguration (Iceberg + MySQL)
└── airflow/                   <- Orchestrierung (Profil "airflow")
    ├── Dockerfile             <- Airflow 3.3.1 + dbt-venv
    ├── requirements.txt       <- dbt-duckdb & Loader-Pakete (eigenes venv)
    └── dags/                  <- qvig_00_raw -> _10_staging -> _20_intermediate -> _30_marts
```

## Schnellstart

```bash
# 1) Stack starten (ohne Werkbank; die laeuft on demand im Profil "tools")
docker compose up -d

# 2) Werkbank-Image bauen (beim ersten Mal, ~3-5 Min.)
docker compose build workbench

# 3) Rohdaten erzeugen (optional - die Seeds sind bereits im Repo enthalten)
docker compose run --rm workbench python /datengenerator/generate.py

# 4) Rohschicht in DuckDB laden und dbt bauen
docker compose run --rm workbench python /work/load_raw.py
docker compose run --rm workbench dbt build
```

`dbt build` legt in `warehouse/qvig.duckdb` die Schichten
`raw -> staging -> intermediate -> marts` an (plus Data Vault und Snapshot).

### Endpoints

| Dienst | URL | Zugang |
|---|---|---|
| MinIO Console | http://localhost:9001 | `qvig` / `qvigqvig` |
| Lakekeeper UI | http://localhost:8181 | - |
| Trino UI | http://localhost:8080 | User: `admin` |
| Metabase | http://localhost:3000 | (bei Erststart einrichten) |
| MySQL | localhost:3306 | `qvig` / `qvig` (DBs `qvig_op`, `qvig_mart`) |
| Airflow UI | http://localhost:8081 | kein Login (nur bei `--profile airflow`) |

## Uebungsbezug

| Uebung | Was passiert |
|---|---|
| **3 - Staging & Column Store** | `load_mysql.py` fuellt MySQL (Zeilenspeicher); dieselben Daten in DuckDB (Spaltenspeicher) - Query-Vergleich |
| **4 - ELT mit dbt Core** | `load_raw.py` + `dbt build`: Staging-Modelle mit Tests, Lineage, Docs |
| **2b - Data Vault** | Modelle unter `models/data_vault/` (Hubs/Link/Satellite, Insert-Only) |
| **5 - Metabase** | `publish_marts.py` schiebt Marts nach `qvig_mart`; Metabase -> MySQL |
| **6 - Lakehouse** | `load_lake.py` -> Iceberg Bronze; Silver/Gold in Trino (DBeaver) |
| **7 - Data Science** | `ds_indikator.py`: reproduzierbarer Indikator + einfaches Modell |

## dbt-Kommandos (Cheatsheet)

```bash
docker compose run --rm workbench dbt build          # alles bauen + testen
docker compose run --rm workbench dbt run             # nur Modelle
docker compose run --rm workbench dbt test            # nur Tests
docker compose run --rm workbench dbt snapshot        # SCD2-Snapshot
docker compose run --rm workbench dbt docs generate   # Doku/Lineage
```

## Orchestrierung mit Airflow (optional, Uebung 4)

Statt `dbt build` manuell aufzurufen, orchestriert **Apache Airflow 3.3.1** die
Pipeline schichtweise. Jede dbt-Schicht ist eine eigene DAG; die DAGs haengen
ueber **Airflow-3-Assets** (data-aware scheduling) zusammen:

```
qvig_00_raw  --[qvig_raw]-->  qvig_10_staging  --[qvig_staging]-->
qvig_20_intermediate  --[qvig_intermediate]-->  qvig_30_marts
```

Sobald ein Test-Task einer Schicht erfolgreich ist, meldet er sein Asset als
aktualisiert - und die naechste DAG startet automatisch.

```bash
# 1) Airflow-Stack zusaetzlich starten (baut beim ersten Mal das Image)
docker compose --profile airflow up -d --build

# 2) UI oeffnen: http://localhost:8081  (kein Login noetig)

# 3) Die vier DAGs (qvig_*) einschalten (Toggle) und qvig_00_raw manuell
#    triggern. Die restliche Kette laeuft ueber die Assets von selbst.
```

Alternativ per CLI:

```bash
docker compose exec airflow-scheduler airflow dags trigger qvig_00_raw
```

> **Wichtig - DuckDB ist Single-Writer:** Solange eine DAG laeuft, darf **nicht**
> parallel `docker compose run --rm workbench dbt ...` ausgefuehrt werden -
> beide wuerden gleichzeitig in `warehouse/qvig.duckdb` schreiben und sich mit
> einem Lock-Fehler blockieren. Airflow serialisiert die Schreibzugriffe ueber
> den Pool `duckdb_write` (1 Slot); der manuelle Aufruf umgeht diesen Schutz.

> **Ressourcen:** Der Airflow-Stack startet fuenf zusaetzliche Container. Wer
> die Uebung isoliert fahren will, kann Trino und Metabase vorher stoppen:
> `docker compose stop trino metabase`.

## Reset zwischen Schulungstagen

```bash
# --profile airflow nur ergaenzen, wenn Airflow gestartet wurde
docker compose --profile airflow down -v
rm -f warehouse/qvig.duckdb
docker compose up -d
```

## Datengenerator (optional neu erzeugen)

```bash
# Standard: 80 Einrichtungen, 50.000 Faelle (Seed=42, reproduzierbar)
docker compose run --rm workbench python /datengenerator/generate.py
# kleinerer Datensatz:
docker compose run --rm workbench python /datengenerator/generate.py --faelle 5000
```
