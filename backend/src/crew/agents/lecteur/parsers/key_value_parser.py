"""KeyValueParser — onglet Prêt (structure clé/valeur col A / col B)."""
from __future__ import annotations
from .base import ParseResult, cell, to_date, to_decimal


class KeyValueParser:
    def __init__(self, ws, sheet_name: str, config: dict):
        self.ws   = ws
        self.name = sheet_name
        self.cfg  = config
        self.result = ParseResult(sheet_name, "KeyValueParser")

    def parse(self) -> ParseResult:
        lc   = self.cfg["label_col"]
        vc   = self.cfg["value_col"]
        rows = self.cfg["rows"]

        all_rows: dict[int, tuple] = {}
        for i, row in enumerate(self.ws.iter_rows(
                min_row=1, max_row=max(rows.keys()), values_only=True)):
            all_rows[i + 1] = row

        record: dict = {}
        for rn, (field, kind) in rows.items():
            row = all_rows.get(rn, ())
            raw = cell(row, vc)
            if kind == "date":
                record[field] = to_date(raw)
            elif kind in ("decimal", "int"):
                v = to_decimal(raw)
                record[field] = int(v) if kind == "int" and v else (float(v) if v else None)
            else:
                record[field] = str(raw).strip() if raw is not None else None

        row1 = all_rows.get(1, ())
        montant = to_decimal(cell(row1, self.cfg.get("montant_initial_col", 1)))
        if montant:
            record["montant_initial"] = float(montant)

        nom_row = self.cfg.get("nom_from_label_row")
        if nom_row and nom_row in all_rows:
            lbl = cell(all_rows[nom_row], self.cfg["label_col"])
            record["nom"] = str(lbl).strip() if lbl else None

        if record:
            self.result.data.append(record)
            self.result.row_count_source    = len(rows)
            self.result.row_count_extracted = 1

        return self.result
