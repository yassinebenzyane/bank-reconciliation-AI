"""Agent Écrivain — mise à jour déterministe de la matrice Excel via CrewAI."""
import json
import logging

from crewai import Crew, Process

from .agent import build_ecrivain_agent
from .task import make_ecrivain_task
from .tools import UpdateBaseClientTool

log = logging.getLogger(__name__)


def run(matches: list[dict], xlsx_path: str, output_path: str) -> dict:
    """Écrit les résultats du rapprochement dans la matrice Excel.

    Pattern identique au Lecteur :
    1. L'agent CrewAI orchestre l'outil (le LLM choisit quand appeler le tool).
    2. En cas d'échec LLM, fallback direct sur le tool.
    3. Le résultat fiable est lu depuis l'instance du tool (pas depuis l'output LLM).
    """
    tool  = UpdateBaseClientTool()
    agent = build_ecrivain_agent(tool)
    task  = make_ecrivain_task(agent, matches, xlsx_path, output_path)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    try:
        crew.kickoff()
    except Exception as e:
        log.warning("Écrivain : LLM indisponible (%s) — appel direct du tool.", e)
        tool._run(
            matches_json=json.dumps(matches, default=str),
            xlsx_path=str(xlsx_path),
            output_path=str(output_path),
        )

    result = tool.result
    log.info("Écrivain terminé : %s", result.get("message", ""))
    return result
