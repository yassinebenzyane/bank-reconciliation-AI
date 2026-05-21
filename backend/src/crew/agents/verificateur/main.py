"""Agent Vérificateur — rapprochement encaissements ↔ factures ouvertes."""
import json
import logging
from crewai import Crew, Process

from src.tools.matching import match_invoices_combination, normalize_client
from .agent import build_verificateur_agent
from .task import make_verificateur_task

log = logging.getLogger(__name__)


def extract_clients(encaissements: list[dict]) -> dict[int, str]:
    """Extrait les noms clients depuis les libellés (un seul appel LLM batch)."""
    return _extract_clients_batch(encaissements)


def run_one(txn: dict, factures_remaining: list[dict], client_name: str) -> dict:
    """Rapproche un encaissement. Retourne statut: match_exact | ambigu | pas_de_match.

    match_exact  → une seule combinaison trouvée, factures_ids rempli
    ambigu       → plusieurs combinaisons possibles, options[] rempli pour demander au comptable
    pas_de_match → aucune combinaison
    """
    from src.tools.matching import find_all_combinations

    amount      = float(txn.get("montant") or 0)
    all_matches = find_all_combinations(amount, factures_remaining, client_filter=client_name)

    if not all_matches:
        return {
            "statut":      "pas_de_match",
            "client":      client_name,
            "montant":     amount,
            "factures_ids": [],
            "total":       0.0,
            "ecart":       amount,
            "options":     [],
        }
    if len(all_matches) == 1:
        m = all_matches[0]
        return {
            "statut":      "match_exact",
            "client":      client_name,
            "montant":     amount,
            "factures_ids": [f.get("id") for f in m["factures"]],
            "total":       m["total"],
            "ecart":       m["ecart"],
            "options":     [],
        }
    return {
        "statut":      "ambigu",
        "client":      client_name,
        "montant":     amount,
        "factures_ids": [],
        "total":       0.0,
        "ecart":       0.0,
        "options": [
            {
                "factures_ids": [f.get("id") for f in m["factures"]],
                "factures":     m["factures"],
                "total":        m["total"],
                "ecart":        m["ecart"],
            }
            for m in all_matches
        ],
    }


def run(encaissements: list[dict], factures_ouvertes: list[dict]) -> list[dict]:
    """Rapproche chaque encaissement client avec les factures ouvertes.

    Stratégie rapide :
    1. Extraction des noms clients via un seul appel LLM léger (batch)
    2. Subset-sum déterministe par client (< 1s)
    """
    if not encaissements or not factures_ouvertes:
        return []

    # Étape 1 : extraction batch des noms clients (un seul appel LLM)
    client_names = _extract_clients_batch(encaissements)

    # Étape 2 : subset-sum déterministe pour chaque encaissement
    # Les factures déjà matchées sont exclues du pool pour les encaissements suivants.
    matched_ids: set[str] = set()
    results = []
    for i, txn in enumerate(encaissements):
        amount    = float(txn.get("montant") or 0)
        client    = normalize_client(client_names.get(i, _extract_client_heuristic(str(txn.get("libelle") or ""))))
        remaining = [f for f in factures_ouvertes if str(f.get("id") or "") not in matched_ids]
        match     = match_invoices_combination(amount, remaining, client_filter=client)

        if match:
            matched_ids |= {str(f.get("id") or "") for f in match["factures"]}
            results.append({
                "idx":          i,
                "transaction":  txn,
                "client":       client,
                "montant":      amount,
                "factures_ids": [f.get("id") for f in match["factures"]],
                "total":        match["total"],
                "ecart":        match["ecart"],
                "statut":       "match_exact",
            })
        else:
            results.append({
                "idx":          i,
                "transaction":  txn,
                "client":       client,
                "montant":      amount,
                "factures_ids": [],
                "total":        0.0,
                "ecart":        amount,
                "statut":       "pas_de_match",
            })

    exact = sum(1 for r in results if r["statut"] == "match_exact")
    log.info("Vérificateur : %d/%d encaissements rapprochés.", exact, len(results))
    return results


def _extract_clients_batch(encaissements: list[dict]) -> dict[int, str]:
    """Extrait les noms clients depuis les libellés via un seul appel LLM."""
    import os
    from openai import OpenAI

    libelles = [
        {"idx": i, "libelle": str(t.get("libelle") or "")[:80]}
        for i, t in enumerate(encaissements)
    ]
    prompt = (
        "Extrais le nom du client payeur depuis chaque libellé de virement bancaire.\n"
        "Retourne UNIQUEMENT un JSON array : [{\"idx\": 0, \"client\": \"NOM\"}, ...]\n\n"
        f"Libellés :\n{json.dumps(libelles, ensure_ascii=False)}"
    )
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = resp.choices[0].message.content or ""
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        if start != -1 and end > start:
            parsed = json.loads(raw[start:end])
            return {item["idx"]: item["client"] for item in parsed if "idx" in item}
    except Exception as e:
        log.warning("Vérificateur : extraction clients LLM échouée (%s) — heuristique.", e)

    return {
        i: _extract_client_heuristic(str(t.get("libelle") or ""))
        for i, t in enumerate(encaissements)
    }


def _fallback(encaissements: list[dict], factures_ouvertes: list[dict]) -> list[dict]:
    """Fallback : subset-sum déterministe sans extraction LLM du client."""
    log.info("Vérificateur : fallback déterministe sur %d encaissements.", len(encaissements))
    results = []
    for i, txn in enumerate(encaissements):
        amount  = float(txn.get("montant") or 0)
        libelle = str(txn.get("libelle") or "")
        match   = match_invoices_combination(amount, factures_ouvertes, client_filter=None)

        if match:
            results.append({
                "idx":          i,
                "transaction":  txn,
                "client":       _extract_client_heuristic(libelle),
                "montant":      amount,
                "factures_ids": [f.get("id") for f in match["factures"]],
                "total":        match["total"],
                "ecart":        match["ecart"],
                "statut":       "match_exact",
            })
        else:
            results.append({
                "idx":          i,
                "transaction":  txn,
                "client":       _extract_client_heuristic(libelle),
                "montant":      amount,
                "factures_ids": [],
                "total":        0.0,
                "ecart":        amount,
                "statut":       "pas_de_match",
            })
    return results


def _extract_client_heuristic(libelle: str) -> str:
    """Extraction simple du client depuis le libellé (mots en majuscules)."""
    mots = [w for w in libelle.upper().split() if len(w) > 3 and w.isalpha()]
    stopwords = {"VIREMENT", "VIRMT", "VIRT", "VERS", "POUR", "PAIEMENT", "FACTURE"}
    mots_filtres = [m for m in mots if m not in stopwords]
    return " ".join(mots_filtres[:3]) if mots_filtres else libelle[:20]
