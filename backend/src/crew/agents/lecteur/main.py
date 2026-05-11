"""Agent Lecteur — orchestrateur parsers Python + validation."""
from __future__ import annotations
import logging
import time
from datetime import date

from crewai import Crew, Process

from .agent import build_lecteur_agent
from .task import make_lecteur_task
from .tools import ParseCsvTool, ParseExcelTool
from .validators import validate_all

log = logging.getLogger(__name__)


def run(
    xlsx_path: str,
    csv_path: str | None = None,
    target_month: date | None = None,
    use_semantic: bool = False,
    detect_drift: bool = False,
) -> dict:
    """Point d'entrée de l'Agent Lecteur.

    L'agent CrewAI orchestre ParseCsvTool et ParseExcelTool.
    Les données typées (Decimal, date) sont récupérées depuis les instances
    des tools après kickoff — le LLM ne voit qu'un résumé JSON.
    """
    t0 = time.time()

    csv_tool   = ParseCsvTool()   if csv_path else None
    excel_tool = ParseExcelTool()

    agent = build_lecteur_agent(csv_tool, excel_tool)
    task  = make_lecteur_task(agent, xlsx_path, csv_path)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    try:
        crew.kickoff()
    except Exception as e:
        log.warning("Lecteur : LLM indisponible (%s) — appel direct des tools.", e)
        excel_tool._run(xlsx_path)
        if csv_tool is not None:
            csv_tool._run(csv_path)

    # Données typées récupérées directement depuis les tools (pas depuis l'output LLM)
    result: dict = {**excel_tool.result}
    if csv_tool is not None:
        result["releve_bancaire"] = csv_tool.result

    validation_errors = validate_all(result)
    result["_validation"] = validation_errors
    if validation_errors:
        for sheet, errs in validation_errors.items():
            for e in errs:
                log.warning("[VALIDATION] %s : %s", sheet, e)

    result["_meta"] = {
        "xlsx":          str(xlsx_path),
        "csv":           str(csv_path) if csv_path else None,
        "duration_s":    round(time.time() - t0, 2),
        "llm_calls":     0,
        "sheets_parsed": list(excel_tool.result.keys()),
        "validation_ok": not validation_errors,
    }

    log.info(
        "Agent Lecteur terminé en %.1fs | validation=%s",
        result["_meta"]["duration_s"],
        "OK" if not validation_errors else f"{sum(len(e) for e in validation_errors.values())} erreurs",
    )
    return result


def _log_result(pr) -> None:
    log.info(
        "  %s : %d/%d lignes extraites, %d warnings",
        pr.sheet, pr.row_count_extracted, pr.row_count_source, len(pr.warnings),
    )
    for w in pr.warnings:
        log.warning("  [%s] %s", pr.sheet, w)
