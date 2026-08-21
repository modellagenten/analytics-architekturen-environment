from pyiceberg.catalog import load_catalog
import pyarrow.parquet as pq
from pathlib import Path

catalog = load_catalog(
    "capitol",
    **{
        "type": "rest",
        "uri": "http://lakekeeper:8181/catalog",   # Service-Name, nicht localhost
        "warehouse": "capitol",
        "s3.endpoint": "http://minio:9000",          # Service-Name, nicht localhost
        "s3.path-style-access": "true",
        "s3.access-key-id": "capitol",
        "s3.secret-access-key": "capitolcapitol",
        "s3.region": "local",
    },
)

catalog.create_namespace_if_not_exists("bronze")

SEED_DIR = Path("/seed-data")   # im Container gemountet
for source_file, table_name in [
    ("A_vertraege_legacy.parquet", "vertraege_legacy"),
    ("schaden_events.parquet",     "schaden_events"),
]:
    arrow_table = pq.read_table(SEED_DIR / source_file)
    identifier = ("bronze", table_name)
    if catalog.table_exists(identifier):
        catalog.drop_table(identifier)
    iceberg_table = catalog.create_table(identifier, schema=arrow_table.schema)
    iceberg_table.append(arrow_table)
    print(f"Iceberg-Tabelle erzeugt: bronze.{table_name} ({arrow_table.num_rows:,} Zeilen)")