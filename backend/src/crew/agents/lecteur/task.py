import yaml
from pathlib import Path
from crewai import Agent, Task

_CONFIG = yaml.safe_load(
    (Path(__file__).parents[3] / "crew" / "config" / "tasks.yaml").read_text(encoding="utf-8")
)["lecteur_task"]


def make_lecteur_task(agent: Agent, xlsx_path: str, csv_path: str | None = None) -> Task:
    steps = []
    if csv_path:
        steps.append(f"1. Appelle parse_csv_bancaire avec path='{csv_path}'")
        steps.append(f"2. Appelle parse_excel_matrice avec path='{xlsx_path}'")
        steps.append("3. Confirme le nombre de transactions CSV et le nombre de lignes par onglet Excel.")
    else:
        steps.append(f"1. Appelle parse_excel_matrice avec path='{xlsx_path}'")
        steps.append("2. Confirme le nombre de lignes par onglet Excel.")

    description = (
        "Ingère les fichiers financiers ECO Steering :\n"
        + (f"- Relevé bancaire : {csv_path}\n" if csv_path else "")
        + f"- Matrice Excel   : {xlsx_path}\n\n"
        + "\n".join(steps)
    )

    return Task(
        description=description,
        expected_output=_CONFIG["expected_output"],
        agent=agent,
    )
