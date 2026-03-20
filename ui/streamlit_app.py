from typing import Optional

import pandas as pd
import requests
import streamlit as st

from app.core.config import get_settings


settings = get_settings()
API_BASE_URL = settings.ui_api_base_url.rstrip("/")

MODE_DESCRIPTIONS = {
    "suggestion_only": "Mode 0: l'agent suggere, l'humain decide tout.",
    "assisted": "Mode 1: l'agent prepare et structure, puis validation humaine.",
    "low_risk_auto": "Mode 2: auto faible risque simule, toujours visible et controle.",
}

MODE_LABELS = {
    "suggestion_only": "Mode 0 - Suggestion only",
    "assisted": "Mode 1 - Assisted",
    "low_risk_auto": "Mode 2 - Low-risk auto",
}

TONE_MAP = {
    "low": ("#EAF8F0", "#2E9B5F"),
    "medium": ("#FFF7E8", "#B7791F"),
    "high": ("#FDECEC", "#D84C4C"),
}


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
    .hero, .panel, .insight-card, .timeline-card {
        border-radius: 20px;
        border: 1px solid rgba(56, 49, 40, 0.08);
        background: rgba(255, 255, 255, 0.78);
        box-shadow: 0 18px 45px rgba(79, 57, 34, 0.08);
    }
    .hero {
        padding: 1.2rem 1.4rem;
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
    .insight-card {
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
    }
    .timeline-card {
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.75rem;
    }
    .eyebrow {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #6b7280;
    }
    .timeline-meta {
        color: #6b7280;
        font-size: 0.85rem;
    }
    .mode-box {
        padding: 0.7rem 0.8rem;
        border-radius: 16px;
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(56, 49, 40, 0.08);
        margin-bottom: 0.65rem;
    }
    </style>
    <div class="hero">
        <h1>AI Automation Agent</h1>
        <p>Explainable Workflow Copilot V2 with stronger scoring, timeline, feedback reuse, and lightweight analytics.</p>
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


def _render_pills(items: list[str]) -> None:
    st.markdown("".join(f'<span class="pill">{item}</span>' for item in items), unsafe_allow_html=True)


def _render_explainability(detail: dict) -> None:
    bg_color, border_color = TONE_MAP.get(detail["risk_level"], ("#EDF4FF", "#2F6BFF"))
    explainability = detail["explainability"]
    st.markdown(
        f"""
        <div class="insight-card" style="background:{bg_color}; border-left: 6px solid {border_color};">
            <div class="eyebrow">EXPLAINABILITY PANEL</div>
            <div style="font-size:1.1rem; font-weight:700; color:#111827; margin-top:0.35rem;">
                {explainability['category']} with {explainability['confidence']:.0%} confidence
            </div>
            <div style="margin-top:0.55rem; color:#374151;"><strong>Risk level:</strong> {explainability['risk_level']}</div>
            <div style="margin-top:0.35rem; color:#374151;"><strong>Strategy:</strong> {', '.join(explainability['strategy'])}</div>
            <div style="margin-top:0.35rem; color:#374151;"><strong>Decision rationale:</strong> {explainability['rationale']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("Detected signals")
    _render_pills(explainability["signals"])


def _render_score_panel(detail: dict) -> None:
    score = detail["score_breakdown"]
    mode_note = "Requested mode aligns with recommendation." if detail["requested_mode"] == detail["autonomy_mode"] else (
        f"Requested mode `{detail['requested_mode']}` is more aggressive than the recommendation `{detail['autonomy_mode']}`."
    )
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### Automation Score V2")
    cols = st.columns(4)
    cols[0].metric("Global", score["global_score"])
    cols[1].metric("Confidence", score["confidence_score"])
    cols[2].metric("Risk", score["risk_score"])
    cols[3].metric("Completeness", score["completeness_score"])
    st.caption(score["rationale"])
    meta_cols = st.columns(3)
    meta_cols[0].metric("Recommended mode", detail["autonomy_mode"])
    meta_cols[1].metric("Requested mode", detail["requested_mode"])
    meta_cols[2].metric("Time saved", f"{detail['estimated_time_saved_minutes']} min")
    st.write(mode_note)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_timeline(detail: dict) -> None:
    st.markdown("### Execution Timeline")
    for event in detail["timeline"]:
        status_color = "#2E9B5F" if event["status"] == "completed" else "#B7791F"
        st.markdown(
            f"""
            <div class="timeline-card">
                <div style="display:flex; justify-content:space-between; gap:1rem; align-items:center;">
                    <div style="font-weight:700; color:#1f2937;">{event['step']}</div>
                    <div style="color:{status_color}; font-weight:700;">{event['status']}</div>
                </div>
                <div class="timeline-meta">Duration: {event['duration_ms']} ms</div>
                <div style="margin-top:0.35rem; color:#374151;">{event['detail']}</div>
                <div class="timeline-meta" style="margin-top:0.3rem;">Output: {event['output_summary']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_recent_feedback(feedback_items: list[dict], title: str) -> None:
    st.write(title)
    if not feedback_items:
        st.caption("Aucune correction disponible.")
        return
    for item in feedback_items:
        st.write(
            f"- [{item['feedback_type']}] {item['field_name']} -> {item['corrected_value']}"
            f" ({item.get('request_category') or 'run'})"
        )


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
        mode = cols[1].selectbox("Mode", list(MODE_LABELS.keys()), format_func=lambda value: MODE_LABELS[value])
        preferred_output = cols[2].selectbox("Preferred output", ["auto", "email_reply", "report"])
        st.caption("V2 remains single-flow and safe: no real email sending, no irreversible action, validation stays visible.")
        st.markdown("</div>", unsafe_allow_html=True)
    with sample_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Provider")
        provider_state = "enabled" if settings.llm_enabled and settings.llm_api_key else "fallback local"
        st.write(f"Provider: `{settings.llm_provider}`")
        st.write(f"Model: `{settings.llm_model}`")
        st.write(f"Mode: `{provider_state}`")
        st.subheader("Autonomy Modes")
        for mode_key, description in MODE_DESCRIPTIONS.items():
            st.markdown(f'<div class="mode-box"><strong>{MODE_LABELS[mode_key]}</strong><br>{description}</div>', unsafe_allow_html=True)
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

        left, center, right = st.columns([1.1, 1.35, 1.05])

        with left:
            _render_explainability(detail)
            _render_score_panel(detail)

        with center:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("### Resultat")
            st.write("Summary")
            st.info(detail["summary"])
            st.write("Extracted fields")
            st.json(detail["extracted_fields"])
            st.write("Generated output")
            st.code(detail["generated_output"], language="markdown")
            st.write("Heuristic reuse")
            if detail["used_preferences"]:
                _render_pills(detail["used_preferences"])
            else:
                st.caption("Aucune preference heuristique reutilisee pour ce run.")

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
                feedback_type = st.selectbox(
                    "Type de correction",
                    ["category", "priority", "tone", "extracted_field"],
                    key="feedback_type",
                )
                field_options = {
                    "category": ["category"],
                    "priority": ["priority"],
                    "tone": ["tone"],
                    "extracted_field": ["subject", "deadline", "actor", "action_requested", "channel"],
                }
                field_name = st.selectbox("Champ", field_options[feedback_type], key="feedback_field_name")
                corrected_value = st.text_area("Valeur corrigee", height=100)
                comment = st.text_input("Commentaire")
                if st.button("Enregistrer la correction", use_container_width=True):
                    _, error = _safe_call(
                        "POST",
                        f"/api/v1/runs/{run_id}/feedback",
                        {
                            "field_name": field_name,
                            "feedback_type": feedback_type,
                            "corrected_value": corrected_value,
                            "comment": comment,
                        },
                    )
                    if error:
                        st.error(error)
                    else:
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            _render_timeline(detail)
            st.markdown("### Review")
            st.metric("Status", detail["status"])
            st.metric("Risk", detail["risk_level"])
            st.metric("Saved time", f"{detail['estimated_time_saved_minutes']} min")
            st.write("Autonomy recommendation:", detail["autonomy_mode"])
            _render_recent_feedback(feedback_items, "Learning from corrections")
            _render_recent_feedback(detail["recent_category_feedback"], "Latest corrections for this category")
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
                "requested_mode": item["requested_mode"],
                "recommended_mode": item["autonomy_mode"],
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

    cols = st.columns(4)
    cols[0].metric("Runs", metrics["total_runs"])
    cols[1].metric("Approval rate", metrics["approval_rate"])
    cols[2].metric("Average score", metrics["average_score"])
    avg_latency = round(sum(metrics["average_step_latency_ms"].values()) / len(metrics["average_step_latency_ms"]), 2) if metrics["average_step_latency_ms"] else 0
    cols[3].metric("Avg step latency", f"{avg_latency} ms")

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Category distribution")
        category_df = pd.DataFrame(
            [{"category": key, "runs": value} for key, value in metrics["category_distribution"].items()]
        )
        if not category_df.empty:
            st.bar_chart(category_df.set_index("category"))
            st.dataframe(category_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucune donnee disponible.")
        st.markdown("### Autonomy mode distribution")
        mode_df = pd.DataFrame(
            [{"mode": key, "runs": value} for key, value in metrics["autonomy_mode_distribution"].items()]
        )
        if not mode_df.empty:
            st.bar_chart(mode_df.set_index("mode"))
            st.dataframe(mode_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucune donnee disponible.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Top feedbacks frequents")
        feedback_df = pd.DataFrame(
            [{"feedback": key, "count": value} for key, value in metrics["frequent_feedback"].items()]
        )
        if not feedback_df.empty:
            st.dataframe(feedback_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucun feedback frequemment detecte.")
        st.markdown("### Average latency by step")
        latency_df = pd.DataFrame(
            [{"step": key, "avg_latency_ms": value} for key, value in metrics["average_step_latency_ms"].items()]
        )
        if not latency_df.empty:
            st.dataframe(latency_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucune latence de run disponible.")
        st.markdown("### Risk distribution")
        risk_df = pd.DataFrame(
            [{"risk": key, "runs": value} for key, value in metrics["risk_distribution"].items()]
        )
        if not risk_df.empty:
            st.dataframe(risk_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucune distribution de risque disponible.")
        st.markdown("</div>", unsafe_allow_html=True)
