"""Schémas Pydantic partagés entre agents."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Une ligne du relevé bancaire normalisée."""
    date_operation: date
    date_valeur: date
    libelle: str
    montant: Decimal
    sens: Literal["debit", "credit"]
    type_operation: str   # code court : 05, 06, 08, 11, 44, 62, 91
    reference: Optional[str] = None
    contrepartie: Optional[str] = None


class Invoice(BaseModel):
    """Une facture client ou sous-traitant (Base CLient / Base Sous-traitants)."""
    id: str
    client: str           # nom du client ou du sous-traitant
    montant_ht: Decimal
    montant_ttc: Decimal
    date_echeance: date
    statut: Literal["a payer", "paye", "litige"] = "a payer"
    date_paiement: Optional[date] = None
    moyen_paiement: Optional[str] = None


class FraisGeneraux(BaseModel):
    """Une ligne de l'onglet Frais Généraux."""
    mois: Optional[date] = None
    num_facture: Optional[str] = None
    date_facture: Optional[date] = None
    fournisseur: str
    montant_ht: Decimal
    montant_ttc: Decimal
    date_paiement: Optional[date] = None
    type_frais: Optional[str] = None


class NotesDeFrais(BaseModel):
    """Une ligne de l'onglet NdF."""
    mois: Optional[date] = None
    salarie: str
    montant: Decimal
    date_paiement: Optional[date] = None
    etat: Optional[str] = None


class Paie(BaseModel):
    """Une ligne agrégée de l'onglet Paies (une ligne par mois)."""
    mois: date
    montant_paye: Decimal
    charges_totales: Decimal
    cout_total: Decimal
    date_paiement: Optional[date] = None
    etat: Optional[str] = None


class TVAMois(BaseModel):
    """TVA pour un mois donné (onglet TVA)."""
    mois: date
    tva_collectee: Decimal = Decimal("0")
    tva_deductible_st: Decimal = Decimal("0")
    tva_deductible_fg: Decimal = Decimal("0")
    tva_due: Optional[Decimal] = None
    credit_tva: Optional[Decimal] = None
    tva_a_payer: Decimal = Decimal("0")


class PretInfo(BaseModel):
    """Informations sur le prêt (onglet Prêt)."""
    nom: str
    montant_initial: Decimal
    premiere_echeance: Optional[date] = None
    derniere_echeance: Optional[date] = None
    duree_mois: int = 0
    mensualite_remboursement: Decimal = Decimal("0")
    assurance_mensuelle: Decimal = Decimal("0")
    mensualite_totale: Decimal = Decimal("0")
    rembourse_a_date: Decimal = Decimal("0")
    reste_a_rembourser: Decimal = Decimal("0")


class BudgetTresoMois(BaseModel):
    """Budget de trésorerie pour un mois (onglet Budget de tréso)."""
    mois: date
    # Encaissements
    total_ca_ttc: Optional[Decimal] = None
    ca_reellement_encaisse: Optional[Decimal] = None
    # Sous-traitance
    total_st_ttc: Optional[Decimal] = None
    st_reellement_payes: Optional[Decimal] = None
    # Charges
    total_frais_generaux: Optional[Decimal] = None
    fg_reellement_payes: Optional[Decimal] = None
    notes_de_frais: Optional[Decimal] = None
    salaires_nets: Optional[Decimal] = None
    echeance_pret: Optional[Decimal] = None
    tva_a_payer: Optional[Decimal] = None
    # Totaux
    total_encaissements: Optional[Decimal] = None
    total_decaissements: Optional[Decimal] = None
    variation_tresorerie: Optional[Decimal] = None
    tresorerie_debut: Optional[Decimal] = None
    tresorerie_fin: Optional[Decimal] = None
    # Soldes banques
    solde_bpvf: Optional[Decimal] = None
    solde_hsbc: Optional[Decimal] = None
    solde_sg: Optional[Decimal] = None


class MatchResult(BaseModel):
    """Résultat d'un rapprochement transaction ↔ facture(s)."""
    transaction: Transaction
    factures: list[Invoice] = Field(default_factory=list)
    categorie: str = ""
    confiance: float = 0.0
    anomalies: list[str] = Field(default_factory=list)


class IngestedData(BaseModel):
    """Sortie complète de l'Agent Lecteur."""

    # ── Relevé bancaire ──────────────────────────────────────────────
    transactions: list[Transaction] = Field(default_factory=list)
    solde_initial: Decimal = Decimal("0")
    solde_final: Decimal = Decimal("0")

    # ── Base CLient ──────────────────────────────────────────────────
    factures_ouvertes: list[Invoice] = Field(default_factory=list)
    factures_payees: list[Invoice] = Field(default_factory=list)

    # ── Base Sous-traitants ──────────────────────────────────────────
    st_ouverts: list[Invoice] = Field(default_factory=list)
    st_payes: list[Invoice] = Field(default_factory=list)

    # ── Frais Généraux ───────────────────────────────────────────────
    frais_generaux: list[FraisGeneraux] = Field(default_factory=list)

    # ── Notes de Frais ───────────────────────────────────────────────
    notes_de_frais: list[NotesDeFrais] = Field(default_factory=list)

    # ── Paies ────────────────────────────────────────────────────────
    paies: list[Paie] = Field(default_factory=list)

    # ── TVA ──────────────────────────────────────────────────────────
    tva: list[TVAMois] = Field(default_factory=list)

    # ── Prêt ─────────────────────────────────────────────────────────
    pret: Optional[PretInfo] = None

    # ── Budget de tréso ──────────────────────────────────────────────
    budget_treso: list[BudgetTresoMois] = Field(default_factory=list)
