import yaml
from pathlib import Path
from crewai import Agent
from src.config import get_llm
from .tools import MatchInvoicesTool

_CONFIG = yaml.safe_load(
    (Path(__file__).parents[3] / "crew" / "config" / "agents.yaml").read_text(encoding="utf-8")
)["verificateur"]


def build_verificateur_agent() -> Agent:
    return Agent(
        config=_CONFIG,
        tools=[MatchInvoicesTool()],
        llm=get_llm("small"),
        verbose=True,
    )
