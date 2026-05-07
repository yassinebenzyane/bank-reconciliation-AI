"""Matching one-to-many factures par algorithme déterministe — implémentation J3.

Règle : le LLM ne calcule JAMAIS les combinaisons de factures.
C'est cet algo subset-sum qui trouve la combinaison exacte, le LLM valide/explique ensuite.
"""
from decimal import Decimal


def match_invoices_combination(
    amount: Decimal,
    client: str,
    open_invoices: list,
) -> list:
    """Trouve la combinaison de factures ouvertes dont la somme TTC = amount.

    Utilise la programmation dynamique (subset-sum) sur les montants TTC.
    Retourne la liste de factures correspondantes, ou [] si aucune combinaison trouvée.
    """
    raise NotImplementedError("J3")
