import yaml
from pathlib import Path
from crewai import Agent
from src.config import get_llm
from .tools import UpdateBaseClientTool

_CONFIG = yaml.safe_load(
    (Path(__file__).parents[3] / "crew" / "config" / "agents.yaml").read_text(encoding="utf-8")
)["ecrivain"]


def build_ecrivain_agent(tool: UpdateBaseClientTool) -> Agent:
    return Agent(
        config=_CONFIG,
        tools=[tool],
        llm=get_llm("small"),
        verbose=True,
    )
