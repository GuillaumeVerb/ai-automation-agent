# AI Automation Agent

AI Automation Agent est un MVP local et démontrable d'un workflow IA centré sur:
- email triage
- reporting copilot
- explicabilité
- observabilité
- validation humaine

Le système reçoit un texte ou un email, le classe, en extrait les champs utiles, génère un résumé puis une sortie exploitable, calcule un automation score, expose une timeline d'exécution, et conserve runs + feedbacks en SQLite.

## Positionnement

Le projet privilégie volontairement:
- une architecture simple
- un flux semi-déterministe
- un service layer modulaire
- une validation humaine visible
- aucune action externe irréversible

Ce n'est pas un multi-agent system. C'est un MVP crédible, lisible et testable.

## Stack

- Python
- FastAPI
- SQLModel + SQLite
- Pydantic
- Streamlit
- Pytest

## Fonctionnalités

### MVP

- création de runs via API ou UI
- classification dans une catégorie fermée
- extraction des champs utiles
- résumé court
- génération d'un brouillon d'email ou d'un mini-rapport markdown
- automation score avec mode recommandé
- explainability panel
- timeline d'exécution
- validation humaine
- persistance des runs et feedbacks

### V2 light

- persistence dédiée des événements de timeline
- feedback learning heuristique via table `preferences`
- réutilisation transparente des dernières corrections pertinentes
- analytics page légère
- modes d'autonomie visibles:
  - `suggestion_only`
  - `assisted`
  - `low_risk_auto`

## Architecture

```text
UI Streamlit / API FastAPI
        -> preprocess
        -> classify
        -> extract
        -> summarize
        -> route strategy
        -> generate output
        -> compute score + explainability
        -> human review
        -> persist run + timeline + feedback
```

Organisation du repo:

```text
app/
  api/
  core/
  db/
  models/
  prompts/
  services/
ui/
tests/
data/
```

## Modèle de données

### `Run`

Stocke l'entrée, la classification, les champs extraits, la sortie générée, le score, le risque, le mode recommandé, le statut et la latence.

### `TimelineEventRecord`

Stocke chaque étape métier individuellement:
- `input_received`
- `preprocessed`
- `classified`
- `extracted`
- `generated`
- `scored`
- `reviewed`
- `saved`

### `Feedback`

Stocke les corrections utilisateur:
- catégorie
- priorité
- ton
- champs extraits

### `Preference`

Mémoire heuristique simple réutilisée sur les runs suivants pour refléter les dernières corrections.

## Endpoints

- `POST /api/v1/runs`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/approve`
- `POST /api/v1/runs/{run_id}/regenerate`
- `POST /api/v1/runs/{run_id}/feedback`
- `GET /api/v1/runs/{run_id}/feedback`
- `GET /api/v1/metrics`
- `GET /health`

## Setup local

### 1. Préparer l'environnement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialiser la base

Pour repartir proprement:

```bash
rm -f agent.db
PYTHONPATH=. python -m app.db.init_db
```

### 3. Lancer l'API

```bash
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4. Lancer l'UI

```bash
PYTHONPATH=. UI_API_BASE_URL=http://127.0.0.1:8000 streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

### 5. URLs utiles

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`
- Healthcheck: `http://127.0.0.1:8000/health`

## Variables d'environnement

Voir [.env.example](/Users/guillaumeverbiguie/Desktop/ai automation agent/.env.example).

Variables principales:

```bash
APP_NAME=AI Automation Agent
APP_ENV=dev
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DATABASE_URL=sqlite:///./agent.db
APP_LLM_PROVIDER=mock
APP_LLM_MODEL=local-heuristic
APP_LLM_API_KEY=
APP_LLM_BASE_URL=https://api.openai.com/v1
APP_LLM_ENABLED=false
APP_LLM_TIMEOUT_SECONDS=20
UI_API_BASE_URL=http://127.0.0.1:8000
```

## Utilisation

### Via l'UI

1. Ouvrir l'UI Streamlit.
2. Coller un email ou charger un preset de démo depuis `data/demo_requests.json`.
3. Choisir le type d'entrée et le mode d'autonomie.
4. Lancer l'analyse.
5. Relire la sortie, la timeline, le score et l'explicabilité.
6. Approuver, corriger, régénérer ou marquer une escalade humaine.

### Via l'API

Créer un run:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour, notre export KPI plante depuis hier. Merci de preparer aussi une reponse client.",
    "input_type": "email",
    "mode": "assisted"
  }'
```

Récupérer les métriques:

```bash
curl -sS http://127.0.0.1:8000/api/v1/metrics
```

## Analytics

La page Analytics expose:
- total runs
- approval rate
- average automation score
- average latency by step
- category distribution
- autonomy mode distribution
- risk distribution
- top feedback patterns
- score bands
- recent runs snapshot

## Tests

Lancer toute la suite:

```bash
PYTHONPATH=. python -m pytest -q
```

Suite ciblée backend:

```bash
PYTHONPATH=. python -m pytest tests/test_api.py tests/test_orchestrator.py tests/test_persistence.py tests/test_classifier.py tests/test_extractor.py tests/test_scorer.py -q
```

Les tests couvrent au minimum:
- classifier output shape
- extractor output shape
- automation score logic
- timeline persistence
- feedback persistence
- autonomy mode recommendation
- API smoke tests

## Démo en moins de 3 minutes

1. Lancer l'API et l'UI.
2. Dans l'onglet Run, charger un preset de démo.
3. Lancer l'analyse.
4. Montrer:
   - la catégorie
   - le résumé
   - les champs extraits
   - le brouillon d'email ou mini-rapport
   - le score et le mode recommandé
   - la timeline détaillée
5. Corriger le ton ou la catégorie.
6. Régénérer un run.
7. Aller dans Analytics pour montrer l'impact des runs et feedbacks.

## Limites du MVP

- pas d'envoi réel d'email
- pas d'intégration tierce réelle
- pas de multi-agent
- pas de mémoire longue durée avancée
- pas de système de migration DB formel
- le mode `low_risk_auto` reste visible et simulé, sans action externe

## OpenAI réel

Le projet peut appeler un provider configuré via `v1/responses`, mais fonctionne par défaut en heuristiques locales.

Exemple:

```bash
APP_LLM_ENABLED=true
APP_LLM_PROVIDER=openai
APP_LLM_API_KEY=sk-...
APP_LLM_MODEL=gpt-4.1-mini
APP_LLM_BASE_URL=https://api.openai.com/v1
```

## Ce que "done" signifie ici

- API locale fonctionnelle
- UI Streamlit locale fonctionnelle
- persistance SQLite active
- données de démo incluses
- tests minimums présents
- README de setup et de démo à jour
