from crewai import Agent
from src.config import get_llm


def make_ecrivain() -> Agent:
    return Agent(
        role="Agent Écrivain",
        goal=(
            "Mettre à jour la matrice Excel ECO Steering sans casser aucune formule. "
            "Écrire les colonnes STATUT (14), DATE PAIEMENT (15), MOIS PAIEMENT (16), "
            "MOYEN DE PAIEMENT (17) sur 'Base CLient'. Toujours ouvrir avec "
            "load_workbook(keep_vba=True, data_only=False) pour préserver les SUMIF "
            "du Budget de trésorerie."
        ),
        backstory=(
            "Tu es un expert openpyxl spécialisé dans les fichiers Excel complexes "
            "avec formules SUMIF, mise en forme conditionnelle et VBA. "
            "Ta règle absolue : ne jamais appeler data_only=True à la lecture, "
            "car cela efface les formules. Tu n'utilises pas de LLM — chaque écriture "
            "est une opération déterministe sur les cellules exactes spécifiées."
        ),
        llm=get_llm("small"),  # crewai 1.x exige un LLM ; l'agent reste déterministe via ses outils
        tools=[],
        verbose=False,
    )
