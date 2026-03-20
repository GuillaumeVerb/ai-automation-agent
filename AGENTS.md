# AGENTS.md

## Project goal
Build a clean MVP for an AI Automation Agent focused on email triage and reporting assistance.

## Engineering principles
- Keep the architecture simple
- Prefer deterministic flows with small agentic choices
- No unnecessary abstractions
- No multi-agent architecture
- No external irreversible actions
- Human validation must remain in the loop

## Tech stack
- Python
- FastAPI
- Streamlit
- SQLite
- Pydantic
- Modular service layer

## What done means
- API runs locally
- Streamlit UI runs locally
- SQLite persistence works
- Demo inputs included
- Basic tests included
- README explains setup and demo flow

## Style
- Clear naming
- Small focused functions
- Typed Python where practical
- Minimal comments, only useful comments
- Keep files easy to review

## Constraints
- No real email sending
- No real third-party integrations in MVP
- No long-term memory
- No overengineering

## V2 evolution rules
- Keep the MVP architecture simple
- No multi-agent system
- Prefer deterministic flows with light agentic routing
- V2 must improve explainability, observability, and human control
- Feedback reuse must stay heuristic and simple
- Avoid any fake sophistication that makes the code harder to ship
- Every new feature must remain demo-friendly and easy to test locally