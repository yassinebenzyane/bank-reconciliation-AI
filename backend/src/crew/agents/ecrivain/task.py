import json
import yaml
from pathlib import Path
from crewai import Agent, Task

_CONFIG = yaml.safe_load(
    (Path(__file__).parents[3] / "crew" / "config" / "tasks.yaml").read_text(encoding="utf-8")
)["ecrivain_task"]


def make_ecrivain_task(agent: Agent, matches: list[dict], xlsx_path: str, output_path: str) -> Task:
    description = _CONFIG["description"].format(
        xlsx_path=xlsx_path,
        output_path=output_path,
        matches_json=json.dumps(matches, ensure_ascii=False, default=str),
    )
    return Task(
        description=description,
        expected_output=_CONFIG["expected_output"],
        agent=agent,
    )
