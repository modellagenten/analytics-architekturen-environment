#!/usr/bin/env python3
"""Uebung 7 - reproduzierbarer Data-Science-Mini-Workflow (QVIG).

Zwei Schritte entlang CRISP-DM:
  1. Ein Qualitaetsindikator, deterministisch berechnet (immer gleiches Ergebnis).
  2. Ein einfaches Vorhersagemodell (Wundinfektion ja/nein) mit ehrlicher
     Bewertung UND einem Fairness-Blick nach Region.

Bewusst klein und nachvollziehbar - kein Kaggle-Wettbewerb, sondern das
Vorgehen verstehen. Lesbar aus dem analytischen DuckDB (Marts).
"""
import os

import duckdb
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

DUCKDB = os.environ.get("QVIG_DUCKDB", "/warehouse/qvig.duckdb")
RANDOM_STATE = 42   # feste Seeds -> reproduzierbar


def lade_faelle() -> pd.DataFrame:
    con = duckdb.connect(DUCKDB, read_only=True)
    df = con.execute("""
        select
            f.wundinfektion, f.reoperation, f.asa_klasse, f.alter_jahre,
            f.verweildauer_tage, f.eingriff_art, e.region, e.bundesland
        from main_marts.fct_faelle f
        join main_marts.dim_einrichtung e using (einrichtung_sk)
    """).fetch_df()
    con.close()
    return df


def indikator_wundinfektion(df: pd.DataFrame) -> None:
    """Schritt 1: deskriptiver Indikator - bundesweite Wundinfektionsrate,
    zusaetzlich beobachtet vs. risikoerwartet je Region (einfache Adjustierung)."""
    gesamt = 100 * df["wundinfektion"].mean()
    print(f"Indikator Wundinfektionsrate bundesweit: {gesamt:.2f} %")

    # Sehr einfache Risikoadjustierung: erwartete Rate anhand ASA-Klasse.
    erwartung = df.groupby("asa_klasse")["wundinfektion"].transform("mean")
    df = df.assign(_erwartet=erwartung)
    regio = df.groupby("region").agg(
        beobachtet=("wundinfektion", "mean"),
        erwartet=("_erwartet", "mean"),
    )
    regio["oe_ratio"] = (regio["beobachtet"] / regio["erwartet"]).round(2)
    print("\nBeobachtet/Erwartet je Region (O/E > 1 = auffaellig):")
    print((regio * [100, 100, 1]).round(2).to_string())


def modell_wundinfektion(df: pd.DataFrame) -> None:
    """Schritt 2: einfaches Klassifikationsmodell + Fairness-Blick."""
    features = pd.get_dummies(
        df[["asa_klasse", "alter_jahre", "verweildauer_tage", "eingriff_art"]],
        columns=["eingriff_art"], drop_first=True,
    )
    y = df["wundinfektion"]
    x_tr, x_te, y_tr, y_te, reg_tr, reg_te = train_test_split(
        features, y, df["region"], test_size=0.25, random_state=RANDOM_STATE,
    )
    model = LogisticRegression(max_iter=1000).fit(x_tr, y_tr)
    proba = model.predict_proba(x_te)[:, 1]
    print(f"\nModell (Logistische Regression) - ROC-AUC: {roc_auc_score(y_te, proba):.3f}")

    # Fairness: taugt das Modell in jeder Region gleich gut?
    print("ROC-AUC je Region (Fairness-Blick):")
    ergebnis = pd.DataFrame({"region": reg_te.values, "y": y_te.values, "p": proba})
    for region, g in ergebnis.groupby("region"):
        auc = roc_auc_score(g["y"], g["p"]) if g["y"].nunique() > 1 else float("nan")
        print(f"  {region:<6} n={len(g):>5}  AUC={auc:.3f}")


def main() -> None:
    df = lade_faelle()
    print(f"Faelle geladen: {len(df):,}\n")
    indikator_wundinfektion(df)
    modell_wundinfektion(df)
    print("\nHinweis: gleiche Seeds -> gleiches Ergebnis bei jedem Lauf (reproduzierbar).")


if __name__ == "__main__":
    main()
