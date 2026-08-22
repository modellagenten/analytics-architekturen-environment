#!/usr/bin/env python3
"""Laedt die QVIG-Seed-Dateien in die DuckDB-Rohschicht (raw.*).

Das ist der "E/L"-Teil der Pipeline (Extract/Load): Rohdaten moeglichst
unveraendert ins Warehouse bringen. Die eigentliche Transformation macht
danach dbt.

Umgebungsvariablen:
    QVIG_DUCKDB   Pfad zur DuckDB-Datei   (Default: /warehouse/qvig.duckdb)
    QVIG_SEED     Verzeichnis der Seeds   (Default: /seed-data)
"""
import os

import duckdb

DB = os.environ.get("QVIG_DUCKDB", "/warehouse/qvig.duckdb")
SEED = os.environ.get("QVIG_SEED", "/seed-data")


def main() -> None:
    con = duckdb.connect(DB)
    con.execute("create schema if not exists raw")

    # CSV-Quellen bewusst komplett als Text laden (all_varchar):
    # Die Rohschicht bleibt "roh", das Casting passiert im dbt-Staging.
    csv_quellen = {
        "einrichtungen": "einrichtungen.csv",
        "faelle": "faelle.csv",
        "sozialdaten": "sozialdaten.csv",
    }
    for tabelle, datei in csv_quellen.items():
        con.execute(f"""
            create or replace table raw.{tabelle} as
            select *, now() as _loaded_at
            from read_csv('{SEED}/{datei}', delim=';', header=true, all_varchar=true)
        """)
        n = con.execute(f"select count(*) from raw.{tabelle}").fetchone()[0]
        print(f"  raw.{tabelle:<16} {n:>8,} Zeilen")

    # Patientenbefragung als JSON-Dokument (verschachtelte Struktur bleibt erhalten).
    con.execute(f"""
        create or replace table raw.patientenbefragung as
        select *, now() as _loaded_at
        from read_json('{SEED}/patientenbefragung.json')
    """)
    n = con.execute("select count(*) from raw.patientenbefragung").fetchone()[0]
    print(f"  raw.patientenbefragung {n:>8,} Zeilen")

    con.close()
    print(f"Rohschicht geladen -> {DB}")


if __name__ == "__main__":
    main()
