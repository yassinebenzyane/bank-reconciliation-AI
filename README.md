# Rapprochement Bancaire Automatisé — ECO Steering

Système multi-agents d'automatisation du rapprochement bancaire mensuel pour la SAS ECO Steering.  
Développé par **Yassine Benzyane** (stagiaire Ennoma, 2026).

---

## Contexte et objectif

ECO Steering gère mensuellement un rapprochement entre :
- un **relevé bancaire CSV** (format CIH/AWB) listant toutes les opérations du mois,
- une **matrice Excel** (13 onglets) regroupant factures clients, sous-traitants, frais, TVA, prévisions de trésorerie et tableau d'amortissement.

Ce travail est aujourd'hui réalisé manuellement : identification des paiements reçus, pointage des factures correspondantes, mise à jour des statuts. L'objectif de ce POC est d'**automatiser entièrement ce pipeline** à l'aide d'un système d'IA multi-agents, en garantissant une fiabilité comptable totale.

---

## Philosophie de conception

### 1. Code déterministe d'abord, LLM ensuite

Le principe central du projet est de **ne jamais confier un calcul financier à un LLM**.

Les LLMs sont statistiques : ils peuvent halluciner un montant, inverser une somme, ou ignorer une facture. Pour un rapprochement bancaire, une erreur n'est pas acceptable.

La règle appliquée tout au long du code est donc :

> **Ce qui peut être calculé de manière certaine doit l'être par du code.  
> Le LLM n'intervient que là où le jugement humain est irremplaçable.**

En pratique :

| Tâche | Traitement |
|---|---|
| Parser le CSV bancaire (colonnes, encodage, soldes) | Code pur (`openpyxl`, `pandas`) |
| Classifier une transaction par son code type (`05`, `06`…) | Dictionnaire déterministe |
| Trouver la combinaison de factures qui somme à un virement | Algorithme subset-sum (backtracking) |
| Valider les soldes (initial + crédits − débits = final) | Assertion arithmétique |
| Interpréter un libellé ambigu pour en extraire un nom client | LLM (Mistral) |
| Classer une opération dont le code type est inconnu | LLM en fallback |
| Répondre aux questions du comptable sur les données | LLM (GPT-4o-mini) |

### 2. Architecture multi-agents (CrewAI)

