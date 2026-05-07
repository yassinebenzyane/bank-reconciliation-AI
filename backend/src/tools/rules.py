"""Règles déterministes de classification par Type d'opération — implémentation J3.

Priorité : ces règles s'appliquent AVANT tout appel LLM.
Signal le plus fiable : colonne 'Type d'opération' du CSV (codifié).
"""


RULES: list[dict] = [
    # (type_op, mot_clé_libelle, categorie)
    {"type_op": "08", "keyword": "URSSAF", "categorie": "Charges sociales"},
    {"type_op": "08", "keyword": "DGFIP", "categorie": "TVA"},
    {"type_op": "91", "keyword": "ECHEANCE PRET", "categorie": "Remboursement prêt"},
    {"type_op": "44", "keyword": None, "categorie": "Sous-traitance"},  # + bénéficiaire connu
    {"type_op": "06", "keyword": "MALAKOFF", "categorie": "Retraite complémentaire"},
    {"type_op": "06", "keyword": None, "categorie": "Encaissement client"},  # + client connu
    {"type_op": "62", "keyword": None, "categorie": "Frais bancaires"},
    {"type_op": "11", "keyword": None, "categorie": "Chèque"},
]


def apply_rules(transaction) -> str | None:
    """Retourne la catégorie si une règle déterministe s'applique, sinon None (→ LLM).

    J3 : implémenter la logique de correspondance.
    """
    raise NotImplementedError("J3")
