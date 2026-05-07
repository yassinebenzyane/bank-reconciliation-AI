"""Tâche C — Détection de drift structurel entre deux imports.

1 appel LLM optionnel par import. Bloque le parsing si severity=high.
"""
from __future__ import annotations
import json
from .llm_client import LLMClient

_SYSTEM = """\
Compare deux signatures de structure Excel.
Renvoie : {"has_drift": bool, "changes": [str], "severity": "low"|"high"}
Si severity=high, c'est un changement cassant (colonne déplacée, header manquant).
Si severity=low, c'est un ajout de ligne ou changement cosmétique."""


class DriftDetector:
    def __init__(self, llm: LLMClient | None = None):
        self._llm = llm or LLMClient()

    def check(self, previous_sig: dict, current_sig: dict) -> dict:
        user = json.dumps({
            "previous": previous_sig,
            "current":  current_sig,
        }, ensure_ascii=False, indent=2)
        result = self._llm.call_json(_SYSTEM, user)
        if result.get("severity") == "high":
            raise RuntimeError(
                f"Drift structurel critique détecté : {result.get('changes')}"
            )
        return result

    @staticmethod
    def signature(ws, n_header_rows: int = 3) -> dict:
        """Extrait une signature légère (premières lignes + nb colonnes)."""
        rows = []
        for i, row in enumerate(ws.iter_rows(max_row=n_header_rows, values_only=True)):
            rows.append([str(v)[:50] if v is not None else None for v in row[:30]])
        return {"header_rows": rows, "n_header_rows": n_header_rows}
