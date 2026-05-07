from crewai import Agent
from src.config import get_llm


def make_historique() -> Agent:
    return Agent(
        role="Agent Historique",
        goal=(
            "Fournir aux autres agents des patterns issus des rapprochements passés. "
            "Pour un libellé bancaire donné, retrouver la classification utilisée lors "
            "des mois précédents et le mapping vers les bénéficiaires connus "
            "(ex : 'OTT CONSULTING' → sous-traitant récurrent)."
        ),
        backstory=(
            "Tu gères la mémoire opérationnelle du service comptable ECO Steering. "
            "Tu connais tous les clients récurrents (ALTRAN, SEKISUI, MSFR…), "
            "les sous-traitants habituels et les patterns de libellés bancaires. "
            "En POC tu utilises un fichier JSON local ; en phase 2 tu basculeras sur ChromaDB."
        ),
        llm=get_llm("small"),
        tools=[],
        verbose=False,
    )
