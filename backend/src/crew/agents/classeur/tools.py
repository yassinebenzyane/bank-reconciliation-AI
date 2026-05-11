import json
from crewai.tools import BaseTool
from pydantic import BaseModel

TYPE_OP_MAP: dict[str, tuple[str, str | None]] = {
    "05": ("encaissement_client", "credit"),
    "06": ("paiement_st",         "debit"),
    "08": ("prelevement",         "debit"),
    "11": ("note_de_frais",       "debit"),
    "44": ("international",       None),
    "62": ("frais_bancaires",     "debit"),
    "91": ("divers",              None),
}


class ClassifyInput(BaseModel):
    transactions_json: str


class ClassifyTransactionsTool(BaseTool):
    name: str = "classify_transactions"
    description: str = (
        "Classifie une liste de transactions bancaires selon leur code type_op. "
        "Entrée : JSON array avec champs date_operation, sens, montant, type_operation, libelle. "
        "Sortie : même array enrichi avec 'categorie' et 'anomalie'."
    )
    args_schema: type[BaseModel] = ClassifyInput

    def _run(self, transactions_json: str) -> str:
        transactions = json.loads(transactions_json)
        results = []
        for t in transactions:
            type_op = str(t.get("type_operation", "")).strip()
            if type_op in TYPE_OP_MAP:
                categorie, sens_attendu = TYPE_OP_MAP[type_op]
                anomalie = None
                if sens_attendu and t.get("sens") != sens_attendu:
                    anomalie = f"sens '{t.get('sens')}' inattendu pour type {type_op} (attendu: {sens_attendu})"
            else:
                categorie = "inconnu"
                anomalie = f"type_op '{type_op}' non reconnu dans la codification CIH/AWB"
            results.append({**t, "categorie": categorie, "anomalie": anomalie})
        return json.dumps(results, ensure_ascii=False, default=str)
