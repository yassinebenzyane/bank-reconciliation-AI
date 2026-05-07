"""Tâche B — Normalisation des labels du Budget de tréso.

1 seul appel LLM, résultat mis en cache indéfiniment.
Le LLM ne reçoit que des labels texte, jamais des montants.
"""
from __future__ import annotations
import json
from pathlib import Path
from .llm_client import LLMClient

_SYSTEM = """\
Tu reçois la liste des labels de la matrice de trésorerie ECO Steering.
Pour chaque label, renvoie un objet JSON :
{
  "row": <numéro de ligne int>,
  "label": <texte original>,
  "categorie": "ENCAISSEMENT" | "DECAISSEMENT" | "SOLDE" | "TOTAL",
  "type": "CA" | "TVA" | "ST" | "FG" | "NDF" | "SALAIRE" | "COTISATION" | "IMPOT" | "PRET" | "BANQUE" | "AUTRE",
  "code_normalise": <slug stable, ex: "CA_REEL", "URSSAF", "TVA_PAYER", "TRESO_FIN">
}
Renvoie un JSON array avec exactement N objets dans le même ordre.
Ne modifie aucune valeur numérique."""


class LabelNormalizer:
    def __init__(self, cache_file: str | Path, llm: LLMClient | None = None):
        self._cache = Path(cache_file)
        self._llm   = llm or LLMClient()

    def normalize(self, labels: list[tuple[int, str]]) -> list[dict]:
        """labels = [(row_num, label_text), ...]"""
        if self._cache.exists():
            cached = json.loads(self._cache.read_text(encoding="utf-8"))
            # Valider que le cache correspond aux mêmes labels
            cached_rows = {e["row"] for e in cached}
            input_rows  = {r for r, _ in labels}
            if cached_rows == input_rows:
                return cached

        user = json.dumps(
            [{"row": r, "label": l} for r, l in labels],
            ensure_ascii=False, indent=2
        )
        result = self._llm.call_json(_SYSTEM, user)

        if len(result) != len(labels):
            raise ValueError(
                f"LabelNormalizer : attendu {len(labels)} entrées, reçu {len(result)}"
            )

        self._cache.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
