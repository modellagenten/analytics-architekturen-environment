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
| **MinIO + Lakekeeper + Trino** | OSS-Lakehouse (Iceberg) + Row-Level Security | 6 |
| **Metabase** | Self-Service BI (spricht MySQL und Trino) | 5 |
| **Python-Werkbank** | Loader, Data Science (scikit-learn) | 4, 7 |

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
└── trino/etc/                 <- Trino-Konfiguration (Iceberg + MySQL)
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

## Uebungsbezug

| Uebung | Was passiert |
|---|---|
| **3 - Staging & Column Store** | `load_mysql.py` fuellt MySQL (Zeilenspeicher); dieselben Daten in DuckDB (Spaltenspeicher) - Query-Vergleich |
| **4 - ELT mit dbt Core** | `load_raw.py` + `dbt build`: Staging-Modelle mit Tests, Lineage, Docs |
| **2b - Data Vault** | Modelle unter `models/data_vault/` (Hubs/Link/Satellite, Insert-Only) |
| **5 - Metabase** | `publish_marts.py` schiebt Marts nach `qvig_mart`; Metabase -> MySQL |
| **6 - Lakehouse + RLS** | `load_lake.py` -> Iceberg Bronze; Silver/Gold + RLS in Trino |
| **7 - Data Science** | `ds_indikator.py`: reproduzierbarer Indikator + einfaches Modell |

## dbt-Kommandos (Cheatsheet)

```bash
docker compose run --rm workbench dbt build          # alles bauen + testen
docker compose run --rm workbench dbt run             # nur Modelle
docker compose run --rm workbench dbt test            # nur Tests
docker compose run --rm workbench dbt snapshot        # SCD2-Snapshot
docker compose run --rm workbench dbt docs generate   # Doku/Lineage
```

## Reset zwischen Schulungstagen

```bash
docker compose down -v
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
