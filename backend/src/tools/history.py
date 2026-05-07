"""Accès à l'historique JSON des patterns — implémentation J2/J3."""
import json
from pathlib import Path

from src.config import HISTORY_PATH


def _load() -> dict:
    p = Path(HISTORY_PATH)
    if not p.exists():
        return {"clients": {}, "sous_traitants": {}, "patterns": []}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def lookup_client_pattern(libelle: str) -> dict | None:
    """Cherche dans l'historique la classification passée d'un libellé similaire.

    En POC : correspondance exacte sur tokens. Phase 2 : embedding ChromaDB.
    Retourne {"categorie": ..., "confiance": ...} ou None.
    """
    raise NotImplementedError("J3")


def lookup_sous_traitant(libelle: str) -> str | None:
    """Mappe un libellé bancaire vers un nom de sous-traitant connu.

    Ex : 'OTT CONSULTING' → 'OTT CONSULTING SARL'.
    Retourne le nom normalisé ou None.
    """
    data = _load()
    return data.get("sous_traitants", {}).get(libelle.upper())
