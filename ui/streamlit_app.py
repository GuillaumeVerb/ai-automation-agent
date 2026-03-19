import requests
import streamlit as st
from typing import Optional

from app.core.config import get_settings


settings = get_settings()
API_BASE_URL = settings.ui_api_base_url.rstrip("/")


st.set_page_config(page_title="AI Automation Agent", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(209, 233, 255, 0.9), transparent 34%),
            radial-gradient(circle at top right, rgba(255, 225, 204, 0.85), transparent 28%),
            linear-gradient(180deg, #f7f3ea 0%, #f2eee6 100%);
    }
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 22px;
        background: rgba(255, 252, 247, 0.82);
        border: 1px solid rgba(56, 49, 40, 0.08);
        box-shadow: 0 18px 45px rgba(79, 57, 34, 0.08);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
        letter-spacing: -0.04em;
        color: #2d241d;
    }
    .hero p {
        margin: 0.45rem 0 0;
        color: #5b4b3c;
        font-size: 1rem;
    }
    .panel {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(56, 49, 40, 0.08);
        margin-bottom: 1rem;
    }
    .pill {
        display: inline-block;
        margin: 0.1rem 0.35rem 0.35rem 0;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        background: #efe3d3;
        color: #5c4630;
        font-size: 0.83rem;
    }
    </style>
    <div class="hero">
        <h1>AI Automation Agent</h1>
        <p>Email triage + reporting copilot with explainability, score, and human review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio("Navigation", ["Run", "Historique", "Analytics"])


