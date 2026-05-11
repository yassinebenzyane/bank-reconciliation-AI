import json
import logging
from crewai import Crew, Process
from .agent import build_classeur_agent
from .task import make_classeur_task
from .tools import ClassifyTransactionsTool

log = logging.getLogger(__name__)


def run(transactions: list[dict]) -> list[dict]:
    """Classifie les transactions.

    Stratégie rapide : outil déterministe d'abord (< 1s),
    puis LLM CrewAI uniquement pour les transactions avec categorie='inconnu'.
    """
    if not transactions:
        return []

    # Étape 1 : classification déterministe instantanée
    tool = ClassifyTransactionsTool()
    classified = json.loads(tool._run(json.dumps(transactions, default=str)))

    inconnus = [t for t in classified if t.get("categorie") == "inconnu"]
    if not inconnus:
        log.info("Classeur : %d transactions classifiées (100%% déterministe).", len(classified))
        return classified

    # Étape 2 : LLM uniquement pour les cas inconnus
    log.info("Classeur : %d cas inconnus → LLM.", len(inconnus))
    try:
        agent = build_classeur_agent()
        task  = make_classeur_task(agent, inconnus)
        crew  = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()

        raw   = str(result).strip()
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        if start != -1 and end > start:
            resolved = json.loads(raw[start:end])
            if isinstance(resolved, list) and len(resolved) == len(inconnus):
                # Remplacer les inconnus dans la liste classifiée
                inconnu_map = {t.get("date_operation", "") + str(t.get("montant", "")): t
                               for t in resolved}
                for t in classified:
                    if t.get("categorie") == "inconnu":
                        key = t.get("date_operation", "") + str(t.get("montant", ""))
                        if key in inconnu_map:
                            t["categorie"] = inconnu_map[key].get("categorie", "inconnu")
    except Exception as e:
        log.warning("Classeur : LLM pour inconnus échoué (%s) — conserve 'inconnu'.", e)

    log.info("Classeur : %d transactions classifiées.", len(classified))
    return classified
