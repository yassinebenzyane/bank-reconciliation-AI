"""Subset-sum déterministe pour le matching factures ↔ virements bancaires.

Règle absolue : le LLM ne calcule JAMAIS les combinaisons.
Cet algo trouve la combinaison exacte — le LLM explique ensuite.
"""
from decimal import Decimal
from itertools import combinations
import logging

log = logging.getLogger(__name__)

# Mapping explicite libellé bancaire → nom client dans la Base CLient.
# Prioritaire sur le matching fuzzy — à compléter au fil des nouveaux clients.
CLIENT_ALIASES: dict[str, str] = {
    "ALTRAN PROTOTYPES AUTO": "ALTRAN TECHNOLOGIES",
    "CAPGEMINI ENGINEERING":  "CAPGEMINI R&D",
    "SEKISUI EUROPE B.V.":    "SEKISUI EUROPE",
    "AMETRA SAS":             "AMETRA",
}

_STOPWORDS = {"SAS", "SA", "SRL", "BV", "BVA", "NV", "SARL", "SNC", "SCI",
              "GROUP", "GROUPE", "EUROPE", "FRANCE", "TECHNOLOGIES", "ENGINEERING",
              "PROTOTYPES", "AUTO", "SERVICES", "SOLUTIONS", "CONSULTING", "INTERNATIONAL"}


def normalize_client(bank_label: str) -> str:
    """Résout le nom client bancaire vers le nom utilisé dans la Base CLient.

    Priorité : mapping explicite > nom brut (le fuzzy est appliqué en aval dans _client_matches).
    """
    upper = bank_label.upper().strip()
    for bank_name, base_name in CLIENT_ALIASES.items():
        if bank_name in upper:
            return base_name
    return bank_label


def _client_tokens(name: str) -> set[str]:
    words = name.upper().split()
    return {w for w in words if len(w) >= 3 and w not in _STOPWORDS and w.isalpha()}


def _client_matches(filter_name: str, candidate_name: str) -> bool:
    tokens_filter = _client_tokens(filter_name)
    tokens_candidate = _client_tokens(candidate_name)
    return bool(tokens_filter & tokens_candidate)


def match_invoices_combination(
    amount: float | Decimal,
    open_invoices: list[dict],
    tolerance: float = 1.0,
    client_filter: str | None = None,
) -> dict | None:
    """Trouve la combinaison de factures ouvertes dont la somme TTC ≈ amount.

    Algorithme : backtracking avec élagage (tri décroissant).
    Retourne un dict {factures, total, ecart} ou None si aucune combinaison.

    Args:
        amount:        Montant du virement bancaire.
        open_invoices: Liste de dicts avec clé 'montant_ttc' et 'client'.
        tolerance:     Écart maximal accepté en euros (défaut 1.0 €).
        client_filter: Si fourni, normalisé via CLIENT_ALIASES puis filtré fuzzy.
    """
    target = float(amount)

    candidates = open_invoices
    if client_filter:
        normalized = normalize_client(client_filter)
        filtered = [inv for inv in open_invoices
                    if _client_matches(normalized, str(inv.get("client") or ""))]
        if filtered:
            candidates = filtered

    log.debug("match %.2f€ | filtre=%s | %d candidats", target, client_filter, len(candidates))

    result = _find_combination(target, candidates, tolerance)
    if result is not None:
        return result

    # Retry sans filtre client si on avait filtré et rien trouvé
    if client_filter and candidates is not open_invoices:
        log.warning("Aucune combinaison pour %.2f€ avec filtre '%s' — retry sans filtre.", target, client_filter)
        return _find_combination(target, open_invoices, tolerance)

    return None


def _find_combination(target: float, invoices: list[dict], tolerance: float) -> dict | None:
    """Cherche la combinaison de factures dont la somme ≈ target (±tolerance).

    Pour ≤ 20 factures : énumération exhaustive via itertools.combinations (garanti).
    Pour > 20 factures : backtracking avec élagage et suffix sums.
    Tout calcul en centimes entiers pour éviter les erreurs de précision float.
    """
    target_cents    = round(target * 100)
    tolerance_cents = round(tolerance * 100)
    amounts_cents   = [round(float(inv.get("montant_ttc") or 0) * 100) for inv in invoices]
    n = len(amounts_cents)

    if n == 0:
        return None

    if n <= 20:
        # Énumération exhaustive — garanti pour n ≤ 20 (2^20 = 1 048 576, < 10ms)
        for size in range(1, n + 1):
            for combo in combinations(range(n), size):
                total_c = sum(amounts_cents[i] for i in combo)
                if abs(total_c - target_cents) <= tolerance_cents:
                    matched = [invoices[i] for i in combo]
                    total   = sum(float(inv.get("montant_ttc") or 0) for inv in matched)
                    return {
                        "factures": matched,
                        "total":    round(total, 2),
                        "ecart":    round(abs(total - target), 2),
                        "nb":       len(matched),
                    }
        return None

    # Backtracking pour grands sets (> 20 factures)
    sorted_inv  = sorted(invoices, key=lambda x: float(x.get("montant_ttc") or 0), reverse=True)
    s_amounts   = [round(float(inv.get("montant_ttc") or 0) * 100) for inv in sorted_inv]
    suffix      = [0] * (n + 1)
    for k in range(n - 1, -1, -1):
        suffix[k] = suffix[k + 1] + s_amounts[k]

    chosen: list[int] = []

    def backtrack(idx: int, remaining: int) -> bool:
        if abs(remaining) <= tolerance_cents:
            return True
        if idx >= n or remaining < -tolerance_cents:
            return False
        if suffix[idx] < remaining - tolerance_cents:
            return False
        chosen.append(idx)
        if backtrack(idx + 1, remaining - s_amounts[idx]):
            return True
        chosen.pop()
        return backtrack(idx + 1, remaining)

    if not backtrack(0, target_cents):
        return None

    matched = [sorted_inv[i] for i in chosen]
    total   = sum(float(inv.get("montant_ttc") or 0) for inv in matched)
    return {
        "factures": matched,
        "total":    round(total, 2),
        "ecart":    round(abs(total - target), 2),
        "nb":       len(matched),
    }
