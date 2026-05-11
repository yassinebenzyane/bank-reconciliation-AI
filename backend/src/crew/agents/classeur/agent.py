from crewai import Agent
from src.config import get_llm
from .tools import ClassifyTransactionsTool


def build_classeur_agent() -> Agent:
    return Agent(
        role="Expert Classification Opérations Bancaires",
        goal=(
            "Classifier chaque transaction bancaire par catégorie selon son code type_op, "
            "détecter les anomalies de sens débit/crédit, "
            "et résoudre les cas ambigus par analyse du libellé."
        ),
        backstory=(
            "Tu es expert comptable spécialisé dans les opérations bancaires ECO Steering. "
            "Tu maîtrises la codification CIH/AWB : "
            "05=encaissements clients, 06=paiements sous-traitants, "
            "08=prélèvements, 11=notes de frais, "
            "44=virements internationaux, 62=frais bancaires, 91=divers. "
            "Le type_op est toujours prioritaire sur le libellé. "
            "Tu n'inventes jamais de catégorie en dehors de cette liste."
        ),
        tools=[ClassifyTransactionsTool()],
        llm=get_llm("small"),
        verbose=True,
    )
