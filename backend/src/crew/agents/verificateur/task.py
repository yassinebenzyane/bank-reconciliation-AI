import json
import yaml
from pathlib import Path
from crewai import Agent, Task

_CONFIG = yaml.safe_load(
    (Path(__file__).parents[3] / "crew" / "config" / "tasks.yaml").read_text(encoding="utf-8")
)["verificateur_task"]


def make_verificateur_task(
    agent: Agent,
    encaissements: list[dict],
    factures_ouvertes: list[dict],
) -> Task:
    enc_summary = [
        {"idx": i, "date": t.get("date_operation"), "montant": float(t.get("montant") or 0),
         "libelle": str(t.get("libelle", ""))[:60]}
        for i, t in enumerate(encaissements)
    ]
    description = _CONFIG["description"].format(
        nb_encaissements=len(encaissements),
        nb_factures=len(factures_ouvertes),
        encaissements_json=json.dumps(enc_summary, ensure_ascii=False),
        factures_json=json.dumps(
            [{"id": f.get("id"), "client": str(f.get("client") or ""),
              "montant_ttc": float(f.get("montant_ttc") or 0)}
             for f in factures_ouvertes],
            ensure_ascii=False,
        ),
    )
    return Task(
        description=description,
        expected_output=_CONFIG["expected_output"],
        agent=agent,
    )
