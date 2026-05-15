# Comprendre le code — Guide personnel

## C'est quoi ce projet en une phrase ?

Un programme qui lit le relevé bancaire CSV + la matrice Excel ECO Steering,
et rapproche automatiquement chaque virement reçu avec la/les facture(s) correspondante(s).

---

## Les fichiers d'entrée

- **Relevé bancaire** : fichier `.csv` exporté depuis la banque (CIH ou AWB)
- **Matrice Excel** : le fichier `.xlsx` interne ECO Steering avec tous les onglets

---

## Comment le programme est organisé : 4 agents

```
CSV + Excel
    ↓
LECTEUR       → lit et extrait les données des deux fichiers
    ↓
CLASSEUR      → trie chaque transaction bancaire dans une catégorie
    ↓
VÉRIFICATEUR  → fait le rapprochement : quel virement = quelles factures ?
    ↓
ÉCRIVAIN      → écrit les résultats dans l'Excel (pas encore fait)
    ↓
Excel mis à jour
```

Chaque agent est un "expert" qui a des outils (fonctions Python) et un LLM (Mistral).

---

## Agent 1 — Lecteur

**Fichiers :** `src/crew/agents/lecteur/`

Il lit les deux fichiers et en extrait les données.

### Outil ParseCsvTool (pour le CSV bancaire)

Le CSV bancaire est particulier : encodage Windows-1252, séparateur `;`, les données commencent à la ligne 7.

Il lit chaque ligne et extrait :
- date, montant, libellé, type d'opération (code `05`, `06`, etc.), débit ou crédit

Il vérifie aussi que les chiffres sont cohérents :
`solde initial + crédits - débits = solde final`
Si ça ne colle pas, il lance un avertissement.

### Outil ParseExcelTool (pour la matrice Excel)

Il ouvre l'Excel et lit chaque onglet avec le bon parser selon la structure :

| Onglet | Parser utilisé | Pourquoi |
|--------|---------------|---------|
| Base CLient, Frais Généraux, Paies... | `TableParser` | Tableau classique (en-têtes en ligne 3) |
| Budget de tréso | `MatrixParser` | Tableau croisé (mois en colonnes) |
| Prêt | `KeyValueParser` | Paires clé/valeur |

**Règle importante :** L'Excel est toujours ouvert avec `data_only=False` pour garder les formules SUMIF du Budget de tréso. Si on met `True`, les formules disparaissent.

---

## Agent 2 — Classeur

**Fichiers :** `src/crew/agents/classeur/`

Il prend les transactions du Lecteur et met une catégorie sur chacune.

### Comment il classifie

Le CSV bancaire a un champ `Type d'opération` avec un code numérique.
Le code est **toujours prioritaire** sur le texte du libellé.

| Code | Catégorie |
|------|-----------|
| `05` | `encaissement_client` — virement reçu d'un client |
| `06` | `paiement_st` — on paie un sous-traitant |
| `08` | `prelevement` |
| `11` | `note_de_frais` |
| `44` | `international` — virement étranger |
| `62` | `frais_bancaires` |
| `91` | `divers` |

Il détecte aussi les anomalies : par exemple un code `05` (encaissement) qui apparaît côté débit — c'est bizarre et il le signale.

Si le code est inconnu, le LLM lit le libellé texte pour deviner la catégorie.

---

## Agent 3 — Vérificateur

**Fichiers :** `src/crew/agents/verificateur/`

Il prend tous les virements de type `encaissement_client` et cherche quelles factures correspondent.

### L'algorithme de matching — `src/tools/matching.py`

C'est la pièce la plus importante du projet.

**Le problème :** Un virement de 53 346 € arrive. Quelles factures ouvertes d'Altran font exactement 53 346 € ?

**La solution :** Un algorithme mathématique qui teste les combinaisons de factures.

- Si ≤ 20 factures : il teste toutes les combinaisons possibles
- Si > 20 factures : il utilise un backtracking intelligent pour aller plus vite
- Tolérance de ±1 € (pour les arrondis)
- Calcule en centimes pour éviter les bugs d'arrondi des nombres à virgule

**Règle absolue : le LLM ne calcule jamais les montants.** Il présente juste le résultat au comptable.

Il y a aussi un système d'alias pour les noms clients :
`"ALTRAN PROTOTYPES AUTO"` dans le libellé bancaire → reconnu comme `"ALTRAN TECHNOLOGIES"` dans l'Excel.

---

## Agent 4 — Écrivain

**Fichier :** `src/crew/agents/ecrivain.py`

Son rôle : écrire les résultats du rapprochement dans la matrice Excel (colonnes STATUT, DATE PAIEMENT, etc.).

**Statut actuel : pas encore implémenté.**

---

