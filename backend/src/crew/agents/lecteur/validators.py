"""Couche 3 — Validation déterministe. Zéro LLM."""
from __future__ import annotations
from datetime import date


def validate_bank_statement(data: list[dict]) -> list[str]:
    errors = []
    meta = next((d for d in data if d.get("_meta")), None)
    if meta and not meta.get("balance_ok"):
        errors.append(f"Balance bancaire KO : écart = {meta['balance_ecart']:.2f} €")
    transactions = [d for d in data if not d.get("_meta")]
    for t in transactions:
        if not t.get("montant") or t["montant"] <= 0:
            errors.append(f"Transaction {t.get('date_operation')} : montant invalide")
        if not t.get("sens") in ("debit", "credit"):
            errors.append(f"Transaction {t.get('date_operation')} : sens invalide")
    return errors


def validate_invoices(data: list[dict], sheet: str) -> list[str]:
    errors = []
    seen_ids = set()
    for row in data:
        facture_id = row.get("n_facture")

        # Doublon strict : même ID ET même statut_ligne (Réel+Prévisionnel du même ID = normal)
        statut_l = row.get("statut_ligne", "")
        key = (facture_id, statut_l)
        if facture_id and key in seen_ids:
            errors.append(f"{sheet} : doublon facture {facture_id} (statut={statut_l})")
        if facture_id:
            seen_ids.add(key)

        # TTC >= HT (sur valeurs absolues — les avoirs sont négatifs)
        ttc = row.get("montant_ttc")
        ht  = row.get("montant_ht")
        if ttc is not None and ht is not None and ht != 0:
            if abs(float(ttc)) < abs(float(ht)) - 0.01:
                errors.append(f"{sheet} {facture_id} : |TTC| ({abs(ttc):.2f}) < |HT| ({abs(ht):.2f})")

        # Dates cohérentes
        for field in ("date_facturation", "date_paiement", "echeance_previsionnelle"):
            d = row.get(field)
            if d and isinstance(d, date):
                if not (date(2015, 1, 1) <= d <= date(2030, 12, 31)):
                    errors.append(f"{sheet} {facture_id} : {field} hors plage ({d})")

        # Facture payée sans col P (mois_paiement) → SUMIF ne captera pas
        if row.get("statut_normalise") == "paye" and not row.get("mois_paiement"):
            errors.append(
                f"{sheet} {facture_id} : statut=payé mais mois_paiement (col P) vide "
                f"→ SUMIF Budget ne captera pas le montant"
            )

    return errors


def validate_budget(data: list[dict]) -> list[str]:
    errors = []
    for entry in data:
        mois = entry.get("mois", "?")
        v = entry.get("values", {})

        enc = v.get("total_encaissements")
        dec = v.get("total_decaissements")
        var = v.get("variation_tresorerie")

        # Variation = enc - dec
        if None not in (enc, dec, var):
            expected = round(enc - dec, 2)
            if abs(expected - var) > 1.0:
                errors.append(
                    f"Budget {mois} : variation {var:.2f} ≠ {enc:.2f} - {dec:.2f} = {expected:.2f}"
                )

        # Total banques = BPVF + HSBC + SG
        total = v.get("total_banques")
        bpvf  = v.get("solde_bpvf") or 0
        hsbc  = v.get("solde_hsbc") or 0
        sg    = v.get("solde_sg") or 0
        if total is not None and abs(total - (bpvf + hsbc + sg)) > 1.0:
            errors.append(
                f"Budget {mois} : total_banques {total:.2f} ≠ "
                f"BPVF {bpvf:.2f} + HSBC {hsbc:.2f} + SG {sg:.2f}"
            )

    return errors


def validate_all(parsed: dict) -> dict[str, list[str]]:
    report: dict[str, list[str]] = {}

    if "releve_bancaire" in parsed:
        e = validate_bank_statement(parsed["releve_bancaire"])
        if e:
            report["releve_bancaire"] = e

    for sheet in ("Base CLient", "Base Sous-traitants"):
        if sheet in parsed:
            e = validate_invoices(parsed[sheet], sheet)
            if e:
                report[sheet] = e

    if "Budget de tréso" in parsed:
        e = validate_budget(parsed["Budget de tréso"])
        if e:
            report["Budget de tréso"] = e

    return report
