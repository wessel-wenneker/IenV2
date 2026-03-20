# -*- coding: utf-8 -*-
"""Vergelijkt twee antwoordenbladen op een paar hoofdeigenschappen."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


DATA_MAP = Path(__file__).resolve().parent / "Data"
EERSTE_ANTWOORDBLAD = DATA_MAP / "Antwoordenblad_Gr98_V1.0.json"
TWEEDE_ANTWOORDBLAD = DATA_MAP / "Antwoordenblad_Gr98V2.0.json"


def leesJsonBestand(pad: Path) -> dict:
    """Leest een JSON-bestand in."""
    with pad.open("r", encoding="utf-8") as bestand:
        return json.load(bestand)


def berekenScore(
    eigenschappen_boot1: list[float],
    eigenschappen_boot2: list[float],
    eigenschap_namen: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    """Zet de eigenschappen van twee schepen om naar punten."""
    punten_boot1 = np.zeros(len(eigenschap_namen))
    punten_boot2 = np.zeros(len(eigenschap_namen))
    for index in range(len(eigenschap_namen) - 1):
        if eigenschappen_boot1[index] > eigenschappen_boot2[index]:
            punten_boot1[index] = 10
            punten_boot2[index] = 6
        else:
            punten_boot1[index] = 6
            punten_boot2[index] = 10
    punten_boot1[-1] = punten_boot1[:-1].sum()
    punten_boot2[-1] = punten_boot2[:-1].sum()
    return punten_boot1, punten_boot2


def maakPuntendiagram(
    punten_boot1: np.ndarray,
    punten_boot2: np.ndarray,
    eigenschap_namen: list[str],
) -> None:
    """Toont het puntendiagram van twee schepen naast elkaar."""
    figuur, assen = plt.subplots(1, len(eigenschap_namen), figsize=(20, 5))
    x_posities = [0, 1]
    for index, eigenschap in enumerate(eigenschap_namen):
        assen[index].bar(x_posities, [punten_boot1[index], punten_boot2[index]], color=["darkblue", "orange"])
        assen[index].set_title(eigenschap)
        assen[index].set_xticks(x_posities)
        assen[index].set_xticklabels(["Alleskunner 1", "Alleskunner 2"])
        assen[index].grid(axis="y", linestyle="--")
    assen[0].set_ylabel("Punten")
    figuur.tight_layout()
    plt.show()


def main() -> None:
    """Leest twee antwoordenbladen in en toont het puntendiagram."""
    data_boot1 = leesJsonBestand(EERSTE_ANTWOORDBLAD)
    data_boot2 = leesJsonBestand(TWEEDE_ANTWOORDBLAD)
    eigenschappen_boot1 = [
        data_boot1["Weerstand_Holtrop_Mennen"]["Totale_weerstand_bij_14_kn #[kN]"],
        data_boot1["Deklast_transition_pieces"]["Aantal_transition_pieces #[-]"] * data_boot1["Deklast_transition_pieces"]["Gewicht_per_transition_piece #[N]"],
        data_boot1["Neerwaartse_krachten"]["Deplacement #[N]"],
        data_boot1["Kraan_beladingsconditie"]["SWLmax_kraan #[N]"],
    ]
    eigenschappen_boot2 = [
        data_boot2["Weerstand_Holtrop_Mennen"]["Totale_weerstand_bij_14_kn #[kN]"],
        data_boot2["Deklast_transition_pieces"]["Aantal_transition_pieces #[-]"] * data_boot2["Deklast_transition_pieces"]["Gewicht_per_transition_piece #[N]"],
        data_boot2["Neerwaartse_krachten"]["Deplacement #[N]"],
        data_boot2["Kraan_beladingsconditie"]["SWLmax_kraan #[N]"],
    ]
    eigenschap_namen = ["scheepsweerstand", "ladinggewicht", "leeg scheepsgewicht", "kraanlast", "totaal"]
    punten_boot1, punten_boot2 = berekenScore(eigenschappen_boot1, eigenschappen_boot2, eigenschap_namen)
    maakPuntendiagram(punten_boot1, punten_boot2, eigenschap_namen)


if __name__ == "__main__":
    main()
