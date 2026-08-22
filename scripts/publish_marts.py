#!/usr/bin/env python3
"""Veroeffentlicht die dbt-Marts aus DuckDB in MySQL (Serving-Schicht fuer BI).

Zweck (Uebung 5): Metabase spricht nativ MySQL. Wir kopieren die fertigen
Marts (Star-Schema + Reporting) aus dem analytischen DuckDB in die
MySQL-Datenbank qvig_mart, auf die Metabase dann zugreift.

Umgebungsvariablen:
    QVIG_DUCKDB=/warehouse/qvig.duckdb
    MYSQL_HOST=mysql MYSQL_USER=qvig MYSQL_PASSWORD=qvig MYSQL_DB=qvig_mart
"""
import os

import duckdb
from sqlalchemy import create_engine

DUCKDB = os.environ.get("QVIG_DUCKDB", "/warehouse/qvig.duckdb")
HOST = os.environ.get("MYSQL_HOST", "mysql")
PORT = os.environ.get("MYSQL_PORT", "3306")
USER = os.environ.get("MYSQL_USER", "qvig")
PW = os.environ.get("MYSQL_PASSWORD", "qvig")
DB = os.environ.get("MYSQL_DB", "qvig_mart")

# Marts, die fuer BI bereitgestellt werden (Schema main_marts in DuckDB).
MARTS = ["dim_einrichtung", "fct_faelle", "rpt_qs_indikatoren"]


def main() -> None:
    con = duckdb.connect(DUCKDB, read_only=True)
    engine = create_engine(f"mysql+pymysql://{USER}:{PW}@{HOST}:{PORT}/{DB}")

    for mart in MARTS:
        df = con.execute(f"select * from main_marts.{mart}").fetch_df()
        df.to_sql(mart, engine, if_exists="replace", index=False, chunksize=5000)
        print(f"  qvig_mart.{mart:<22} {len(df):>8,} Zeilen")

    con.close()
    print(f"Marts veroeffentlicht -> {HOST}:{PORT}/{DB}")


if __name__ == "__main__":
    main()
