"""Point d'entrée FastAPI — Rapprochement Bancaire ECO Steering."""
import asyncio
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

app = FastAPI(
    title="Rapprochement Bancaire API",
    description="Backend multi-agents CrewAI pour ECO Steering",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(os.getenv("DATA_INPUT_DIR", "data/input"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    csv_filename: str | None = None
    xlsx_filename: str | None = None


class UploadResponse(BaseModel):
    session_id: str
    csv_filename: str | None = None
    xlsx_filename: str | None = None
    message: str


sessions: dict[str, dict] = {}


def _sse(text: str) -> str:
    return f"data: {json.dumps({'delta': text})}\n\n"

def _sse_progress(text: str) -> str:
    # Heartbeat SSE — ignoré par le frontend (pas de clé 'delta')
    return f"data: {json.dumps({'progress': text})}\n\n"

def _sse_done() -> str:
    return f"data: {json.dumps({'done': True})}\n\n"

async def _stream_text(text: str) -> AsyncGenerator[str, None]:
    words = text.split(" ")
    for i, word in enumerate(words):
        yield _sse(word + (" " if i < len(words) - 1 else ""))
        await asyncio.sleep(0.01)


def _run_parse(csv_path: str | None, xlsx_path: str | None) -> dict:
    """Orchestre l'Agent Lecteur : parsers Python + validation."""
    from src.crew.agents.lecteur.main import run as lecteur_run

    raw = lecteur_run(
        xlsx_path=xlsx_path or "",
        csv_path=csv_path,
        use_semantic=False,
    )
    result = {}

    if csv_path:
        releve  = raw.get("releve_bancaire", [])
        meta_r  = next((r for r in releve if r.get("_meta")), {})
        txns    = [r for r in releve if not r.get("_meta")]
        debits  = sum(r["montant"] for r in txns if r.get("sens") == "debit")
        credits = sum(r["montant"] for r in txns if r.get("sens") == "credit")
        types: dict[str, int] = {}
        for t in txns:
            k = t.get("type_operation", "??")
            types[k] = types.get(k, 0) + 1
        result["csv"] = {
            "nb_transactions": len(txns),
            "solde_initial":   meta_r.get("solde_initial", 0),
            "solde_final":     meta_r.get("solde_final", 0),
            "total_debits":    float(debits),
            "total_credits":   float(credits),
            "types":           types,
            "transactions":    txns,
        }

    if xlsx_path:
        base_client = raw.get("Base CLient", [])
        ouvertes    = [r for r in base_client if r.get("statut_normalise") == "ouvert"]
        payees      = [r for r in base_client if r.get("statut_normalise") == "paye"]
        clients     = sorted({str(r.get("client") or "") for r in ouvertes if r.get("client")})

        base_st    = raw.get("Base Sous-traitants", [])
        st_ouverts = [r for r in base_st if r.get("statut_normalise") == "ouvert"]
        st_payes   = [r for r in base_st if r.get("statut_normalise") == "paye"]
        sous_traitants = sorted({str(r.get("client") or "") for r in st_ouverts if r.get("client")})

        tva_flat = [
            {"mois": e["mois"], **e["values"]}
            for e in raw.get("TVA", [])
        ]

        budget_flat = [
            {"mois": e["mois"], **e["values"]}
            for e in raw.get("Budget de tréso", [])
        ]

        pret = raw.get("Prêt") or {}
        pret_dict = {
            "nom":                      pret.get("nom", ""),
            "montant_initial":          float(pret.get("montant_initial") or 0),
            "mensualite_totale":        float(pret.get("mensualite_totale") or 0),
            "mensualite_remboursement": float(pret.get("mensualite_remboursement") or 0),
            "assurance_mensuelle":      float(pret.get("assurance_mensuelle") or 0),
            "rembourse_a_date":         float(pret.get("rembourse_a_date") or 0),
            "reste_a_rembourser":       float(pret.get("reste_a_rembourser") or 0),
            "derniere_echeance":        str(pret.get("derniere_echeance") or ""),
        } if pret else None

        result["xlsx"] = {
            "nb_ouvertes":     len(ouvertes),
            "nb_payees":       len(payees),
            "total_ouvert":    sum(float(r.get("montant_ttc") or 0) for r in ouvertes),
            "clients":         clients,
            "factures": [
                {"id": r.get("n_facture"), "client": r.get("client"),
                 "montant_ttc": float(r.get("montant_ttc") or 0),
                 "date_echeance": str(r.get("echeance_previsionnelle") or "")}
                for r in ouvertes
            ],
            "nb_st_ouverts":   len(st_ouverts),
            "nb_st_payes":     len(st_payes),
            "total_st_ouvert": sum(float(r.get("montant_ttc") or 0) for r in st_ouverts),
            "sous_traitants":  sous_traitants,
            "st_ouverts": [
                {"id": r.get("n_facture"), "client": r.get("client"),
                 "montant_ttc": float(r.get("montant_ttc") or 0)}
                for r in st_ouverts
            ],
            "nb_fg":           len(raw.get("Frais Généraux", [])),
            "nb_ndf":          len(raw.get("NdF", [])),
            "nb_paies":        len(raw.get("Paies", [])),
            "tva":             tva_flat,
            "pret":            pret_dict,
            "budget_treso":    budget_flat,
        }

    return result


def _format_parse_report(parsed: dict) -> str:
    lines = []

    if "csv" in parsed:
        c = parsed["csv"]
        method_tag = " *(LLM)*" if c.get("_meta", {}).get("method") == "llm_generated" else ""
        si, sf = c["solde_initial"], c["solde_final"]
        ecart = abs(si + c["total_credits"] - c["total_debits"] - sf)
        balance_ok = ecart <= 1.0
        balance_line = (
            f"**{'✅' if balance_ok else '❌'} Balance** : "
            f"{si:,.2f} + {c['total_credits']:,.2f} − {c['total_debits']:,.2f} = {sf:,.2f} € "
            f"(écart = {ecart:.2f} €)"
        )
        type_labels = {
            "05": "Vir. reçu clients", "06": "Vir. émis ST",
            "08": "Prélèvements", "11": "Carte / NdF",
            "44": "Transferts internationaux", "62": "Frais bancaires", "91": "Divers",
        }
        lines += [
            f"## Relevé bancaire{method_tag}",
            "",
            f"**{c['nb_transactions']} transactions** extraites",
            "",
            "| Solde initial | Solde final | Débits | Crédits |",
            "|---|---|---|---|",
            f"| {si:,.2f} € | {sf:,.2f} € | {c['total_debits']:,.2f} € | {c['total_credits']:,.2f} € |",
            "",
            balance_line,
            "",
            "**Types d'opération :**",
        ]
        for code, count in sorted(c["types"].items()):
            lines.append(f"- `{code}` {type_labels.get(code, '')} : **{count}**")

        txns = c.get("transactions", [])
        if txns:
            lines += ["", "**Aperçu (5 premières transactions) :**",
                      "| Date | Sens | Montant | Type | Libellé |",
                      "|---|---|---|---|---|"]
            for t in txns[:5]:
                m = t.get("montant") or 0
                sens = "↑ crédit" if t.get("sens") == "credit" else "↓ débit"
                lib = str(t.get("libelle", ""))[:40]
                lines.append(
                    f"| {t.get('date_operation','')} | {sens} | {m:,.2f} € "
                    f"| `{t.get('type_operation','')}` | {lib} |"
                )

    if "csv" in parsed and "xlsx" in parsed:
        lines += ["", "---"]

    if "xlsx" in parsed:
        x = parsed["xlsx"]
        method_tag_xl = " *(LLM)*" if x.get("_meta", {}).get("method") == "llm_generated" else ""
        lines += [
            "",
            f"## Matrice Excel{method_tag_xl}",
            "",
            f"**Base CLient** — {x['nb_ouvertes']} ouvertes ({x['total_ouvert']:,.2f} €), {x['nb_payees']} payées",
            f"Clients : {', '.join(x['clients'][:8])}" + (" …" if len(x['clients']) > 8 else ""),
        ]
        factures = x.get("factures", [])
        if factures:
            lines += ["", "| N° Facture | Client | Montant TTC | Échéance |",
                      "|---|---|---|---|"]
            for f in factures[:5]:
                m = f.get("montant_ttc") or 0
                lines.append(
                    f"| {f.get('id','')} | {str(f.get('client',''))[:22]} "
                    f"| {m:,.2f} € | {f.get('date_echeance') or '—'} |"
                )

        lines += [
            "",
            f"**Base Sous-traitants** — {x['nb_st_ouverts']} ouvertes ({x['total_st_ouvert']:,.2f} €)",
            f"**Autres** — FG : {x['nb_fg']}, NdF : {x['nb_ndf']}, Paies : {x['nb_paies']}",
        ]

        pret = x.get("pret")
        if pret:
            lines += [
                "",
                f"**Prêt — {pret.get('nom', '')}**",
                f"- Mensualité : **{pret.get('mensualite_totale') or 0:,.2f} €** "
                f"(remboursement {pret.get('mensualite_remboursement') or 0:,.2f} € + assurance {pret.get('assurance_mensuelle') or 0:,.2f} €)",
                f"- Remboursé à date : {pret.get('rembourse_a_date') or 0:,.2f} € — "
                f"Reste : **{pret.get('reste_a_rembourser') or 0:,.2f} €**",
                f"- Dernière échéance : {pret.get('derniere_echeance', '')}",
            ]

        tva_list = x.get("tva", [])
        mois_csv = None
        if "csv" in parsed:
            txns = parsed["csv"].get("transactions", [])
            if txns:
                mois_csv = (txns[0].get("date_operation") or "")[:7]

        tva_mois = None
        if mois_csv and tva_list:
            tva_mois = next((t for t in tva_list if t["mois"][:7] == mois_csv), None)

        if tva_mois:
            lines += [
                "",
                f"**TVA — {tva_mois['mois'][:7]}**",
                "| TVA collectée | TVA déductible ST | TVA déductible FG | TVA à payer |",
                "|---|---|---|---|",
                f"| {tva_mois.get('tva_collectee') or 0:,.2f} € "
                f"| {tva_mois.get('tva_deductible_st') or 0:,.2f} € "
                f"| {tva_mois.get('tva_deductible_fg') or 0:,.2f} € "
                f"| {tva_mois.get('tva_due') or tva_mois.get('decaissement_tva') or 0:,.2f} € |",
            ]

        budget_list = x.get("budget_treso", [])
        budget_mois = None
        if mois_csv and budget_list:
            budget_mois = next((b for b in budget_list if b["mois"][:7] == mois_csv), None)

        if budget_mois:
            lines += [
                "",
                f"**Budget de tréso — {budget_mois['mois'][:7]}**",
                "| Poste | Prévu | Réel |",
                "|---|---|---|",
                f"| Encaissements | {budget_mois.get('total_ca_ttc') or 0:,.2f} € | {budget_mois.get('ca_reellement_encaisse') or 0:,.2f} € |",
                f"| Sous-traitance | {budget_mois.get('total_st_ttc') or 0:,.2f} € | {budget_mois.get('st_reellement_payes') or 0:,.2f} € |",
                f"| Frais Généraux | {budget_mois.get('total_frais_generaux') or 0:,.2f} € | {budget_mois.get('fg_reellement_payes') or 0:,.2f} € |",
                f"| Salaires nets | {budget_mois.get('salaires_nets') or 0:,.2f} € | — |",
                f"| Échéance prêt | {budget_mois.get('echeance_pret') or 0:,.2f} € | — |",
                f"| TVA | {budget_mois.get('tva_a_payer') or 0:,.2f} € | — |",
                "|---|---|---|",
                f"| **Total encaissements** | **{budget_mois.get('total_encaissements') or 0:,.2f} €** | — |",
                f"| **Total décaissements** | **{budget_mois.get('total_decaissements') or 0:,.2f} €** | — |",
                f"| **Variation tréso** | **{budget_mois.get('variation_tresorerie') or 0:,.2f} €** | — |",
                f"| Tréso début | {budget_mois.get('tresorerie_debut') or 0:,.2f} € | — |",
                f"| **Tréso fin** | **{budget_mois.get('tresorerie_fin') or 0:,.2f} €** | — |",
            ]

    if "csv" in parsed and "xlsx" in parsed:
        lines += [
            "",
            "---",
            "",
            "Ingestion terminée. Posez une question sur les données ou tapez **Lancer le rapprochement**.",
        ]

    return "\n".join(lines)


def _build_data_context(parsed: dict) -> str:
    """Sérialise les données parsées pour le contexte GPT-4o."""
    parts = []

    if "csv" in parsed:
        c = parsed["csv"]
        parts.append(
            f"RELEVE BANCAIRE : {c['nb_transactions']} transactions | "
            f"solde {c['solde_initial']:,.2f} → {c['solde_final']:,.2f} € | "
            f"débits {c['total_debits']:,.2f} € | crédits {c['total_credits']:,.2f} €\n"
            f"Types : {c['types']}"
        )
        txns = c.get("transactions", [])
        if txns:
            rows = [
                f"  {t.get('date_operation','')} | {t.get('sens','')} | "
                f"{t.get('montant') or 0:,.2f} € | type={t.get('type_operation','')} | "
                f"{str(t.get('libelle',''))}"
                for t in txns
            ]
            parts.append("Toutes les transactions :\n" + "\n".join(rows))

    if "xlsx" in parsed:
        x = parsed["xlsx"]
        parts.append(
            f"MATRICE EXCEL : {x['nb_ouvertes']} factures ouvertes ({x['total_ouvert']:,.2f} €) | "
            f"{x['nb_payees']} payées | {x['nb_st_ouverts']} ST ouvertes | "
            f"FG : {x['nb_fg']} | NdF : {x['nb_ndf']} | Paies : {x['nb_paies']}\n"
            f"Clients : {', '.join(x['clients'])}"
        )

        factures = x.get("factures", [])
        if factures:
            rows = [
                f"  {f.get('id','')} | {str(f.get('client',''))} | "
                f"{f.get('montant_ttc') or 0:,.2f} € | échéance={f.get('date_echeance') or '—'}"
                for f in factures
            ]
            parts.append("Factures ouvertes :\n" + "\n".join(rows))

        st = x.get("st_ouverts", [])
        if st:
            rows = [
                f"  {f.get('id','')} | {str(f.get('client',''))} | {f.get('montant_ttc') or 0:,.2f} €"
                for f in st
            ]
            parts.append("Sous-traitants ouverts :\n" + "\n".join(rows))

        pret = x.get("pret")
        if pret:
            parts.append(
                f"PRET — {pret.get('nom','')} : mensualité {pret.get('mensualite_totale',0):,.2f} € | "
                f"reste {pret.get('reste_a_rembourser',0):,.2f} € | "
                f"dernière échéance {pret.get('derniere_echeance','')}"
            )

        tva_list = x.get("tva", [])
        if tva_list:
            rows = [
                f"  {t.get('mois','')[:7]} | collectée {t.get('tva_collectee') or 0:,.2f} € | "
                f"déd.ST {t.get('tva_deductible_st') or 0:,.2f} € | "
                f"due {t.get('tva_due') or 0:,.2f} €"
                for t in tva_list[-6:]
            ]
            parts.append("TVA (6 derniers mois) :\n" + "\n".join(rows))

    return "\n\n".join(parts)


def _qa_sync(question: str, parsed: dict, history: list[dict]) -> str:
    """Appel GPT-4o avec historique de conversation et contexte des données."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    context = _build_data_context(parsed)

    system_msg = {
        "role": "system",
        "content": (
            "Tu es un assistant comptable expert pour ECO Steering. "
            "Tu réponds en français de manière concise, en Markdown. "
            "Tu as accès aux données de rapprochement bancaire ci-dessous. "
            "Utilise l'historique de la conversation pour les questions de suivi. "
            "Ne suppose rien d'extérieur aux données — si la réponse n'y est pas, dis-le.\n\n"
            f"Données disponibles :\n{context}"
        ),
    }

    messages = [system_msg] + history[-20:] + [{"role": "user", "content": question}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_files(
    csv_file: UploadFile | None = File(default=None),
    xlsx_file: UploadFile | None = File(default=None),
):
    if not csv_file and not xlsx_file:
        raise HTTPException(status_code=400, detail="Aucun fichier reçu.")

    session_id  = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    csv_name = xlsx_name = None

    if csv_file and csv_file.filename:
        dest = session_dir / csv_file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(csv_file.file, f)
        csv_name = csv_file.filename

    if xlsx_file and xlsx_file.filename:
        dest = session_dir / xlsx_file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(xlsx_file.file, f)
        xlsx_name = xlsx_file.filename

    sessions[session_id] = {
        "csv":     str(session_dir / csv_name)  if csv_name  else None,
        "xlsx":    str(session_dir / xlsx_name) if xlsx_name else None,
        "parsed":  None,
        "history": [],
    }

    parts = []
    if csv_name:  parts.append(f"relevé `{csv_name}`")
    if xlsx_name: parts.append(f"matrice `{xlsx_name}`")

    return UploadResponse(
        session_id=session_id,
        csv_filename=csv_name,
        xlsx_filename=xlsx_name,
        message=f"Fichier(s) reçu(s) : {' et '.join(parts)}.",
    )


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate() -> AsyncGenerator[str, None]:
        session = sessions.get(req.session_id or "", {})
        csv_path  = session.get("csv")
        xlsx_path = session.get("xlsx")
        csv_ok    = bool(csv_path)
        xlsx_ok   = bool(xlsx_path)
        msg       = req.message.lower().strip()

        if not csv_ok and not xlsx_ok:
            async for chunk in _stream_text(
                "Pour démarrer un rapprochement, j'ai besoin de deux fichiers :\n\n"
                "1. **Relevé bancaire** — fichier `.csv` (export CIH/AWB)\n"
                "2. **Matrice Excel** — fichier `.xlsx` (matrice ECO Steering)\n\n"
                "Utilisez le bouton **Importer des fichiers** pour les déposer."
            ):
                yield chunk
            yield _sse_done()
            return

        if csv_ok and not xlsx_ok:
            async for chunk in _stream_text(
                "✅ Relevé bancaire reçu.\n\n"
                "Il me manque encore la **matrice Excel** (`.xlsx`). Déposez-la pour continuer."
            ):
                yield chunk
            yield _sse_done()
            return

        if not csv_ok and xlsx_ok:
            async for chunk in _stream_text(
                "✅ Matrice Excel reçue.\n\n"
                "Il me manque encore le **relevé bancaire** (`.csv`). Déposez-le pour continuer."
            ):
                yield chunk
            yield _sse_done()
            return

        lance = any(w in msg for w in ["lancer", "démarrer", "parser", "analyser",
                                        "start", "rapprochement", "csv", "excel",
                                        "déposer", "fichier"])
        already_parsed = session.get("parsed") is not None

        if lance and not already_parsed:
            yield _sse("Parsing en cours...\n\n")
            await asyncio.sleep(0.1)
            try:
                loop = asyncio.get_event_loop()
                parse_task = loop.run_in_executor(None, _run_parse, csv_path, xlsx_path)
                steps = [
                    "Echantillonnage des fichiers",
                    "GPT-4o analyse la structure",
                    "Generation du code de parsing",
                    "Execution et validation",
                    "Correction automatique",
                ]
                step_idx = 0
                while True:
                    try:
                        parsed = await asyncio.wait_for(asyncio.shield(parse_task), timeout=3.0)
                        break
                    except asyncio.TimeoutError:
                        yield _sse_progress(steps[min(step_idx, len(steps)-1)])
                        step_idx += 1
                sessions[req.session_id]["parsed"] = parsed
                async for chunk in _stream_text(_format_parse_report(parsed)):
                    yield chunk
            except Exception as e:
                async for chunk in _stream_text(f"Erreur de parsing : {e}"):
                    yield chunk

        elif already_parsed and not lance:
            yield _sse_progress("Analyse des données...")
            await asyncio.sleep(0.05)
            try:
                history = session.get("history", [])
                loop    = asyncio.get_event_loop()
                answer  = await loop.run_in_executor(
                    None, _qa_sync, req.message.strip(), session["parsed"], history
                )
                sessions[req.session_id]["history"] = history + [
                    {"role": "user",      "content": req.message.strip()},
                    {"role": "assistant", "content": answer},
                ]
                async for chunk in _stream_text(answer):
                    yield chunk
            except Exception as e:
                async for chunk in _stream_text(f"Erreur : {e}"):
                    yield chunk

        elif lance and already_parsed:
            async for chunk in _stream_text(
                "Les données sont déjà parsées. "
                "Posez une question sur les transactions ou les factures, "
                "ou tapez **Réinitialiser** pour recommencer."
            ):
                yield chunk

        else:
            async for chunk in _stream_text(
                "Les deux fichiers sont prêts.\n\n"
                "Tapez **Lancer le parsing** pour démarrer l'ingestion."
            ):
                yield chunk

        yield _sse_done()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/session/{session_id}/data")
async def get_session_data(session_id: str):
    from fastapi.encoders import jsonable_encoder
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    parsed = session.get("parsed")
    if not parsed:
        return {"status": "not_parsed"}
    return {"status": "ok", "data": jsonable_encoder(parsed)}


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    return {
        "session_id":    session_id,
        "has_csv":       bool(session.get("csv")),
        "has_xlsx":      bool(session.get("xlsx")),
        "is_parsed":     session.get("parsed") is not None,
        "message_count": len(session.get("history", [])),
    }