def _api_get(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def _api_post(path: str, payload: dict):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def _safe_call(method: str, path: str, payload: Optional[dict] = None):
    try:
        if method == "GET":
            return _api_get(path), None
        return _api_post(path, payload or {}), None
    except requests.RequestException as exc:
        return None, str(exc)


if page == "Run":
    intro, sample_col = st.columns([1.2, 1])
    with intro:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("New Run")
        sample_text = st.text_area(
            "Texte ou email",
            height=240,
            placeholder="Collez ici un email, une demande metier ou un texte libre.",
        )
        cols = st.columns(3)
        input_type = cols[0].selectbox("Input type", ["email", "text", "json"])
        mode = cols[1].selectbox("Mode", ["suggestion", "assisted", "auto_low_risk"])
        preferred_output = cols[2].selectbox("Preferred output", ["auto", "email_reply", "report"])
        st.caption("Guardrails: no real email send, no irreversible action, validation required for medium/high risk.")
        st.markdown("</div>", unsafe_allow_html=True)
    with sample_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Provider")
        provider_state = "enabled" if settings.llm_enabled and settings.llm_api_key else "fallback local"
        st.write(f"Provider: `{settings.llm_provider}`")
        st.write(f"Model: `{settings.llm_model}`")
        st.write(f"Mode: `{provider_state}`")
        st.subheader("What is visible")
        st.write("Explainability panel")
        st.write("Execution timeline")
        st.write("Automation score")
        st.write("Learning from corrections")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Lancer l'analyse", type="primary", use_container_width=True):
        if not sample_text.strip():
            st.warning("Ajoutez un texte a analyser.")
        else:
            data, error = _safe_call(
                "POST",
                "/api/v1/runs",
                {
                    "text": sample_text,
                    "input_type": input_type,
                    "mode": mode,
                    "preferred_output": None if preferred_output == "auto" else preferred_output,
                },
            )
            if error:
                st.error(f"API unavailable: {error}")
            else:
                st.session_state["last_run_id"] = data["run_id"]

    run_id = st.session_state.get("last_run_id")
    if run_id:
        detail, detail_error = _safe_call("GET", f"/api/v1/runs/{run_id}")
        feedback_items, feedback_error = _safe_call("GET", f"/api/v1/runs/{run_id}/feedback")
        if detail_error:
            st.error(f"Impossible de charger le run: {detail_error}")
            st.stop()
        if feedback_error:
            feedback_items = []

        left, center, right = st.columns([1.15, 1.3, 1])

        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Explainability")
            st.metric("Category", detail["category"])
            st.metric("Confidence", f"{detail['confidence']:.2f}")
            st.metric("Automation Score", detail["automation_score"])
            st.write("Signals")
            st.markdown(
                "".join(f'<span class="pill">{signal}</span>' for signal in detail["explainability"]["signals"]),
                unsafe_allow_html=True,
            )
            st.write("Rationale:", detail["rationale"])
            st.write("Strategy:", ", ".join(detail["strategy"]))
            st.markdown("</div>", unsafe_allow_html=True)

        with center:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Resultat")
            st.write("Summary")
            st.info(detail["summary"])
            st.write("Extracted fields")
            st.json(detail["extracted_fields"])
            st.write("Generated output")
            st.code(detail["generated_output"], language="markdown")

            action_cols = st.columns(3)
            if action_cols[0].button("Approuver", use_container_width=True):
                _, error = _safe_call("POST", f"/api/v1/runs/{run_id}/approve", {})
                if error:
                    st.error(error)
                else:
                    st.rerun()
            regenerate_choice = action_cols[1].selectbox(
                "Regenerate as",
                ["report", "email_reply"],
                key="regenerate_choice",
            )
            if action_cols[1].button("Relancer", use_container_width=True):
                data, error = _safe_call(
                    "POST",
                    f"/api/v1/runs/{run_id}/regenerate",
                    {"preferred_output": regenerate_choice, "strategy_hint": regenerate_choice},
                )
                if error:
                    st.error(error)
                else:
                    st.session_state["last_run_id"] = data["run_id"]
                    st.rerun()
            with action_cols[2].expander("Corriger"):
                field_name = st.selectbox("Champ", ["generated_output", "summary", "priority", "subject"])
                corrected_value = st.text_area("Valeur corrigee", height=100)
                comment = st.text_input("Commentaire")
                if st.button("Enregistrer la correction", use_container_width=True):
                    _, error = _safe_call(
                        "POST",
                        f"/api/v1/runs/{run_id}/feedback",
                        {"field_name": field_name, "corrected_value": corrected_value, "comment": comment},
                    )
                    if error:
                        st.error(error)
                    else:
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Timeline")
            for event in detail["timeline"]:
                st.write(f"**{event['step']}**")
                st.caption(event["detail"])
            st.markdown("### Review")
            st.metric("Status", detail["status"])
            st.metric("Risk", detail["risk_level"])
            st.metric("Saved time", f"{detail['estimated_time_saved_minutes']} min")
            st.write("Autonomy recommendation:", detail["autonomy_recommendation"])
            st.markdown("### Learning from corrections")
            if feedback_items:
                for item in feedback_items:
                    st.write(f"- {item['field_name']}: {item['corrected_value']}")
            else:
                st.caption("Aucune correction pour ce run.")
            st.markdown("</div>", unsafe_allow_html=True)

elif page == "Historique":
    st.subheader("Historique des runs")
    runs, error = _safe_call("GET", "/api/v1/runs")
    if error:
        st.error(f"API unavailable: {error}")
        st.stop()
    category_filter = st.selectbox("Filtre categorie", ["all", "support", "reporting", "commercial", "administratif", "autre"])
    status_filter = st.selectbox("Filtre statut", ["all", "pending_review", "approved"])

    filtered = [
        item
        for item in runs
        if (category_filter == "all" or item["category"] == category_filter)
        and (status_filter == "all" or item["status"] == status_filter)
    ]
    st.dataframe(
        [
            {
                "run_id": item["run_id"],
                "created_at": item["created_at"],
                "category": item["category"],
                "risk_level": item["risk_level"],
                "automation_score": item["automation_score"],
                "status": item["status"],
            }
            for item in filtered
        ],
        use_container_width=True,
    )

elif page == "Analytics":
    st.subheader("Analytics")
    metrics, error = _safe_call("GET", "/api/v1/metrics")
    if error:
        st.error(f"API unavailable: {error}")
        st.stop()
    cols = st.columns(3)
    cols[0].metric("Runs", metrics["total_runs"])
    cols[1].metric("Approval rate", metrics["approval_rate"])
    cols[2].metric("Average score", metrics["average_score"])
    st.write("Category distribution")
    st.json(metrics["category_distribution"])
    st.write("Frequent feedback")
    st.json(metrics["frequent_feedback"])
