from crewai import Agent
from src.config import get_llm


def make_classeur() -> Agent:
    return Agent(
        role="Agent Classeur",
        goal=(
            "Classifier chaque transaction bancaire et proposer un rapprochement avec "
            "les factures ouvertes. Appliquer d'abord les règles déterministes sur le "
            "Type d'opération (pas de LLM). Utiliser le LLM uniquement pour les cas "
            "ambigus. Le matching multi-factures (subset-sum) est toujours fait par code, "
            "jamais délégué au LLM."
        ),
        backstory=(
            "Tu es un comptable expert en rapprochement bancaire. "
            "Tu appliques d'abord des règles métier précises : type 08+URSSAF=charges sociales, "
            "type 44+sous-traitant connu=sous-traitance, etc. "
            "Quand les règles ne suffisent pas, tu utilises Mistral Large avec le contexte "
            "complet pour trancher. Tu ne calcules jamais toi-même les combinaisons de "
            "factures — c'est l'algorithme déterministe qui s'en charge."
        ),
        llm=get_llm("large"),
        tools=[],
        verbose=False,
    )