Le pipeline est découpé en **agents spécialisés** orchestrés par [CrewAI](https://github.com/crewAIInc/crewAI). Chaque agent a un rôle unique, des outils dédiés et un LLM configuré indépendamment.

Ce choix permet :
- une **séparation claire des responsabilités** (parsing ≠ classification ≠ matching),
- un **remplacement LLM sans toucher au code** (variable d'env `LLM_PROVIDER`),
- une **résilience** : si le LLM est indisponible, les outils s'exécutent directement.

### 3. Les données typées ne passent pas par le LLM

Les outils CrewAI retournent des résultats typés Python (`list[dict]`, `Decimal`, `date`) stockés dans des attributs `.result`. Le LLM ne voit qu'un **résumé JSON compact** de ce que l'outil a trouvé — jamais les données brutes.

Cela évite la fenêtre de contexte surchargée et les hallucinations sur des données numériques.

---

## Pipeline de traitement

```
Fichiers uploadés (CSV + XLSX)
         │
         ▼
┌─────────────────────────────┐
│  Agent Lecteur              │  Analyse structurelle des fichiers
│  ├─ ParseCsvTool            │  → 100 % déterministe (openpyxl/pandas)
│  └─ ParseExcelTool          │  → 13 onglets parsés avec mappings de colonnes
└──────────────┬──────────────┘
               │  résultats typés (list[Transaction], dict[sheet → rows])
               ▼
┌─────────────────────────────┐
│  Agent Classeur             │  Classification des opérations bancaires
│  ├─ Pass déterministe        │  → TYPE_OP_MAP : code "05" → encaissement_client
│  └─ Fallback LLM            │  → LLM uniquement pour codes inconnus/ambigus
└──────────────┬──────────────┘
               │  transactions enrichies (catégorie + anomalie)
               ▼
┌─────────────────────────────┐
│  Agent Vérificateur         │  Rapprochement virement ↔ factures
│  ├─ LLM : extraction client │  → 1 seul appel batch pour tous les virements
│  └─ Subset-sum : matching   │  → combinaisons exactes à ± 1 € (code, pas LLM)
└──────────────┬──────────────┘
               │  liste de matches (factures_ids, écart, statut)
               ▼
┌─────────────────────────────┐
│  Rapport Markdown           │  Résumé structuré envoyé au frontend via SSE
│  + Session en mémoire       │  Données disponibles pour les questions QA
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  GPT-4o-mini (mode QA)      │  Répond aux questions en langage naturel
│                             │  avec les données parsées comme contexte
└─────────────────────────────┘
```

---

## Structure du code

```
backend/
├── main.py                     ← API FastAPI (upload, chat SSE, session)
├── src/
│   ├── config.py               ← Routeur LLM : get_llm("small"|"large")
│   ├── tools/
│   │   └── matching.py         ← Algorithme subset-sum (rapprochement factures)
│   ├── models/
│   │   └── schemas.py          ← Modèles Pydantic (Transaction, Invoice…)
│   └── crew/
│       └── agents/
│           ├── lecteur/        ← Parsing CSV + Excel
│           │   ├── main.py         Orchestrateur de l'agent
│           │   ├── agent.py        Définition CrewAI (rôle, outils, LLM)
│           │   ├── task.py         Instructions données à l'agent
│           │   ├── tools.py        ParseCsvTool, ParseExcelTool
│           │   ├── config.py       Mappings de colonnes par onglet
│           │   ├── validators.py   Contrôles arithmétiques post-parsing
│           │   └── parsers/        Parsers spécialisés par type de structure
│           │       ├── bank_statement_parser.py
│           │       ├── table_parser.py
│           │       ├── matrix_parser.py
│           │       └── key_value_parser.py
│           ├── classeur/       ← Classification des transactions
│           │   ├── main.py
│           │   ├── agent.py
│           │   ├── task.py
│           │   └── tools.py        ClassifyTransactionsTool
│           └── verificateur/   ← Matching virement ↔ factures
│               ├── main.py
│               ├── agent.py
│               ├── task.py
│               └── tools.py        MatchInvoicesTool

frontend/
└── src/
    ├── app/                    ← Next.js App Router
    ├── components/
    │   ├── DataInspector.tsx   ← 5 onglets de visualisation des données
    │   ├── ChatInterface.tsx   ← Interface de conversation
    │   └── FileUploadZone.tsx  ← Dépôt de fichiers
    └── lib/
        ├── api.ts              ← Client SSE (Server-Sent Events)
        └── types.ts            ← Types TypeScript partagés
```

---

## Détails techniques clés

### Parsing du CSV bancaire

Le relevé CIH/AWB a un format non standard : encodage **Windows-1252**, séparateur **`;`**, en-têtes à la **ligne 7**.

```python
pd.read_csv(path, encoding="windows-1252", sep=";", header=6)
```

Le champ `Type d'opération` contient un code numérique (`05`, `06`, `08`…) qui est **le signal de classification le plus fiable**, prioritaire sur le libellé textuel.

### Parsing de la matrice Excel

```python
openpyxl.load_workbook(path, data_only=False, keep_vba=True)
```

`data_only=False` est impératif : les formules SUMIF du **Budget de trésorerie** doivent être conservées. Passer `True` efface les formules et renvoie `None`.

Les en-têtes de l'onglet **Base CLient** sont en **ligne 3** (pas ligne 1). Chaque onglet a son propre mapping de colonnes défini explicitement dans `lecteur/config.py`.

### Algorithme subset-sum (matching factures)

Pour un virement de montant M, l'algorithme cherche la combinaison de factures ouvertes dont la somme est égale à M (tolérance ± 1 €).

- Pour ≤ 20 factures : énumération exhaustive via `itertools.combinations`.
- Pour > 20 factures : backtracking avec élagage par somme suffixe.
- Tous les calculs en centimes (entiers) pour éviter les erreurs flottantes.

```python
match_invoices_combination(amount=53346.0, open_invoices=[...])
# → { "factures": [FC1183, FC1184, FC1195], "total": 53346.0, "ecart": 0.0 }
```

### Routeur LLM (provider-agnostique)

```python
# src/config.py
from src.config import get_llm

agent = Agent(..., llm=get_llm("small"))  # mistral-small-latest par défaut
```

La variable `.env` `LLM_PROVIDER` permet de basculer entre `mistral_api`, `openai` ou `ollama` sans modifier le code.

### Streaming temps réel (SSE)

Les réponses du backend sont envoyées au frontend via **Server-Sent Events** (`/api/chat/stream`). Cela permet d'afficher la progression du parsing ligne par ligne, sans bloquer l'interface.

---

## Lancer le projet

### Prérequis

- Python 3.13 (Miniconda : `C:\Users\Asus\miniconda3\python.exe`)
- Node.js 18+
- Clé API Mistral (ou OpenAI)

### Installation

```bash
# Backend
cd backend
cp .env.example .env        # Remplir MISTRAL_API_KEY et LLM_PROVIDER
C:\Users\Asus\miniconda3\python.exe -m pip install -e .

# Frontend
cd frontend
npm install
```

### Démarrage

```bash
# Terminal 1 — Backend
cd backend
C:\Users\Asus\miniconda3\python.exe -m uvicorn main:app --reload --port 8001
# → Swagger : http://localhost:8001/docs

# Terminal 2 — Frontend
cd frontend
npm run dev
# → Interface : http://localhost:3000
```

### Utilisation

1. Ouvrir `http://localhost:3000`
2. Déposer le **relevé bancaire CSV** et la **matrice XLSX**
3. Taper « Lancer le parsing » dans le chat
4. Explorer les résultats dans les 5 onglets du DataInspector
5. Poser des questions en langage naturel sur les données

---

## Stack technique

| Composant | Technologie | Version |
|---|---|---|
| Backend API | FastAPI + uvicorn | ≥ 0.110 |
| Orchestration IA | CrewAI | ≥ 0.86 |
| Abstraction LLM | LiteLLM | ≥ 1.40 |
| LLM par défaut | Mistral Small (API) | — |
| LLM QA | GPT-4o-mini (OpenAI) | — |
| Parsing Excel | openpyxl | ≥ 3.1 |
| Parsing CSV | pandas | ≥ 2.2 |
| Validation schémas | Pydantic | ≥ 2.0 |
| Frontend | Next.js + React | 14.2 / 18 |
| Style | Tailwind CSS | 3 |
| Langage frontend | TypeScript | 5 |
| Python | Miniconda | 3.13 |

---

## Variables d'environnement

Créer `backend/.env` à partir de `.env.example` :

```env
MISTRAL_API_KEY=sk-...          # Clé Mistral (console.mistral.ai)
LLM_PROVIDER=mistral_api        # "mistral_api" | "openai" | "ollama"
DATA_INPUT_DIR=data/input
DATA_OUTPUT_DIR=data/output
HISTORY_PATH=data/history.json
```
