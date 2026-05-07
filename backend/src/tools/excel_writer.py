"""Écriture dans la matrice Excel sans casser les formules — implémentation J4.

Règle absolue : load_workbook(keep_vba=True, data_only=False).
Ne jamais utiliser data_only=True (efface les formules SUMIF).
"""
from pathlib import Path


def update_base_client(
    xlsx_path: str | Path,
    facture_id: str,
    date_paiement: str,
    moyen_paiement: str,
) -> None:
    """Met à jour colonnes 14 (STATUT), 15 (DATE PAIEMENT), 16 (MOIS PAIEMENT), 17 (MOYEN)."""
    raise NotImplementedError("J4")


def append_frais_generaux(xlsx_path: str | Path, transaction) -> None:
    """Ajoute une ligne à l'onglet Frais Généraux."""
    raise NotImplementedError("J4")


def append_ndf(xlsx_path: str | Path, transaction) -> None:
    """Ajoute une ligne à l'onglet NdF."""
    raise NotImplementedError("J4")


def update_echeance_previsionnelle(
    xlsx_path: str | Path,
    facture_id: str,
    new_date: str,
) -> None:
    """Décale la colonne 13 (échéance prévisionnelle) — déclenche le recalcul SUMIF."""
    raise NotImplementedError("J4")
