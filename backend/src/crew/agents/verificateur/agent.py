from crewai import Agent
from src.config import get_llm
from .tools import MatchInvoicesTool


def build_verificateur_agent() -> Agent:
    return Agent(
        role="Expert Rapprochement Bancaire",
        goal=(
            "Pour chaque encaissement client, identifier le nom du client depuis le libellé "
            "du virement, puis trouver la combinaison exacte de factures ouvertes "
            "qui correspond au montant via l'outil subset-sum."
        ),
        backstory=(
            "Tu es expert-comptable spécialisé dans le rapprochement bancaire pour ECO Steering. "
            "Tu sais lire les libellés de virements CIH/AWB pour extraire le nom du client payeur. "
            "Tu utilises l'outil match_invoices_subset_sum pour trouver mathématiquement "
            "quelle(s) facture(s) correspond(ent) à chaque virement. "
            "Tu ne devines jamais un montant — tu t'appuies toujours sur le résultat de l'outil."
        ),
        tools=[MatchInvoicesTool()],
        llm=get_llm("small"),
        verbose=True,
    )
