"""Lösung Gruppe D – Tarif-Hierarchie mit OCCURS (12-fache Wiederholgruppen).

Datei-Layout D_tarife_legacy.dat:

  Pos    Länge  Feld           Format          Bemerkung
  -----  -----  -------------  --------------  --------------------------
      0     10  vertrag_id     Alphanumerisch
     10      4  tarif_code     Alphanumerisch
     14      4  sparte         Alphanumerisch  z.B. "HAUS", "KFZB", "LEB1"
     18      8  gueltig_ab     YYYYMMDD

  Dann 12-mal die Wiederholgruppe (OCCURS 12 TIMES) je 9 Bytes:
     26      9  monat_1_block  Format unten
     35      9  monat_2_block
     ...
    125      9  monat_12_block

  Pro Monatsblock (9 Bytes):
      +0      2  monat_nr       z.B. "01" für Januar
      +2      7  praemie_zoned  zoned decimal, S9(5)V99 (7 Stellen)

  Gesamtlänge: 134 Bytes
"""

import os
from pathlib import Path

import pandas as pd


def resolve_seed_file(filename: str) -> Path:
    """Findet die Seed-Datei im Container (/seed-data) wie auch lokal im Repo."""
    # 1. Explizit per Env-Variable gesetzt
    env_dir = os.environ.get("CAPITOL_SEED_DATA_DIR")
    if env_dir:
        return Path(env_dir) / filename
    # 2. Container-Mount (docker-compose: ./seed-data:/seed-data)
    if Path("/seed-data").is_dir():
        return Path("/seed-data") / filename
    # 3. Lokal: vom Skript aus nach einem seed-data-Verzeichnis suchen
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "seed-data"
        if candidate.is_dir():
            return candidate / filename
    # 4. Fallback relativ zum Arbeitsverzeichnis
    return Path("seed-data") / filename


FILE_PATH = resolve_seed_file("D_tarife_legacy.dat")


def parse_date(raw: str) -> pd.Timestamp | None:
    raw = (raw or "").strip()
    if not raw or set(raw) == {"0"}:
        return None
    try:
        return pd.to_datetime(raw, format="%Y%m%d", errors="raise")
    except (ValueError, TypeError):
        return None


_ZONED_SIGN = {
    "{": ("+", "0"), "A": ("+", "1"), "B": ("+", "2"), "C": ("+", "3"), "D": ("+", "4"),
    "E": ("+", "5"), "F": ("+", "6"), "G": ("+", "7"), "H": ("+", "8"), "I": ("+", "9"),
    "}": ("-", "0"), "J": ("-", "1"), "K": ("-", "2"), "L": ("-", "3"), "M": ("-", "4"),
    "N": ("-", "5"), "O": ("-", "6"), "P": ("-", "7"), "Q": ("-", "8"), "R": ("-", "9"),
}


def parse_zoned_decimal(raw: str, decimals: int = 2) -> float | None:
    raw = (raw or "").strip()
    if not raw or set(raw) <= {" ", "0"}:
        return None
    last = raw[-1]
    if last in _ZONED_SIGN:
        sign, last_digit = _ZONED_SIGN[last]
        digits = raw[:-1] + last_digit
    elif last.isdigit():
        sign, digits = "+", raw
    else:
        return None
    try:
        return float(f"{sign}{digits}") / (10 ** decimals)
    except ValueError:
        return None


def read_fixed_width(path: Path) -> pd.DataFrame:
    """Liest die Datei und gibt sie direkt in **langer Form** zurück
    (eine Zeile pro Vertrag und Monat).
    """
    with path.open("r", encoding="latin-1") as fh:
        lines = [line.rstrip("\n") for line in fh if line.strip()]

    rows = []
    for line in lines:
        if len(line) < 134:
            continue

        head = {
            "vertrag_id": line[0:10].strip(),
            "tarif_code": line[10:14].strip(),
            "sparte": line[14:18].strip(),
            "gueltig_ab": parse_date(line[18:26]),
        }

        # 12 OCCURS-Gruppen (je 9 Bytes: 2 monat_nr + 7 zoned) explodieren
        for i in range(12):
            block_start = 26 + i * 9
            block = line[block_start:block_start + 9]
            monat_nr_raw = block[0:2].strip()
            praemie_raw = block[2:9]
            if not monat_nr_raw:
                continue  # leere Monatsangabe (z.B. Vertrag begann mitten im Jahr)
            try:
                monat_nr = int(monat_nr_raw)
            except ValueError:
                continue
            rows.append({
                **head,
                "monat_nr": monat_nr,
                "praemie_monat": parse_zoned_decimal(praemie_raw),
            })
    return pd.DataFrame(rows)


def data_quality_report(df: pd.DataFrame) -> dict:
    n = len(df)
    by_vertrag = df.groupby("vertrag_id").size()
    return {
        "n_rows": n,
        "n_vertraege": int(df["vertrag_id"].nunique()),
        "monate_pro_vertrag_distribution": by_vertrag.value_counts().to_dict(),
        "null_quote_praemie": float(df["praemie_monat"].isna().mean()),
        "duplicates_in_pk": int(df.duplicated(subset=["vertrag_id", "monat_nr"]).sum()),
        "sparten_verteilung": df["sparte"].value_counts().to_dict(),
        "praemie_summary": {
            "min": float(df["praemie_monat"].min()) if df["praemie_monat"].notna().any() else None,
            "mean": float(df["praemie_monat"].mean()) if df["praemie_monat"].notna().any() else None,
            "max": float(df["praemie_monat"].max()) if df["praemie_monat"].notna().any() else None,
        },
    }


if __name__ == "__main__":
    df = read_fixed_width(FILE_PATH)
    out_path = FILE_PATH.with_suffix(".parquet")
    df.to_parquet(out_path)
    print(f"Geschrieben: {out_path} ({len(df)} Zeilen)")
    import json
    print(json.dumps(data_quality_report(df), default=str, indent=2))
