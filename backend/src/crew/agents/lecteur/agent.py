import yaml
from pathlib import Path
from crewai import Agent
from src.config import get_llm
from .tools import ParseExcelTool, ParseCsvTool

_CONFIG = yaml.safe_load(
    (Path(__file__).parents[3] / "crew" / "config" / "agents.yaml").read_text(encoding="utf-8")
)["lecteur"]


def build_lecteur_agent(csv_tool: ParseCsvTool, excel_tool: ParseExcelTool) -> Agent:
    tools = [excel_tool]
    if csv_tool is not None:
        tools.insert(0, csv_tool)

    return Agent(
        config=_CONFIG,
        tools=tools,
        llm=get_llm("small"),
        verbose=True,
    )
