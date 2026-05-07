"""Tâche A — Décodage des champs libres mixtes (ex: colonne Salariés de NdF).

1 appel LLM par onglet, batchant toutes les lignes en une fois.
Le LLM ne reçoit que du texte, jamais des montants.
"""
from __future__ import annotations
from .llm_client import LLMClient

_SYSTEM = """\
Tu reçois N lignes contenant des informations mélangées (nom, code, description, période).
Décompose chaque ligne en :
{"nom_complet": str|null, "code": str|null, "description": str|null, "periode": str|null}
Renvoie un JSON array avec exactement N éléments dans le même ordre.
Ne corrige aucune valeur. Si un champ est absent, mets null."""


class FieldDecoder:
    def __init__(self, llm: LLMClient | None = None):
        self._llm = llm or LLMClient()

    def decode_batch(self, texts: list[str]) -> list[dict]:
        """Décode une liste de textes libres. Retourne N dicts."""
        if not texts:
            return []
        import json
        user   = json.dumps(texts, ensure_ascii=False, indent=2)
        result = self._llm.call_json(_SYSTEM, user)
        if len(result) != len(texts):
            raise ValueError(
                f"FieldDecoder : attendu {len(texts)} éléments, reçu {len(result)}"
            )
        return result
