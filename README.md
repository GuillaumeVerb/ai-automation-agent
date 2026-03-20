# AI Automation Agent MVP + V2

AI Automation Agent est un MVP portfolio centre sur un cas d'usage simple:
tri, resume et generation de sorties utiles a partir d'un email ou d'une demande metier.

Le projet privilegie:
- une architecture explicable,
- un workflow etroit et observable,
- une validation humaine,
- des integrations externes simulees.

## Stack

- FastAPI
- SQLModel + SQLite
- Streamlit
- Tests Pytest

## Features MVP

- Creation de runs via API
- Classification, extraction et resume
- Routage semi-deterministe vers reponse email ou mini report
- Explainability panel, timeline et automation score
- Feedback utilisateur et memoire legere via `preferences`
- Historique des runs et analytics simples

## V2 Features

- Explainability panel enrichi:
  - categorie detectee
  - confiance
  - signaux
  - strategie choisie
  - justification concise
  - niveau de risque
- Execution timeline detaillee:
  - input_received
  - preprocess
  - classification
  - extraction
  - generation
  - scoring
  - human_validation
  - persistence
  - avec statut, duree et sortie courte par etape
- Automation Score V2:
  - score global
  - sous-score confiance
  - sous-score risque
  - sous-score completude
  - recommandation d'autonomie
  - temps economise estime
- Modes d'autonomie visibles:
  - `suggestion_only`
  - `assisted`
  - `low_risk_auto`
- Feedback learning simple:
  - corrections de categorie, priorite, ton, champs extraits
  - stockage en base
  - reutilisation heuristique transparente sur les runs suivants
- Analytics page legere:
  - total runs
  - taux d'approbation
  - repartition par categorie
  - score moyen
  - top feedbacks
  - latence moyenne par etape
  - distribution des modes d'autonomie

## Lancement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
rm -f agent.db
python -m app.db.init_db
uvicorn app.main:app --reload
streamlit run ui/streamlit_app.py
```

L'API demarre sur `http://127.0.0.1:8000` et l'UI consomme cette base par defaut.

## Important V2 SQLite

La V2 ajoute plusieurs champs au schema SQLite sans systeme de migration.

Pour un environnement local propre:

```bash
rm -f agent.db
python -m app.db.init_db
```

## OpenAI reel

Le projet peut appeler l'API OpenAI via `v1/responses` avec Structured Outputs pour les etapes JSON.

Variables utiles:

```bash
APP_LLM_ENABLED=true
APP_LLM_PROVIDER=openai
APP_LLM_API_KEY=sk-...
APP_LLM_MODEL=gpt-4.1-mini
APP_LLM_BASE_URL=https://api.openai.com/v1
```

Si ces variables ne sont pas definies, le systeme retombe automatiquement sur le moteur heuristique local.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`

## Endpoints

- `POST /api/v1/runs`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/approve`
- `POST /api/v1/runs/{run_id}/regenerate`
- `POST /api/v1/runs/{run_id}/feedback`
- `GET /api/v1/runs/{run_id}/feedback`
- `GET /api/v1/metrics`

## Demo flow

1. Coller un email ou un texte dans l'UI.
2. Choisir un mode d'autonomie visible.
3. Lancer l'analyse.
4. Verifier explainability, score V2, timeline et resultat genere.
5. Approuver ou corriger.
6. Rejouer un run pour observer la reutilisation heuristique du feedback.
7. Verifier l'impact dans l'historique et les analytics.

## Tests

Depuis un environnement virtuel avec les dependances installees:

```bash
python -m pytest -q
```

Tests cibles V2:

- score d'automatisation
- timeline detaillee
- persistance du feedback
- modes d'autonomie
- endpoints enrichis

## Notes

- Le provider LLM est configurable, mais le MVP tourne en mode heuristique local.
- Aucun email reel n'est envoye.
- Aucune action irreversible n'est executee.
- Le mode `low_risk_auto` reste simule et visible, sans automation externe.
- Le feedback learning reste simple, heuristique et transparent.
