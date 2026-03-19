# AI Automation Agent MVP

AI Automation Agent est un MVP portfolio centré sur un cas d'usage simple:
tri, résumé et génération de sorties utiles à partir d'un email ou d'une demande métier.

Le projet privilégie:
- une architecture explicable,
- un workflow étroit et observable,
- une validation humaine,
- des intégrations externes simulées.

## Stack

- FastAPI
- SQLModel + SQLite
- Streamlit
- Tests Pytest

## Features

- Création de runs via API
- Classification, extraction et résumé
- Routage semi-déterministe vers réponse email ou mini report
- Explainability panel, timeline et automation score
- Feedback utilisateur et mémoire légère via `preferences`
- Historique des runs et analytics simples

## Lancement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --reload
streamlit run ui/streamlit_app.py
```

L'API démarre sur `http://127.0.0.1:8000` et l'UI consomme cette base par défaut.

## Endpoints

- `POST /api/v1/runs`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/approve`
- `POST /api/v1/runs/{run_id}/regenerate`
- `POST /api/v1/runs/{run_id}/feedback`
- `GET /api/v1/metrics`

## Demo flow

1. Coller un email ou un texte dans l'UI.
2. Lancer l'analyse.
3. Vérifier classification, résumé, champs extraits, timeline et score.
4. Approuver ou corriger.
5. Contrôler l'impact dans l'historique et les analytics.

## Notes

- Le provider LLM est configurable, mais le MVP tourne en mode heuristique local.
- Un provider OpenAI-compatible peut etre active via `APP_LLM_ENABLED=true`, `APP_LLM_API_KEY`, `APP_LLM_MODEL` et `APP_LLM_BASE_URL`.
- Aucun email réel n'est envoyé.
- Aucune action irréversible n'est exécutée.
