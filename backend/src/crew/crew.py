"""Crew principal — assemblage des 4 agents via @CrewBase et fichiers YAML."""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from src.config import get_llm
from src.crew.agents.lecteur.tools import ParseCsvTool, ParseExcelTool
from src.crew.agents.classeur.tools import ClassifyTransactionsTool
from src.crew.agents.verificateur.tools import MatchInvoicesTool
from src.crew.agents.ecrivain.tools import UpdateBaseClientTool


@CrewBase
class ReconciliationCrew:
    """Crew de rapprochement bancaire ECO Steering."""

    agents_config = "src/crew/config/agents.yaml"
    tasks_config  = "src/crew/config/tasks.yaml"

    # ── Agents ───────────────────────────────────────────────────────

    @agent
    def lecteur(self) -> Agent:
        self._csv_tool   = ParseCsvTool()
        self._excel_tool = ParseExcelTool()
        return Agent(
            config=self.agents_config["lecteur"],
            tools=[self._csv_tool, self._excel_tool],
            llm=get_llm("small"),
            verbose=True,
        )

    @agent
    def classeur(self) -> Agent:
        return Agent(
            config=self.agents_config["classeur"],
            tools=[ClassifyTransactionsTool()],
            llm=get_llm("small"),
            verbose=True,
        )

    @agent
    def verificateur(self) -> Agent:
        return Agent(
            config=self.agents_config["verificateur"],
            tools=[MatchInvoicesTool()],
            llm=get_llm("small"),
            verbose=True,
        )

    @agent
    def ecrivain(self) -> Agent:
        self._ecrivain_tool = UpdateBaseClientTool()
        return Agent(
            config=self.agents_config["ecrivain"],
            tools=[self._ecrivain_tool],
            llm=get_llm("small"),
            verbose=True,
        )

    # ── Tasks ─────────────────────────────────────────────────────────

    @task
    def lecteur_task(self) -> Task:
        return Task(config=self.tasks_config["lecteur_task"])

    @task
    def classeur_task(self) -> Task:
        return Task(config=self.tasks_config["classeur_task"])

    @task
    def verificateur_task(self) -> Task:
        return Task(config=self.tasks_config["verificateur_task"])

    @task
    def ecrivain_task(self) -> Task:
        return Task(config=self.tasks_config["ecrivain_task"])

    # ── Crew ──────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
