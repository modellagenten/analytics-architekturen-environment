#!/usr/bin/env python3
"""Laedt QVIG-Rohdaten als Bronze-Tabellen ins Iceberg-Lakehouse (Uebung 6).

Storage: MinIO (S3-kompatibel), Catalog: Lakekeeper (Iceberg REST),
Query-Engine: Trino. Die Teilnehmenden bauen darauf Silver/Gold in DBeaver.

Vorbedingung: Warehouse 'qvig' wurde in Phase 1 der Uebung per REST-API
angelegt (siehe uebungen/06-oss-lakehouse-rls.md).
"""
import os

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyiceberg.catalog import load_catalog

SEED = os.environ.get("QVIG_SEED", "/seed-data")

catalog = load_catalog(
    "qvig",
    **{
        "type": "rest",
        "uri": "http://lakekeeper:8181/catalog",   # Service-Name im Compose-Netz
        "warehouse": "qvig",
        "s3.endpoint": "http://minio:9000",
        "s3.path-style-access": "true",
        "s3.access-key-id": "qvig",
        "s3.secret-access-key": "qvigqvig",
        "s3.region": "local",
    },
)

catalog.create_namespace_if_not_exists("bronze")


def lade(identifier: tuple[str, str], table: pa.Table) -> None:
    if catalog.table_exists(identifier):
        catalog.drop_table(identifier)
    tbl = catalog.create_table(identifier, schema=table.schema)
    tbl.append(table)
    print(f"  Iceberg-Tabelle {identifier[0]}.{identifier[1]:<16} {table.num_rows:>8,} Zeilen")


def main() -> None:
    faelle = pq.read_table(f"{SEED}/faelle.parquet")
    lade(("bronze", "faelle"), faelle)

    einrichtungen = pa.Table.from_pandas(
        pd.read_csv(f"{SEED}/einrichtungen.csv", sep=";"), preserve_index=False
    )
    lade(("bronze", "einrichtungen"), einrichtungen)

    print("Bronze-Schicht im Lakehouse bereit.")


if __name__ == "__main__":
    main()
