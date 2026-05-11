import json
from crewai import Agent, Task


def make_classeur_task(agent: Agent, transactions: list[dict]) -> Task:
    return Task(
        description=(
            f"Classifie les {len(transactions)} transactions bancaires ci-dessous.\n\n"
            "Appelle l'outil classify_transactions avec ce JSON exact :\n"
            f"{json.dumps(transactions, ensure_ascii=False, default=str)}\n\n"
            "Après l'appel à l'outil, examine les transactions avec categorie='inconnu'. "
            "Pour chacune, analyse le libellé et remplace 'inconnu' par la catégorie "
            "la plus probable parmi : encaissement_client, paiement_st, prelevement, "
            "note_de_frais, international, frais_bancaires, divers. "
            "Si tu ne peux pas déterminer la catégorie, laisse 'inconnu'.\n\n"
            "Retourne UNIQUEMENT le JSON array final, sans texte autour."
        ),
        expected_output=(
            "Un JSON array de transactions, chacune enrichie avec :\n"
            "- categorie : encaissement_client | paiement_st | prelevement | "
            "note_de_frais | international | frais_bancaires | divers | inconnu\n"
            "- anomalie : string décrivant l'anomalie détectée, ou null\n"
            "Exemple : [{\"date_operation\": \"2026-03-01\", \"sens\": \"credit\", "
            "\"montant\": 12500.0, \"type_operation\": \"05\", "
            "\"categorie\": \"encaissement_client\", \"anomalie\": null}]"
        ),
        agent=agent,
    )
