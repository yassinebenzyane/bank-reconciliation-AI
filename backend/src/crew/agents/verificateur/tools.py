import json
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.tools.matching import match_invoices_combination


class MatchInput(BaseModel):
    amount: float
    invoices_json: str
    client_filter: str = ""


class MatchInvoicesTool(BaseTool):
    name: str = "match_invoices_subset_sum"
    description: str = (
        "Trouve la combinaison de factures ouvertes dont la somme TTC correspond "
        "au montant d'un virement bancaire (tolérance ±1 €). "
        "Entrée : montant du virement (float), JSON array des factures ouvertes "
        "(chaque facture avec 'id', 'client', 'montant_ttc'), "
        "et optionnellement un filtre client (string). "
        "Retourne la combinaison trouvée ou null."
    )
    args_schema: type[BaseModel] = MatchInput

    def _run(self, amount: float, invoices_json: str, client_filter: str = "") -> str:
        invoices = json.loads(invoices_json)
        result = match_invoices_combination(
            amount=amount,
            open_invoices=invoices,
            client_filter=client_filter or None,
        )
        if result is None:
            return json.dumps({"match": None, "message": "Aucune combinaison trouvée."})
        return json.dumps({
            "match": {
                "factures":    result["factures"],
                "total":       result["total"],
                "ecart":       result["ecart"],
                "nb_factures": result["nb"],
            }
        }, ensure_ascii=False, default=str)
