"""Configuration explicite de tous les parsers — positions de colonnes hardcodées.

Basé sur l'audit structurel de la matrice ECO Steering (Claude Excel, avril 2026).
Toute modification de structure Excel doit forcer une mise à jour ici.
"""
from __future__ import annotations


def col(letter: str) -> int:
    """Convertit une lettre Excel en index 0-based. A=0, Z=25, AA=26..."""
    result = 0
    for c in letter.upper():
        result = result * 26 + (ord(c) - ord("A") + 1)
    return result - 1


# ── Tableaux relationnels ─────────────────────────────────────────────────────

TABLE_CONFIGS: dict[str, dict] = {
    "Base CLient": {
        "header_row": 3,
        "data_start": 4,
        "columns": {
            "statut_ligne":              col("A"),
            "date_facturation":          col("B"),
            "mois_facturation":          col("C"),
            "n_facture":                 col("D"),
            "projet":                    col("E"),
            "sous_traitant_affecte":     col("F"),
            "mois_prestation":           col("G"),
            "n_contrat":                 col("H"),
            "client":                    col("I"),
            "montant_ttc":               col("J"),
            "montant_ht":                col("K"),
            "date_reglement":            col("L"),
            "echeance_previsionnelle":   col("M"),
            "statut_paiement":           col("N"),
            "date_paiement":             col("O"),   # date réelle du virement
            "mois_paiement":             col("P"),   # serial du 1er du mois — clé SUMIF
            "moyen_paiement":            col("Q"),
            "reference_paiement":        col("R"),
            "cir":                       col("S"),
            "observations":              col("T"),
        },
        "date_columns":   ["date_facturation", "mois_facturation",
                           "date_reglement", "echeance_previsionnelle",
                           "date_paiement", "mois_paiement"],
        "amount_columns": ["montant_ttc", "montant_ht"],
        "required":       ["n_facture", "client", "montant_ttc"],
        "statut_ouvert":  {"a payer", "à payer", "chq à débiter", "chq a debiter"},
        "statut_paye":    {"payé", "paye"},
        # Col A : toutes les valeurs réelles (Réel + variantes FAE historiques)
        "statut_ligne_reel": {
            "réel", "reel", "fae2017", "fae2018", "fae2019",
            "fae2021", "fae2022", "fae 2017", "fae 2018",
            "fae 2019", "fae 2021", "fae 2022",
        },
        # Colonnes à écrire lors du pointage (Agent Écrivain)
        "pointage_statut_col": col("N"),   # "payé"
        "pointage_date_col":   col("O"),   # date réelle virement
        "pointage_mois_col":   col("P"),   # serial 1er du mois
    },

    "Base Sous-traitants": {
        "header_row": 3,
        "data_start": 4,
        "columns": {
            "statut_ligne":              col("A"),
            "date_facturation":          col("B"),
            "mois_facturation":          col("C"),
            "n_facture":                 col("D"),
            "projet":                    col("E"),
            "mois_prestation":           col("F"),
            "n_contrat":                 col("G"),
            "n_devis":                   col("H"),
            "client":                    col("I"),
            "montant_ttc":               col("J"),
            "montant_ht":                col("K"),
            "echeance_previsionnelle":   col("M"),
            "statut_paiement":           col("N"),
            "date_paiement":             col("O"),
            "mois_paiement":             col("P"),
            "moyen_paiement":            col("Q"),
        },
        "date_columns":   ["date_facturation", "mois_facturation",
                           "echeance_previsionnelle", "date_paiement", "mois_paiement"],
        "amount_columns": ["montant_ttc", "montant_ht"],
        "required":       ["n_facture", "client", "montant_ttc"],
        "statut_ouvert":  {"a payer", "à payer", "chq à débiter", "chq a debiter"},
        "statut_paye":    {"payé", "paye"},
        "statut_ligne_reel": {"réel", "reel"},
        "pointage_statut_col": col("N"),
        "pointage_date_col":   col("O"),
        "pointage_mois_col":   col("P"),
    },

    "Frais Généraux": {
        "header_row": 3,
        "data_start": 4,
        "columns": {
            "mois":           col("A"),
            "num_facture":    col("B"),
            "date_facture":   col("C"),
            "fournisseur":    col("D"),
            "montant_ht":     col("E"),
            "tx_tva":         col("F"),
            "montant_ttc":    col("G"),
            "mois_paiement_prev": col("H"),
            "date_paiement":  col("I"),   # col J pour pointage SUMIF budget
            "mois_paiement":  col("J"),   # serial 1er du mois → SUMIF Budget L38
            "type_frais":     col("K"),
        },
        "date_columns":   ["mois", "date_facture", "date_paiement", "mois_paiement"],
        "amount_columns": ["montant_ht", "montant_ttc"],
        "required":       ["fournisseur"],
        "skip_values":    {"reel", "réel", "total"},
        "pointage_mois_col": col("J"),    # clé SUMIF Budget row 38
    },

    "NdF": {
        "header_row": 3,
        "data_start": 4,
        "columns": {
            "mois":           col("A"),
            "salarie":        col("B"),   # champ libre mixte → Tâche A LLM
            "montant":        col("C"),
            "date_paiement":  col("D"),
            "mois_paiement":  col("E"),   # serial → SUMIF Budget row 39
            "etat":           col("F"),
            "observation":    col("G"),
        },
        "date_columns":   ["mois", "date_paiement", "mois_paiement"],
        "amount_columns": ["montant"],
        "required":       ["salarie"],
        "llm_decode_col": "salarie",      # Tâche A : décodage champ libre
    },

    "Paies": {
        "header_row": 2,
        "data_start": 3,
        "columns": {
            "mois":             col("A"),
            "montant_paye":     col("J"),
            "charges_totales":  col("O"),
            "cout_total":       col("Q"),
            "date_paiement":    col("R"),   # serial → SUMIF Budget row 40
            "etat":             col("S"),
        },
        "date_columns":   ["mois", "date_paiement"],
        "amount_columns": ["montant_paye", "charges_totales", "cout_total"],
        "required":       ["mois"],
        "pointage_mois_col": col("R"),    # clé SUMIF Budget row 40
    },
}

