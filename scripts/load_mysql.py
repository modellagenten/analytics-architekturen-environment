#!/usr/bin/env python3
"""Laedt QVIG-Stammdaten und Faelle ins operative MySQL (Zeilenspeicher).

Zweck (Uebung 3): MySQL als operatives Quellsystem / ODS. Dieselben Daten
liegen spaeter analytisch in DuckDB (Spaltenspeicher) - so lassen sich
Zeilen- vs. Spaltenspeicher direkt vergleichen.

Umgebungsvariablen (Default = Docker-Compose-Netz):
    MYSQL_HOST=mysql  MYSQL_PORT=3306
    MYSQL_USER=qvig   MYSQL_PASSWORD=qvig   MYSQL_DB=qvig_op
    QVIG_SEED=/seed-data
"""
import os

import pandas as pd
from sqlalchemy import create_engine

SEED = os.environ.get("QVIG_SEED", "/seed-data")
HOST = os.environ.get("MYSQL_HOST", "mysql")
PORT = os.environ.get("MYSQL_PORT", "3306")
USER = os.environ.get("MYSQL_USER", "qvig")
PW = os.environ.get("MYSQL_PASSWORD", "qvig")
DB = os.environ.get("MYSQL_DB", "qvig_op")


def main() -> None:
    engine = create_engine(f"mysql+pymysql://{USER}:{PW}@{HOST}:{PORT}/{DB}")

    einrichtungen = pd.read_csv(f"{SEED}/einrichtungen.csv", sep=";")
    einrichtungen.to_sql("einrichtung", engine, if_exists="replace", index=False)
    print(f"  qvig_op.einrichtung   {len(einrichtungen):>8,} Zeilen")

    # Typisierte, saubere Faelle aus Parquet (fuer faire Query-Vergleiche).
    faelle = pd.read_parquet(f"{SEED}/faelle.parquet")
    faelle.to_sql("fall", engine, if_exists="replace", index=False, chunksize=5000)
    print(f"  qvig_op.fall          {len(faelle):>8,} Zeilen")

    print(f"Operatives MySQL geladen -> {HOST}:{PORT}/{DB}")


if __name__ == "__main__":
    main()
