from crewai import Agent, Task


def make_lecteur_task(agent: Agent, xlsx_path: str, csv_path: str | None = None) -> Task:
    steps = []
    if csv_path:
        steps.append(f"1. Appelle parse_csv_bancaire avec path='{csv_path}'")
        steps.append(f"2. Appelle parse_excel_matrice avec path='{xlsx_path}'")
        steps.append("3. Confirme le nombre de transactions CSV et le nombre de lignes par onglet Excel.")
    else:
        steps.append(f"1. Appelle parse_excel_matrice avec path='{xlsx_path}'")
        steps.append("2. Confirme le nombre de lignes par onglet Excel.")

    return Task(
        description=(
            "Ingère les fichiers financiers ECO Steering :\n"
            + (f"- Relevé bancaire : {csv_path}\n" if csv_path else "")
            + f"- Matrice Excel   : {xlsx_path}\n\n"
            + "\n".join(steps)
        ),
        expected_output=(
            "Un rapport de parsing avec pour chaque source :\n"
            "- Nombre de lignes extraites par onglet\n"
            "- Anomalies détectées (lignes vides, types inconnus, etc.)\n"
            "- Confirmation que le parsing s'est terminé sans erreur critique"
        ),
        agent=agent,
    )
