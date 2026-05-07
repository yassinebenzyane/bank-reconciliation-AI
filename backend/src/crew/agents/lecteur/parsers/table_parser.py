"""TableParser — onglets tabulaires (Base CLient, ST, FG, NdF, Paies)."""
from __future__ import annotations
import unicodedata
from .base import ParseResult, cell, to_date, to_decimal


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


class TableParser:
    def __init__(self, ws, sheet_name: str, config: dict):
        self.ws  = ws
        self.name = sheet_name
        self.cfg  = config
        self.result = ParseResult(sheet_name, "TableParser")

    def parse(self) -> ParseResult:
        # Corrige le tag <dimension> XML incorrect en recalculant max_row depuis _cells.
        # Sans ça, iter_rows s'arrête trop tôt (ex: 1813 au lieu de 2329 lignes réelles).
        try:
            if self.ws._cells:
                self.ws._max_row = max(r for r, _ in self.ws._cells)
                self.ws._max_column = max(c for _, c in self.ws._cells)
        except (AttributeError, ValueError, TypeError):
            pass

        cols          = self.cfg["columns"]
        date_cols     = set(self.cfg.get("date_columns", []))
        amount_cols   = set(self.cfg.get("amount_columns", []))
        required      = self.cfg.get("required", [])
        skip_vals     = {_nfc(v.lower()) for v in self.cfg.get("skip_values", [])}
        statut_ouvert = {_nfc(s.lower()) for s in self.cfg.get("statut_ouvert", [])}
        statut_paye   = {_nfc(s.lower()) for s in self.cfg.get("statut_paye", [])}
        statut_reel   = {_nfc(s) for s in self.cfg.get("statut_ligne_reel", set())}

        for row in self.ws.iter_rows(min_row=self.cfg["data_start"], values_only=True):
            self.result.row_count_source += 1
            if not row or all(v is None for v in row):
                continue

            first_req = required[0] if required else None
            if first_req and first_req in cols:
                raw = cell(row, cols[first_req])
                if raw is None or _nfc(str(raw).strip().lower()) in skip_vals:
                    continue

            record: dict = {}
            for field, idx in cols.items():
                raw = cell(row, idx)
                if field in date_cols:
                    record[field] = to_date(raw)
                elif field in amount_cols:
                    record[field] = to_decimal(raw)
                else:
                    record[field] = str(raw).strip() if raw is not None else None

            if any(not record.get(r) for r in required):
                continue

            # statut_ligne doit être normalisé avant statut_paiement (dépendance)
            if "statut_ligne" in record:
                s = _nfc((record["statut_ligne"] or "").strip().lower())
                record["is_reel"] = s in statut_reel or s in {_nfc("réel"), _nfc("reel")}

            if "statut_paiement" in record:
                s_n = _nfc((record["statut_paiement"] or "").lower().strip())
                if s_n in statut_paye:
                    record["statut_normalise"] = "paye"
                elif s_n:
                    record["statut_normalise"] = "ouvert"
                else:
                    record["statut_normalise"] = "autre"

            ttc = record.get("montant_ttc")
            ht  = record.get("montant_ht")
            if ttc is not None and ht is not None and ttc < ht:
                self.result.warn(
                    f"Facture {record.get('n_facture','?')} : TTC ({ttc}) < HT ({ht})"
                )

            self.result.data.append(record)
            self.result.row_count_extracted += 1

        return self.result
