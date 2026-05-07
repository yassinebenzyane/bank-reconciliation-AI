"""MatrixParser — matrices temporelles (Budget de tréso, TVA)."""
from __future__ import annotations
from datetime import date
from .base import ParseResult, to_date, to_decimal


class MatrixParser:
    def __init__(self, ws, sheet_name: str, config: dict):
        self.ws   = ws
        self.name = sheet_name
        self.cfg  = config
        self.result = ParseResult(sheet_name, "MatrixParser")

    def parse(self, target_months: list[date] | None = None) -> ParseResult:
        date_row_num = self.cfg["date_row"]
        key_rows     = self.cfg["key_rows"]
        needed       = {date_row_num} | set(key_rows.keys())

        data: dict[int, tuple] = {}
        for i, row in enumerate(self.ws.iter_rows(
                min_row=1, max_row=max(needed), values_only=True)):
            rn = i + 1
            if rn in needed:
                data[rn] = row

        date_row = data.get(date_row_num, ())

        for col_idx, raw in enumerate(date_row):
            if raw is None:
                continue
            mois = to_date(raw)
            if mois is None:
                continue
            if target_months and mois not in target_months:
                continue

            self.result.row_count_source += 1
            values: dict[str, float | None] = {}

            for rn, field in key_rows.items():
                row = data.get(rn, ())
                v   = to_decimal(row[col_idx] if col_idx < len(row) else None)
                values[field] = float(v) if v is not None else None

            self.result.data.append({
                "mois":    mois.isoformat(),
                "col_idx": col_idx,
                "values":  values,
            })
            self.result.row_count_extracted += 1

        # Validation variation = enc - dec
        check = self.cfg.get("check_variation")
        if check:
            rvar, renc, rdec = check
            var_field = key_rows.get(rvar)
            enc_field = key_rows.get(renc)
            dec_field = key_rows.get(rdec)
            for entry in self.result.data:
                v = entry["values"]
                enc, dec, var = v.get(enc_field), v.get(dec_field), v.get(var_field)
                if None not in (enc, dec, var):
                    expected = round(enc - dec, 2)
                    if abs(expected - var) > 1.0:
                        self.result.warn(
                            f"{entry['mois']} : variation {var:.2f} ≠ "
                            f"{enc:.2f} - {dec:.2f} = {expected:.2f}"
                        )

        return self.result
