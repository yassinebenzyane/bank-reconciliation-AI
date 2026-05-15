"""Outil déterministe d'écriture dans la matrice Excel ECO Steering.

Règle absolue : load_workbook(data_only=False, keep_vba=True).
Ne jamais passer data_only=True — cela efface les formules SUMIF du Budget de tréso.
"""
import json
import logging
from datetime import datetime, date
from pathlib import Path

import openpyxl
from crewai.tools import BaseTool
from pydantic import BaseModel

log = logging.getLogger(__name__)

# Colonnes de l'onglet Base CLient (1-indexé, basé sur l'exploration du fichier réel)
_COL_N_FACTURE = 4   # D — N° FACTURE
_COL_STATUT    = 14  # N — STATUT (a payer / paye)
_COL_DATE_P    = 15  # O — DATE PAIEMENT
_COL_MOIS_P    = 16  # P — MOIS PAIEMENT
_COL_MOYEN     = 17  # Q — MOYEN DE PAIEMENT
_COL_REF       = 18  # R — Référence Paiement

_SHEET = "Base CLient"


class WriteInput(BaseModel):
    matches_json: str   # JSON array des résultats du rapprochement (verificateur)
    xlsx_path:    str   # chemin de la matrice source
    output_path:  str   # chemin de la matrice mise à jour


class UpdateBaseClientTool(BaseTool):
    """Met à jour la matrice Excel ECO Steering avec les résultats du rapprochement validé."""

    name: str        = "update_base_client"
    _result: dict    = PrivateAttr(default_factory=dict)
    description: str = (
        "Met à jour l'onglet Base CLient de la matrice Excel ECO Steering "
        "avec les paiements rapprochés et validés par le comptable. "
        "Pour chaque facture matchée, renseigne : STATUT (payé), DATE PAIEMENT, "
        "MOIS PAIEMENT, MOYEN DE PAIEMENT (virement), Référence Paiement. "
        "Ne modifie jamais les factures non rapprochées ni les colonnes hors périmètre."
    )
    args_schema: type[BaseModel] = WriteInput

    def _run(self, matches_json: str, xlsx_path: str, output_path: str) -> str:
        matches = json.loads(matches_json)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.load_workbook(xlsx_path, data_only=False, keep_vba=True)
        ws = wb[_SHEET]

        # Construire un index facture_id → données de paiement depuis les matches
        paiements: dict[str, dict] = {}
        for m in matches:
            if m.get("statut") != "match_exact":
                continue
            txn       = m.get("transaction", {})
            date_op   = _parse_date(txn.get("date_operation"))
            reference = str(txn.get("reference") or "").strip()
            mois_p    = date_op.replace(day=1) if date_op else None

            for fid in m.get("factures_ids", []):
                paiements[str(fid).strip()] = {
                    "date_p": date_op,
                    "mois_p": mois_p,
                    "ref":    reference,
                }

        if not paiements:
            return json.dumps({"updated": 0, "message": "Aucun match exact à écrire."})

        updated = 0
        skipped = []

        for row in ws.iter_rows(min_row=4):
            n_fact = str(row[_COL_N_FACTURE - 1].value or "").strip()
            if n_fact not in paiements:
                continue
            statut_actuel = str(row[_COL_STATUT - 1].value or "").strip().lower()
            if statut_actuel == "paye":
                skipped.append(n_fact + " (déjà payé)")
                continue

            p = paiements[n_fact]
            row[_COL_STATUT - 1].value = "paye"
            row[_COL_DATE_P  - 1].value = p["date_p"]
            row[_COL_MOIS_P  - 1].value = p["mois_p"]
            row[_COL_MOYEN   - 1].value = "virement"
            row[_COL_REF     - 1].value = p["ref"]
            updated += 1
            log.info("Écrivain : L%d %s -> payé %s", row[0].row, n_fact, p["date_p"])

        wb.save(output_path)
        wb.close()

        msg = f"{updated} ligne(s) mises à jour dans Base CLient."
        if skipped:
            msg += f" Ignorées (déjà payées) : {skipped}."
        log.info("Écrivain : %s", msg)
        self._result = {"updated": updated, "skipped": skipped, "output": output_path, "message": msg}
        return json.dumps(self._result)

    @property
    def result(self) -> dict:
        return self._result


def _parse_date(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (datetime, date)):
        return datetime(raw.year, raw.month, raw.day) if isinstance(raw, date) else raw
    try:
        return datetime.fromisoformat(str(raw)[:10])
    except ValueError:
        return None
