from crewai import Agent
from src.config import get_llm
from .tools import ParseExcelTool, ParseCsvTool


def build_lecteur_agent(csv_tool: ParseCsvTool, excel_tool: ParseExcelTool) -> Agent:
    tools = [excel_tool]
    if csv_tool is not None:
        tools.insert(0, csv_tool)

    return Agent(
        role="Agent Lecteur — Ingestion Fichiers Financiers",
        goal=(
            "Parser avec précision le relevé bancaire CSV et la matrice Excel ECO Steering, "
            "extraire toutes les données structurées et signaler toute anomalie de parsing."
        ),
        backstory=(
            "Tu es expert en ingestion de données financières pour ECO Steering. "
            "Tu maîtrises le format CSV CIH/AWB (Windows-1252, séparateur ;, en-tête ligne 7) "
            "et la structure de la matrice Excel ECO Steering (Base CLient en-tête ligne 3, "
            "formules SUMIF à préserver). "
            "Tu appelles les outils de parsing et valides que toutes les données ont été extraites."
        ),
        tools=tools,
        llm=get_llm("small"),
        verbose=True,
    )
