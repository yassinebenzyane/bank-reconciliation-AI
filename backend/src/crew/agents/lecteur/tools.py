import json
import openpyxl
from crewai.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from .config import TABLE_CONFIGS, MATRIX_CONFIGS, PRET_CONFIG, BANK_CSV_CONFIG
from .parsers.table_parser import TableParser
from .parsers.matrix_parser import MatrixParser
from .parsers.key_value_parser import KeyValueParser
from .parsers.bank_statement_parser import BankStatementParser


class PathInput(BaseModel):
    path: str


class ParseExcelTool(BaseTool):
    """Parse la matrice Excel ECO Steering — tous onglets."""

    name: str = "parse_excel_matrice"
    description: str = (
        "Parse la matrice Excel ECO Steering : Base CLient, Base Sous-traitants, "
        "Frais Généraux, NdF, Paies, TVA, Budget de tréso, Prêt. "
        "Entrée : chemin absolu du fichier .xlsx. "
        "Retourne un résumé JSON des données extraites."
    )
    args_schema: type[BaseModel] = PathInput

    # Résultat typé accessible après l'exécution
    _result: dict = PrivateAttr(default_factory=dict)

    def _run(self, path: str) -> str:
        wb = openpyxl.load_workbook(str(path), data_only=True)
        sheets = wb.sheetnames
        result: dict = {}

        for sheet_name, cfg in TABLE_CONFIGS.items():
            if sheet_name in sheets:
                pr = TableParser(wb[sheet_name], sheet_name, cfg).parse()
                result[sheet_name] = pr.data

        for sheet_name, cfg in MATRIX_CONFIGS.items():
            if sheet_name in sheets:
                pr = MatrixParser(wb[sheet_name], sheet_name, cfg).parse()
                result[sheet_name] = pr.data

        if "Prêt" in sheets:
            pr = KeyValueParser(wb["Prêt"], "Prêt", PRET_CONFIG).parse()
            result["Prêt"] = pr.data[0] if pr.data else {}

        wb.close()
        self._result = result

        # Résumé compact pour le LLM (pas les données brutes complètes)
        summary = {
            sheet: f"{len(rows)} lignes extraites"
            for sheet, rows in result.items()
            if isinstance(rows, list)
        }
        if isinstance(result.get("Prêt"), dict):
            summary["Prêt"] = "OK"
        return json.dumps(summary, ensure_ascii=False)

    @property
    def result(self) -> dict:
        return self._result


class ParseCsvTool(BaseTool):
    """Parse un relevé bancaire CSV CIH/AWB."""

    name: str = "parse_csv_bancaire"
    description: str = (
        "Parse un relevé bancaire CSV (encodage Windows-1252, séparateur ;, en-tête ligne 7). "
        "Entrée : chemin absolu du fichier .csv. "
        "Retourne un résumé JSON des transactions extraites."
    )
    args_schema: type[BaseModel] = PathInput

    _result: list = PrivateAttr(default_factory=list)

    def _run(self, path: str) -> str:
        cfg = BANK_CSV_CONFIG["BPVF"]
        pr = BankStatementParser(str(path), cfg).parse()
        self._result = pr.data

        meta = next((r for r in pr.data if r.get("_meta")), {})
        txns = [r for r in pr.data if not r.get("_meta")]
        summary = {
            "nb_transactions": len(txns),
            "solde_initial": str(meta.get("solde_initial", "?")),
            "solde_final": str(meta.get("solde_final", "?")),
        }
        return json.dumps(summary, ensure_ascii=False)

    @property
    def result(self) -> list:
        return self._result
