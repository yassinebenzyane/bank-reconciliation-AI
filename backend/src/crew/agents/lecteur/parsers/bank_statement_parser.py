"""BankStatementParser — relevé bancaire CSV (format BPVF).

Principe : colonnes fixes hardcodées. Vérification obligatoire de la balance.
"""
from __future__ import annotations
import re
from decimal import Decimal
from .base import ParseResult, to_date


def _clean_amount(raw: str, cleanup: list[tuple]) -> Decimal | None:
    if not raw or not raw.strip():
        return None
    s = raw
    for old, new in cleanup:
        s = s.replace(old, new)
    s = s.strip()
    try:
        return Decimal(s) if s else None
    except Exception:
        return None


class BankStatementParser:
    def __init__(self, path: str, config: dict):
        self.path   = path
        self.cfg    = config
        self.result = ParseResult("Relevé bancaire", "BankStatementParser")

    def parse(self) -> ParseResult:
        cfg     = self.cfg
        cols    = cfg["columns"]
        cleanup = cfg["amount_cleanup"]

        with open(self.path, encoding=cfg["encoding"], errors="replace") as f:
            lines = f.readlines()

        solde_initial: Decimal | None = None
        solde_final:   Decimal | None = None

        for i, line in enumerate(lines):
            parts = line.rstrip("\n").split(cfg["separator"])

            # Détecter les lignes de solde (col[9] contient "Solde")
            c9 = parts[9].strip() if len(parts) > 9 else ""
            if cfg["solde_col_9_label"] in c9:
                if solde_initial is None:
                    raw = parts[cfg["solde_initial_col"]] if len(parts) > cfg["solde_initial_col"] else ""
                    solde_initial = _clean_amount(raw, cleanup)
                else:
                    raw = parts[cfg["solde_final_col"]] if len(parts) > cfg["solde_final_col"] else ""
                    solde_final = _clean_amount(raw, cleanup)
                continue

            # Lignes de transaction (col[2] contient une date)
            if i < cfg["data_start"] - 1:
                continue

            date_raw = parts[cols["date_operation"]] if len(parts) > cols["date_operation"] else ""
            d = to_date(date_raw.strip())
            if d is None:
                continue

            self.result.row_count_source += 1

            debit_raw  = parts[cols["debit"]]  if len(parts) > cols["debit"]  else ""
            credit_raw = parts[cols["credit"]] if len(parts) > cols["credit"] else ""
            debit  = _clean_amount(debit_raw,  cleanup)
            credit = _clean_amount(credit_raw, cleanup)

            if debit is None and credit is None:
                continue

            montant = debit if debit else credit
            sens    = "debit" if debit else "credit"

            # Type opération : "44 - Transfert émis" → "44"
            type_raw = parts[cols["type_operation"]] if len(parts) > cols["type_operation"] else ""
            type_op  = type_raw.strip().split(" ")[0] if type_raw.strip() else "??"

            libelle = parts[cols["libelle"]].strip() if len(parts) > cols["libelle"] else ""

            self.result.data.append({
                "date_operation": d.isoformat(),
                "date_valeur":    to_date(parts[cols["date_valeur"]].strip() if len(parts) > cols["date_valeur"] else ""),
                "libelle":        libelle,
                "montant":        float(montant),
                "sens":           sens,
                "type_operation": type_op,
                "reference":      parts[cols["reference"]].strip() if len(parts) > cols["reference"] else None,
            })
            self.result.row_count_extracted += 1

        # Balance check — validation obligatoire
        if solde_initial is not None and solde_final is not None:
            credits = sum(Decimal(str(t["montant"])) for t in self.result.data if t["sens"] == "credit")
            debits  = sum(Decimal(str(t["montant"])) for t in self.result.data if t["sens"] == "debit")
            expected = solde_initial + credits - debits
            ecart = abs(expected - solde_final)
            if ecart > Decimal("1"):
                self.result.warn(
                    f"Balance KO : {solde_initial:.2f} + {credits:.2f} - {debits:.2f} "
                    f"= {expected:.2f} ≠ {solde_final:.2f} (écart {ecart:.2f} €)"
                )
            self.result.data.insert(0, {
                "_meta": True,
                "solde_initial": float(solde_initial),
                "solde_final":   float(solde_final),
                "total_credits": float(credits),
                "total_debits":  float(debits),
                "balance_ecart": float(ecart),
                "balance_ok":    ecart <= Decimal("1"),
            })

        return self.result
