"""Evaluation du POC contre le golden test ECO Steering — J5."""
import sys
from pathlib import Path


GOLDEN_DIR = Path(__file__).parent / "golden"
INPUT_CSV = GOLDEN_DIR / "Extrait_de_compte_-_31121882729_-_20260331.csv"
INPUT_MATRIX = GOLDEN_DIR / "2026-03-13_MATRICE_ECO_STEERING.xlsx"
EXPECTED_MATRIX = GOLDEN_DIR / "2026-04-16_MATRICE_ECO_STEERING.xlsx"


def run_eval():
    """Compare la sortie du POC avec la matrice golden."""
    raise NotImplementedError("J5 — placer les fichiers golden dans eval/golden/ d'abord")


if __name__ == "__main__":
    run_eval()
