"""Utilitaires partagés par tous les parsers."""
from __future__ import annotations
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


def to_decimal(val) -> Decimal | None:
    if isinstance(val, (int, float)):
        return Decimal(str(round(val, 6)))
    if isinstance(val, str):
        s = re.sub(r"[\xa0\s€]", "", val).replace(",", ".")
        try:
            return Decimal(s) if s else None
        except InvalidOperation:
            return None
    return None


def to_date(val) -> date | None:
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    # Serial Excel (entier) — openpyxl retourne parfois des int avec data_only=True
    if isinstance(val, (int, float)) and 40000 < val < 60000:
        return date(1899, 12, 30) + timedelta(days=int(val))
    if isinstance(val, str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None


def date_to_serial(d: date) -> int:
    """Convertit une date Python en serial Excel (pour écriture dans col P)."""
    return (d - date(1899, 12, 30)).days


def cell(row: tuple, idx: int):
    return row[idx] if row and 0 <= idx < len(row) else None


class ParseResult:
    """Enveloppe standard pour la sortie de tous les parsers."""

    def __init__(self, sheet: str, parser: str):
        self.sheet   = sheet
        self.parser  = parser
        self.data:     list[dict] = []
        self.warnings: list[str]  = []
        self.row_count_source     = 0
        self.row_count_extracted  = 0

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def to_dict(self) -> dict:
        return {
            "sheet":               self.sheet,
            "parser":              self.parser,
            "row_count_source":    self.row_count_source,
            "row_count_extracted": self.row_count_extracted,
            "warnings":            self.warnings,
            "data":                self.data,
        }
