from crewai import Agent, Crew, Process, Task
from src.config import get_llm
from src.crew.tasks import make_ping_task


def run_ping() -> str:
    """Crew minimal de validation — vérifie que l'orchestration CrewAI fonctionne."""
    ping_agent = Agent(
        role="Ping Agent",
        goal="Répondre 'pong' à chaque sollicitation.",
        backstory="Agent de test qui valide que l'orchestration CrewAI est opérationnelle.",
        llm=get_llm("small"),
        tools=[],
        verbose=True,
    )
    task = make_ping_task(ping_agent)
    crew = Crew(
        agents=[ping_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()
    return str(result)


def build_reconciliation_crew(csv_path: str, xlsx_path: str) -> Crew:
    """Construit le Crew complet — implémentation J2–J5."""
    raise NotImplementedError("Crew complet disponible à partir de J2.")
