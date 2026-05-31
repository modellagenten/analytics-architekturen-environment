# Schulungsumgebung - Analytics Architekturen (Training)

Schlanke Teilnehmenden-Umgebung. Enthaelt nur das, was zur Durchfuehrung der
praktischen Uebungen noetig ist:

- **Uebung 1 - Datenarchaeologie:** Seed-Daten + Python-Werkbank
- **Uebung 6 - OSS-Lakehouse + RLS:** MinIO + Lakekeeper + Trino + Metabase

## Link zu Übungsaufgaben und Folien

https://drive.google.com/drive/folders/1Qbpg-Vdp_rx4eGGOhBh0VUGHr1xNQO5d?usp=sharing

## Verzeichnislayout

```
analytics-architekturen-training/
├── docker-compose.yml
├── seed-data/                 <- Rohdateien fuer die Uebungen
├── python/                    <- Python-Werkbank (Uebung 1)
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/                   <- Ablage fuer eigene Skripte (-> /work im Container)
└── trino/etc/                 <- Trino-Konfiguration (Uebung 6)
    ├── config.properties
    ├── jvm.config
    ├── node.properties
    └── catalog/iceberg.properties
```

## Uebung 1 - Python-Werkbank

Statt Python lokal zu installieren, nutzen die Teilnehmenden den Container.
Die Seed-Daten liegen im Container unter `/seed-data/`.

```bash
cd schulungsumgebung/analytics-architekturen-training

# Datei inspizieren
docker compose run --rm python head -n 5 /seed-data/A_vertraege_legacy.dat
docker compose run --rm python od -A x -t x1z -v /seed-data/A_vertraege_legacy.dat | head -25
docker compose run --rm python awk '{ print length }' /seed-data/A_vertraege_legacy.dat | sort -u

# Eigenen Parser ausfuehren (Skript nach ./scripts legen -> /work)
docker compose run --rm python python /work/parser.py
```

In `/seed-data/` geschriebene Ausgaben landen automatisch wieder im lokalen
`seed-data/`-Ordner.

## Uebung 6 - OSS-Lakehouse

```bash
# Kompletten Stack starten (Python-Werkbank bleibt im Profil "tools" aus)
docker compose up -d

# Status pruefen (alles healthy? minio-init + lakekeeper-bootstrap auf "Exited (0)")
docker compose ps -a
```

**Endpoints:**

| Dienst         | URL                     | Zugang                  |
|----------------|-------------------------|-------------------------|
| MinIO Console  | http://localhost:9001   | `capitol` / `capitolcapitol` |
| Lakekeeper UI  | http://localhost:8181   | -                       |
| Trino UI       | http://localhost:8080   | User: `admin`           |
| Metabase       | http://localhost:3000   | -                       |

Beim Start wird Lakekeeper automatisch gebootstrappt (Terms akzeptiert,
Default-Projekt angelegt). Das **Warehouse `capitol`** legen die Teilnehmenden
in Phase 1 der Uebung selbst per REST-API an.

Die RLS-Dateien `access-control.properties` und `rules.json` erstellen die
Teilnehmenden in Phase 2 unter `trino/etc/` und laden sie mit
`docker compose restart trino` neu.

## Reset zwischen Schulungstagen

```bash
docker compose down -v
docker compose up -d minio minio-init lakekeeper trino metabase
```
