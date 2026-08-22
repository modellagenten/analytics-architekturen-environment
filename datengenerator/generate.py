#!/usr/bin/env python3
"""QVIG-Datengenerator - synthetische Daten fuer das Analytics-Architekturen-Training.

QVIG = fiktives "Qualitaetsinstitut fuer Versorgung im Gesundheitswesen".
Verfahren: Hueftendoprothetik (Erstimplantation). Alle Daten sind rein
synthetisch und reproduzierbar (fester Seed) - keine echten Patienten- oder
Krankenhausdaten.

Erzeugte Rohdaten (Analogie zum echten QS-Datenfluss):

    einrichtungen.csv        Stammdaten der Krankenhaeuser (operatives Quellsystem)
    faelle.csv               QS-Dokumentation der Leistungserbringer (bewusst "roh")
    sozialdaten.csv          Follow-up der Krankenkassen (andere Granularitaet)
    patientenbefragung.json  Patientenbefragung (Dokument / JSON)
    landesstellen.csv        Nutzer der Landesstellen (fuer Row-Level Security)
    qs_dokumentation.xml      Roh-XML-Auszug der Spezifikation (Data-Lake-Bronze)
    faelle.parquet           typisierte Faelle (Data-Lake-Bronze, Iceberg)

Aufruf:
    python generate.py                      # Standard: 80 Einrichtungen, 50.000 Faelle
    python generate.py --faelle 5000        # kleinerer Datensatz
    python generate.py --out ../seed-data   # Zielverzeichnis
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

SEED = 42
BERICHTSJAHR = 2024

BUNDESLAENDER = [
    ("BW", "Baden-Wuerttemberg", "Sued"),
    ("BY", "Bayern", "Sued"),
    ("BE", "Berlin", "Ost"),
    ("BB", "Brandenburg", "Ost"),
    ("HB", "Bremen", "Nord"),
    ("HH", "Hamburg", "Nord"),
    ("HE", "Hessen", "West"),
    ("MV", "Mecklenburg-Vorpommern", "Ost"),
    ("NI", "Niedersachsen", "Nord"),
    ("NW", "Nordrhein-Westfalen", "West"),
    ("RP", "Rheinland-Pfalz", "West"),
    ("SL", "Saarland", "West"),
    ("SN", "Sachsen", "Ost"),
    ("ST", "Sachsen-Anhalt", "Ost"),
    ("SH", "Schleswig-Holstein", "Nord"),
    ("TH", "Thueringen", "Ost"),
]

# Gewichtung grob nach Bevoelkerung, damit grosse Laender mehr Einrichtungen haben.
LAND_GEWICHT = {
    "NW": 21, "BY": 16, "BW": 13, "NI": 9, "HE": 7, "RP": 5, "SN": 5,
    "BE": 4, "SH": 3, "BB": 3, "ST": 3, "TH": 3, "HH": 2, "MV": 2, "SL": 1, "HB": 1,
}

TRAEGER = ["oeffentlich", "freigemeinnuetzig", "privat"]
STADT_TEILE = [
    "Nord", "Sued", "Ost", "West", "Mitte", "am Park", "an der Aue", "Hoehe",
    "im Tal", "Marien", "Sankt Josef", "Elisabeth", "Barmherzige Brueder",
]
STADT_NAMEN = [
    "Falkenberg", "Lindau", "Rosenheim", "Weidenbach", "Ahlbeck", "Goldbach",
    "Neustadt", "Buchholz", "Steinfeld", "Hohenwald", "Birkenau", "Tannheim",
    "Seeburg", "Moorbach", "Kranichfeld", "Ellwangen", "Sonnenberg", "Waldkirch",
    "Reinhausen", "Bergheim", "Auental", "Freihofen", "Nordheim", "Katzbach",
]

# ICD-Diagnosen fuer Huefterkrankungen (fiktiv-plausibel).
DIAGNOSEN = ["M16.0", "M16.1", "M16.9", "M87.05", "S72.00", "M16.2"]
PROTHESEN = ["zementiert", "unzementiert", "hybrid"]


def bundesland_pool() -> list[str]:
    pool: list[str] = []
    for kuerzel, gewicht in LAND_GEWICHT.items():
        pool.extend([kuerzel] * gewicht)
    return pool


def land_info(kuerzel: str) -> tuple[str, str]:
    for k, name, region in BUNDESLAENDER:
        if k == kuerzel:
            return name, region
    raise KeyError(kuerzel)


def gen_einrichtungen(rng: random.Random, anzahl: int) -> list[dict]:
    """Krankenhaus-Stammdaten. Jede Einrichtung bekommt eine verdeckte
    'qualitaets_tendenz', die spaeter die Ergebnisqualitaet beeinflusst -
    so entstehen echte Ausreisser fuer die Analyse (Uebung 5 und 7)."""
    pool = bundesland_pool()
    einrichtungen = []
    for i in range(1, anzahl + 1):
        land = rng.choice(pool)
        land_name, region = land_info(land)
        stadt = rng.choice(STADT_NAMEN)
        teil = rng.choice(STADT_TEILE)
        traeger = rng.choices(TRAEGER, weights=[45, 35, 20])[0]
        betten = int(rng.triangular(120, 1400, 350))
        lehr = betten > 800 and rng.random() < 0.6
        # Qualitaetstendenz: die meisten Haeuser sind ok, wenige sind besser
        # oder schlechter als der Durchschnitt (Grundlage fuer Ausreisser).
        tendenz = rng.gauss(0, 1)
        einrichtungen.append({
            "einrichtung_id": f"KH{i:04d}",
            "name": f"Klinikum {stadt} {teil}".strip(),
            "traeger_typ": traeger,
            "bundesland": land,
            "bundesland_name": land_name,
            "region": region,
            "betten": betten,
            "lehrkrankenhaus": 1 if lehr else 0,
            "aktiv": 1,
            "gueltig_ab": date(2015, 1, 1).isoformat(),
            "_qualitaets_tendenz": round(tendenz, 4),
        })
    return einrichtungen


def _rand_date(rng: random.Random, jahr: int) -> date:
    start = date(jahr, 1, 1)
    return start + timedelta(days=rng.randint(0, 364))


def gen_faelle(rng: random.Random, einrichtungen: list[dict], anzahl: int) -> list[dict]:
    """QS-Dokumentation je Fall. Ergebnis-Indikatoren haengen an ASA-Klasse,
    Alter und der verdeckten Qualitaetstendenz der Einrichtung."""
    # Fallzahl je Einrichtung grob proportional zur Bettenzahl.
    gewichte = [e["betten"] for e in einrichtungen]
    faelle = []
    for n in range(1, anzahl + 1):
        e = rng.choices(einrichtungen, weights=gewichte)[0]
        aufnahme = _rand_date(rng, BERICHTSJAHR)
        op = aufnahme + timedelta(days=rng.randint(0, 3))
        quartal = (op.month - 1) // 3 + 1
        alter = int(min(95, max(45, rng.gauss(70, 9))))
        geschlecht = rng.choices(["m", "w", "d"], weights=[46, 53, 1])[0]
        asa = rng.choices([1, 2, 3, 4], weights=[15, 45, 33, 7])[0]
        notfall = rng.random() < 0.12
        op_dauer = int(rng.triangular(45, 210, 90) + (asa - 1) * 8)
        verweildauer = max(3, int(rng.gauss(9 + (asa - 1) * 1.5 + (3 if notfall else 0), 3)))
        entlass = op + timedelta(days=verweildauer)

        # Basisrisiko + Einflussgroessen -> Wahrscheinlichkeit fuer Komplikationen.
        risiko = (
            0.02
            + 0.010 * (asa - 1)
            + 0.0015 * max(0, alter - 70)
            + (0.02 if notfall else 0)
            + 0.02 * e["_qualitaets_tendenz"]
        )
        risiko = min(0.5, max(0.005, risiko))
        wundinfektion = 1 if rng.random() < risiko * 0.8 else 0
        luxation = 1 if rng.random() < risiko * 0.6 else 0
        reoperation = 1 if (wundinfektion or luxation) and rng.random() < 0.5 else 0
        letalitaet = 1 if rng.random() < risiko * 0.15 else 0

        bewegl_auf = int(min(60, max(10, rng.gauss(35, 8))))
        bewegl_ent = int(min(100, bewegl_auf + rng.gauss(25, 8) - (10 if reoperation else 0)))

        pseudonym = f"P{BERICHTSJAHR}{n:07d}"
        faelle.append({
            "fall_id": f"F{BERICHTSJAHR}{n:07d}",
            "einrichtung_id": e["einrichtung_id"],
            "patient_pseudonym": pseudonym,
            "berichtsjahr": BERICHTSJAHR,
            "quartal": quartal,
            "aufnahme_datum": aufnahme,
            "op_datum": op,
            "entlass_datum": entlass,
            "alter": alter,
            "geschlecht": geschlecht,
            "asa_klasse": asa,
            "eingriff_art": "notfall" if notfall else "elektiv",
            "diagnose_icd": rng.choice(DIAGNOSEN),
            "prothesen_typ": rng.choice(PROTHESEN),
            "op_dauer_minuten": op_dauer,
            "verweildauer_tage": verweildauer,
            "wundinfektion": wundinfektion,
            "luxation": luxation,
            "reoperation": reoperation,
            "letalitaet": letalitaet,
            "beweglichkeit_aufnahme": bewegl_auf,
            "beweglichkeit_entlassung": bewegl_ent,
        })
    return faelle


# ─── "Verschmutzung" der Roh-CSV, damit Staging/Tests Substanz haben ────────

def _dirty_geschlecht(rng: random.Random, wert: str) -> str:
    # Mal gross, mal klein geliefert.
    return wert.upper() if rng.random() < 0.5 else wert.lower()


def _dirty_dezimal(rng: random.Random, wert: int) -> str:
    # Deutsche Dezimalschreibweise mit Komma bei einem Teil der Zeilen.
    if rng.random() < 0.3:
        return f"{wert},0"
    return str(wert)


def _de_date(d: date) -> str:
    # Deutsches Datumsformat TT.MM.JJJJ (muss im Staging gecastet werden).
    return d.strftime("%d.%m.%Y")


def write_faelle_csv(path: Path, faelle: list[dict], rng: random.Random) -> None:
    felder = [
        "fall_id", "einrichtung_id", "patient_pseudonym", "berichtsjahr", "quartal",
        "aufnahme_datum", "op_datum", "entlass_datum", "alter", "geschlecht",
        "asa_klasse", "eingriff_art", "diagnose_icd", "prothesen_typ",
        "op_dauer_minuten", "verweildauer_tage", "wundinfektion", "luxation",
        "reoperation", "letalitaet", "beweglichkeit_aufnahme", "beweglichkeit_entlassung",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";")
        w.writeheader()
        for fall in faelle:
            row = dict(fall)
            row["aufnahme_datum"] = _de_date(fall["aufnahme_datum"])
            row["op_datum"] = _de_date(fall["op_datum"])
            row["entlass_datum"] = _de_date(fall["entlass_datum"])
            row["geschlecht"] = _dirty_geschlecht(rng, fall["geschlecht"])
            row["op_dauer_minuten"] = _dirty_dezimal(rng, fall["op_dauer_minuten"])
            w.writerow(row)


def write_einrichtungen_csv(path: Path, einrichtungen: list[dict]) -> None:
    felder = [
        "einrichtung_id", "name", "traeger_typ", "bundesland", "bundesland_name",
        "region", "betten", "lehrkrankenhaus", "aktiv", "gueltig_ab",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";")
        w.writeheader()
        for e in einrichtungen:
            w.writerow({k: e[k] for k in felder})


def write_sozialdaten_csv(path: Path, faelle: list[dict], rng: random.Random) -> None:
    """Kassen-Follow-up: nur ein Teil der Patienten, andere Granularitaet
    (pro Pseudonym), teils spaetere Folge-Operationen und 1-Jahres-Sterblichkeit."""
    gruende = ["Prothesenwechsel", "Infektsanierung", "Luxationsbehandlung", "Nachblutung"]
    felder = ["patient_pseudonym", "folge_op_datum", "folge_op_grund", "verstorben_365"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";")
        w.writeheader()
        for fall in faelle:
            # Nur ~35 % der Faelle tauchen im Kassen-Abgleich auf.
            if rng.random() > 0.35:
                continue
            hat_folge = fall["reoperation"] == 1 and rng.random() < 0.7
            folge_datum = ""
            grund = ""
            if hat_folge:
                folge = fall["entlass_datum"] + timedelta(days=rng.randint(10, 350))
                folge_datum = folge.isoformat()
                grund = rng.choice(gruende)
            verstorben = 1 if (fall["letalitaet"] == 1 or rng.random() < 0.01) else 0
            w.writerow({
                "patient_pseudonym": fall["patient_pseudonym"],
                "folge_op_datum": folge_datum,
                "folge_op_grund": grund,
                "verstorben_365": verstorben,
            })


def write_befragung_json(path: Path, faelle: list[dict], rng: random.Random) -> None:
    """Patientenbefragung als verschachteltes JSON-Dokument (Document-Store-Beispiel)."""
    freitexte = [
        "Sehr zufrieden mit der Betreuung.",
        "Schmerzen nach OP schnell besser geworden.",
        "Wartezeit war lang, Ergebnis gut.",
        "Freundliches Personal, wuerde wiederkommen.",
        "Reha-Anschluss haette besser laufen koennen.",
        "",
    ]
    dokumente = []
    for fall in faelle:
        if rng.random() > 0.25:  # nur ein Teil nimmt teil
            continue
        schmerz_vorher = rng.randint(5, 10)
        schmerz_nachher = max(0, schmerz_vorher - rng.randint(2, 8) - (2 if fall["reoperation"] else 0))
        zufried = max(1, min(5, round(rng.gauss(4 - (1 if fall["reoperation"] else 0), 0.8))))
        dokumente.append({
            "pseudonym": fall["patient_pseudonym"],
            "fall_id": fall["fall_id"],
            "berichtsjahr": fall["berichtsjahr"],
            "antworten": {
                "zufriedenheit_gesamt": zufried,
                "schmerz_vorher": schmerz_vorher,
                "schmerz_nachher": schmerz_nachher,
                "wuerde_empfehlen": zufried >= 4,
            },
            "freitext": rng.choice(freitexte),
        })
    with path.open("w", encoding="utf-8") as f:
        json.dump(dokumente, f, ensure_ascii=False, indent=2)


def write_landesstellen_csv(path: Path) -> None:
    """Nutzer der Landesstellen fuer Row-Level Security: jede Stelle sieht nur
    ihr Bundesland, der Bund sieht alles."""
    felder = ["nutzer", "bundesland", "rolle"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=felder, delimiter=";")
        w.writeheader()
        w.writerow({"nutzer": "bund", "bundesland": "*", "rolle": "bund"})
        for kuerzel, name, _region in BUNDESLAENDER:
            w.writerow({
                "nutzer": f"ls_{kuerzel.lower()}",
                "bundesland": kuerzel,
                "rolle": "landesstelle",
            })


def write_xml(path: Path, faelle: list[dict], einrichtungen: list[dict], rng: random.Random,
              anzahl: int) -> None:
    """Roh-XML-Auszug analog einer QS-Spezifikation (verschachtelt).
    Nur ein kleiner Auszug - fuer die Dokument-Modellierung und den Data Lake."""
    by_id = {e["einrichtung_id"]: e for e in einrichtungen}
    auswahl = faelle[:anzahl]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<QS-Dokumentation verfahren=\"HEP\" jahr=\"%d\">" % BERICHTSJAHR]
    for fall in auswahl:
        e = by_id[fall["einrichtung_id"]]
        lines.append("  <Fall id=\"%s\">" % fall["fall_id"])
        lines.append("    <Einrichtung ik=\"%s\" bundesland=\"%s\">%s</Einrichtung>"
                     % (e["einrichtung_id"], e["bundesland"], escape(e["name"])))
        lines.append("    <Patient pseudonym=\"%s\" alter=\"%d\" geschlecht=\"%s\"/>"
                     % (fall["patient_pseudonym"], fall["alter"], fall["geschlecht"]))
        lines.append("    <OP datum=\"%s\" art=\"%s\" dauerMinuten=\"%d\" prothese=\"%s\"/>"
                     % (fall["op_datum"].isoformat(), fall["eingriff_art"],
                        fall["op_dauer_minuten"], fall["prothesen_typ"]))
        lines.append("    <Indikatoren>")
        lines.append("      <Wundinfektion>%d</Wundinfektion>" % fall["wundinfektion"])
        lines.append("      <Luxation>%d</Luxation>" % fall["luxation"])
        lines.append("      <Reoperation>%d</Reoperation>" % fall["reoperation"])
        lines.append("    </Indikatoren>")
        lines.append("  </Fall>")
    lines.append("</QS-Dokumentation>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_parquet(path: Path, faelle: list[dict]) -> bool:
    """Typisierte Faelle als Parquet fuer den Data Lake (Iceberg-Bronze).
    Benoetigt pyarrow; bei Fehlen wird uebersprungen."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("  pyarrow nicht installiert - faelle.parquet uebersprungen.")
        return False
    cols = {
        "fall_id": [f["fall_id"] for f in faelle],
        "einrichtung_id": [f["einrichtung_id"] for f in faelle],
        "patient_pseudonym": [f["patient_pseudonym"] for f in faelle],
        "berichtsjahr": [f["berichtsjahr"] for f in faelle],
        "quartal": [f["quartal"] for f in faelle],
        "op_datum": [f["op_datum"].isoformat() for f in faelle],
        "alter": [f["alter"] for f in faelle],
        "geschlecht": [f["geschlecht"] for f in faelle],
        "asa_klasse": [f["asa_klasse"] for f in faelle],
        "eingriff_art": [f["eingriff_art"] for f in faelle],
        "diagnose_icd": [f["diagnose_icd"] for f in faelle],
        "prothesen_typ": [f["prothesen_typ"] for f in faelle],
        "op_dauer_minuten": [f["op_dauer_minuten"] for f in faelle],
        "verweildauer_tage": [f["verweildauer_tage"] for f in faelle],
        "wundinfektion": [f["wundinfektion"] for f in faelle],
        "luxation": [f["luxation"] for f in faelle],
        "reoperation": [f["reoperation"] for f in faelle],
        "letalitaet": [f["letalitaet"] for f in faelle],
        "beweglichkeit_aufnahme": [f["beweglichkeit_aufnahme"] for f in faelle],
        "beweglichkeit_entlassung": [f["beweglichkeit_entlassung"] for f in faelle],
    }
    pq.write_table(pa.table(cols), path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="QVIG-Datengenerator (synthetisch)")
    parser.add_argument("--einrichtungen", type=int, default=80)
    parser.add_argument("--faelle", type=int, default=50_000)
    parser.add_argument("--xml-faelle", type=int, default=50,
                        help="Anzahl Faelle im XML-Auszug")
    parser.add_argument("--out", type=str, default=None,
                        help="Zielverzeichnis (Default: ../seed-data relativ zum Skript)")
    args = parser.parse_args()

    out = Path(args.out) if args.out else (Path(__file__).resolve().parent.parent / "seed-data")
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    print(f"QVIG-Datengenerator (Seed={SEED})")
    print(f"  Zielverzeichnis: {out}")

    einrichtungen = gen_einrichtungen(rng, args.einrichtungen)
    faelle = gen_faelle(rng, einrichtungen, args.faelle)

    write_einrichtungen_csv(out / "einrichtungen.csv", einrichtungen)
    print(f"  einrichtungen.csv        {len(einrichtungen):>7,} Zeilen")
    write_faelle_csv(out / "faelle.csv", faelle, rng)
    print(f"  faelle.csv               {len(faelle):>7,} Zeilen")
    write_sozialdaten_csv(out / "sozialdaten.csv", faelle, rng)
    write_befragung_json(out / "patientenbefragung.json", faelle, rng)
    write_landesstellen_csv(out / "landesstellen.csv")
    write_xml(out / "qs_dokumentation.xml", faelle, einrichtungen, rng, args.xml_faelle)
    print(f"  qs_dokumentation.xml     {args.xml_faelle:>7,} Faelle (Auszug)")
    if write_parquet(out / "faelle.parquet", faelle):
        print(f"  faelle.parquet           {len(faelle):>7,} Zeilen")

    print("Fertig.")


if __name__ == "__main__":
    main()
