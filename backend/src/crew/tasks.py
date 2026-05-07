"""Stubs de tâches CrewAI — implémentation J2–J4."""
from crewai import Task


def make_ping_task(agent) -> Task:
    return Task(
        description="Réponds uniquement avec le mot 'pong'.",
        expected_output="pong",
        agent=agent,
    )


# J2 — parsing
def make_ingest_task(agent, csv_path: str, xlsx_path: str) -> Task:
    raise NotImplementedError("J2")


# J3 — classification
def make_classify_task(agent, ingested_data) -> Task:
    raise NotImplementedError("J3")


# J3 — vérification
def make_verify_task(agent, classified_data) -> Task:
    raise NotImplementedError("J3")


# J4 — écriture
def make_write_task(agent, verified_data, output_path: str) -> Task:
    raise NotImplementedError("J4")


# J5 — prévisionnel
def make_forecast_task(agent, context) -> Task:
    raise NotImplementedError("J5")