# ── Matrices temporelles ──────────────────────────────────────────────────────

MATRIX_CONFIGS: dict[str, dict] = {
    "Budget de tréso": {
        "date_row":       13,    # row 13 contient des serials Excel (int)
        "label_col":       0,    # col A = libellé
        "data_start_col":  1,    # col B = premier mois (jan 2016)

        # Lignes à LIRE (toutes sont des formules SUMIF sauf 44, 51, 79-81)
        "key_rows": {
            15: "total_ca_ttc",
            16: "ca_previsionnel",
            21: "ca_reellement_encaisse",       # SUMIF Base CLient col P
            33: "total_st_ttc",
            34: "st_previsionnel",
            35: "st_reellement_payes",           # SUMIF Base ST col P
            36: "total_frais_generaux",
            37: "fg_previsionnel",
            38: "fg_reellement_payes",           # SUMIF Frais Généraux col J
            39: "notes_de_frais",               # SUMIF NdF col E
            40: "salaires_nets",                # SUMIF Paies col R
            44: "echeance_pret",                # MANUELLE ← écrire ici
            48: "total_autres_decaissements",
            51: "regule_urssaf",                # MANUELLE ← écrire ici
            63: "tva_a_payer",                  # =TVA!DT14
            72: "total_encaissements",
            73: "total_decaissements",
            74: "variation_tresorerie",
            76: "tresorerie_debut",             # =mois_precedent.tresorerie_fin
            77: "tresorerie_fin",               # =debut + variation
            78: "total_banques",               # =BPVF+HSBC+SG
            79: "solde_bpvf",                  # MANUELLE ← écrire ici
            80: "solde_hsbc",                  # MANUELLE ← écrire ici
            81: "solde_sg",                    # MANUELLE ← écrire ici
        },

        # Lignes écrivables par l'Agent Écrivain (les autres sont des formules)
        "writable_rows": {44, 51, 79, 80, 81},

        # Validation : row 74 = row 72 - row 73
        "check_variation": (74, 72, 73),
        # Validation : row 78 = row 79 + row 80 + row 81
        "check_banques": (78, 79, 80, 81),
    },

    "TVA": {
        "date_row":       1,     # row 1 contient les serials (même structure)
        "label_col":      0,
        "data_start_col": 1,
        # Toutes sont des formules sauf row 10 (cumul manuel)
        "key_rows": {
            2:  "tva_collectee",           # ='Budget de tréso'!DT15/1.2*20%
            3:  "tva_deductible_st",       # ='Budget de tréso'!DT33/1.2*20%
            4:  "tva_deductible_fg",       # ='Budget de tréso'!DT36/1.2*20%
            5:  "tva_deductible_totale",
            7:  "tva_due",
            8:  "credit_tva",
            10: "cumul",                   # MANUELLE
            13: "encaissement_tva",
            14: "decaissement_tva",        # → Budget de tréso row 63
        },
        "writable_rows": {10},
    },
}

# ── Prêt (clé/valeur) ─────────────────────────────────────────────────────────

PRET_CONFIG = {
    "label_col": 0,   # col A = label (ex: "PGE ECO STEERING")
    "value_col": 1,   # col B = valeur numérique
    "nom_from_label_row": 1,   # le nom du prêt est dans col A de la ligne 1
    "rows": {
        1:  ("montant_initial",        "decimal"),  # col B = 100000
        2:  ("premiere_echeance",      "date"),
        3:  ("derniere_echeance",      "date"),
        4:  ("duree_mois",             "int"),
        5:  ("mensualite_remboursement","decimal"),
        6:  ("assurance_mensuelle",    "decimal"),
        7:  ("mensualite_totale",      "decimal"),
        8:  ("total_remb_ht_assurance","decimal"),
        9:  ("total_remb_avec_assurance","decimal"),
        11: ("rembourse_a_date",       "decimal"),
        12: ("reste_a_rembourser",     "decimal"),
    },
    # B1 = montant initial du prêt
    "montant_initial_col": 1,
    "montant_initial_row": 1,
}

# ── CSV bancaire ──────────────────────────────────────────────────────────────

BANK_CSV_CONFIG = {
    "BPVF": {
        "encoding":    "windows-1252",
        "separator":   ";",
        "data_start":  8,           # données à partir de la ligne 9 (index 8)
        "columns": {
            "date_operation": 2,
            "reference":      4,
            "libelle":        7,
            "date_valeur":    11,
            "type_operation": 14,
            "debit":          17,
            "credit":         22,
        },
        # Solde : ligne contenant "Solde" dans col[9]
        "solde_col_9_label": "Solde",
        "solde_initial_col": 18,    # col[18] pour le solde initial
        "solde_final_col":   19,    # col[19] pour le solde final (différent !)
        # Nettoyage des montants : \xa0 = séparateur de milliers, virgule = décimale
        "amount_cleanup": [("\xa0", ""), (" ", ""), (",", "."), ("€", "")],
    },
}

# ── Cache semantic ────────────────────────────────────────────────────────────

import os
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
LABEL_CACHE_FILE = os.path.join(CACHE_DIR, "budget_labels_v1.json")