## Le LLM — comment c'est configuré

**Fichier :** `src/config.py`

Tous les agents utilisent `get_llm("small")` — jamais de nom de modèle en dur dans le code.

Dans le fichier `.env` tu choisis le provider :
- `LLM_PROVIDER=mistral_api` → Mistral en ligne (faut une clé API)
- `LLM_PROVIDER=ollama` → Mistral en local sur ton PC (pas de clé)
- `LLM_PROVIDER=openai` → GPT

---

## L'orchestrateur — `src/crew/orchestrator.py`

C'est le fichier qui doit assembler les 4 agents et les faire tourner en séquence.

**Statut actuel : pas encore implémenté.** La fonction `build_reconciliation_crew()` lance juste une erreur pour l'instant.

C'est ce qu'on doit faire ensuite.

---

## Les schémas de données — `src/models/schemas.py`

Ce sont des "moules" Python (Pydantic) qui définissent la forme des données.

| Schéma | À quoi ça correspond |
|--------|---------------------|
| `Transaction` | Une ligne du relevé bancaire |
| `Invoice` | Une facture (client ou sous-traitant) |
| `MatchResult` | Un virement + les factures matchées |
| `IngestedData` | Tout ce que le Lecteur a extrait |

---

## Comment marche le rapprochement — de A à Z

### Le point de départ

Tu as deux sources de données :
- **Relevé bancaire** : liste des mouvements d'argent du mois (virements reçus, paiements, etc.)
- **Matrice Excel** : liste des factures que tes clients doivent payer

Le rapprochement = relier chaque virement reçu à la/les facture(s) correspondante(s).

---

### Étape 1 — Filtrer les encaissements

On ne rapproche pas toutes les transactions — seulement celles de type `05` (virements reçus de clients).

```
55 transactions au total
  → 7 sont de type 05 (encaissement_client)
  → Ce sont les 7 qu'on va rapprocher
```

---

### Étape 2 — Identifier le client (LLM)

Pour chaque virement, le libellé bancaire dit quelque chose comme :
```
"VIR ALTRAN PROTOTYPES AUTO REF 2026-03"
```

Un seul appel LLM (batch) lit tous les libellés d'un coup et extrait le nom du client :
```
→ "ALTRAN PROTOTYPES AUTO"
```

Puis un dictionnaire d'alias normalise le nom :
```
"ALTRAN PROTOTYPES AUTO"  →  "ALTRAN TECHNOLOGIES"
```
pour que ça corresponde à ce qui est écrit dans l'Excel.

---

### Étape 3 — Trouver les factures (algo subset-sum)

Pour un virement de **53 346 €** d'Altran, l'algo fait :

1. Prend toutes les factures ouvertes d'Altran dans l'Excel
2. Cherche quelle combinaison de ces factures donne exactement 53 346 € (±1 €)
3. Retourne la/les combinaison(s) trouvée(s)

```
Factures Altran ouvertes :
  FC1183 → 12 000 €
  FC1184 → 38 346 €
  FC1195 → 15 000 €
  FC1201 →  8 000 €

L'algo teste :
  FC1183 seule          → 12 000 € ❌
  FC1184 seule          → 38 346 € ❌
  FC1183 + FC1184       → 50 346 € ❌
  FC1184 + FC1195       → 53 346 € ✅ TROUVÉ
```

---

### Étape 4 — Trois cas possibles

| Cas | Ce qui se passe |
|-----|----------------|
| **1 combinaison** | Match automatique, on continue |
| **Plusieurs combinaisons** | On affiche les options, le comptable choisit |
| **0 combinaison** | Signalé comme non rapproché |

---

### Étape 5 — Les factures utilisées sont "consommées"

Une fois FC1184 et FC1195 matchées avec le virement Altran, elles sont **retirées du pool** pour les virements suivants. Ça évite de matcher deux fois la même facture.

```
Virement 1 → Altran 53 346 €    → FC1184 + FC1195 ✅  (retirées du pool)
Virement 2 → Capgemini 45 000 € → cherche parmi les factures restantes
...
```

---

### Résumé en une ligne

> Pour chaque virement reçu : LLM identifie le client → algo mathématique cherche la combinaison de factures → comptable valide si ambigu.

---

## Ce qui est fait vs ce qui reste

| Quoi | État |
|------|------|
| Lire le CSV bancaire | Fait |
| Lire la matrice Excel (tous onglets) | Fait |
| Classifier les transactions | Fait |
| Algorithme de matching factures | Fait |
| Agents Lecteur, Classeur, Vérificateur | Fait |
| Orchestrateur (assembler la crew) | **À faire** |
| Écrivain (écrire dans l'Excel) | **À faire** |
| Frontend branché sur le backend | **À faire** |
