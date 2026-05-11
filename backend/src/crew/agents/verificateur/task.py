import json
from crewai import Agent, Task


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
    factures_json = json.dumps(
        [{"id": f.get("id"), "client": str(f.get("client") or ""),
          "montant_ttc": float(f.get("montant_ttc") or 0)}
         for f in factures_ouvertes],
        ensure_ascii=False,
    )

    return Task(
        description=(
            f"Rapproche les {len(encaissements)} encaissements clients suivants "
            f"avec les {len(factures_ouvertes)} factures ouvertes.\n\n"
            f"Encaissements à traiter :\n{json.dumps(enc_summary, ensure_ascii=False)}\n\n"
            f"Factures ouvertes :\n{factures_json}\n\n"
            "Pour chaque encaissement :\n"
            "1. Lis le libellé et identifie le nom du client payeur.\n"
            "2. Appelle match_invoices_subset_sum avec le montant, "
            "   les factures JSON ci-dessus, et le client_filter extrait du libellé.\n"
            "3. Note le résultat : factures matchées, total, écart.\n\n"
            "Retourne UNIQUEMENT un JSON array :\n"
            "[{\"idx\": 0, \"client\": \"NOM\", \"montant\": 53346.0, "
            "\"factures_ids\": [\"FC1183\", ...], \"total\": 53346.0, "
            "\"ecart\": 0.0, \"statut\": \"match_exact\"}, ...]"
        ),
        expected_output=(
            "JSON array, un objet par encaissement avec :\n"
            "- idx : index de l'encaissement\n"
            "- client : nom extrait du libellé\n"
            "- montant : montant du virement\n"
            "- factures_ids : liste des N° factures matchées ([] si pas de match)\n"
            "- total : somme des factures matchées\n"
            "- ecart : différence en euros\n"
            "- statut : 'match_exact' | 'pas_de_match'"
        ),
        agent=agent,
    )
