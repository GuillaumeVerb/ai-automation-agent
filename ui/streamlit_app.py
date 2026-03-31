import html
import json
import time
import textwrap
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
import requests
import streamlit as st

from app.core.config import get_settings
from ui.design_system import GLOBAL_CSS, STEP_META
from ui.i18n import available_languages, get_lang, init_i18n, t


settings = get_settings()
API_BASE_URL = settings.ui_api_base_url.rstrip("/")
DEMO_REQUESTS_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_requests.json"
PAGE_KEYS = ["execution", "result", "history", "analytics"]
MODE_KEYS = ["suggestion_only", "assisted", "low_risk_auto"]
INPUT_TYPES = ["email", "text", "json"]
OUTPUT_TYPES = ["auto", "email_reply", "report"]
CATEGORY_FILTERS = ["all", "support", "reporting", "commercial", "administratif", "autre"]
STATUS_FILTERS = ["all", "processing", "pending_review", "approved", "failed"]
FEEDBACK_TYPES = ["category", "priority", "tone", "extracted_field"]
REGENERATE_OUTPUTS = ["report", "email_reply"]


st.set_page_config(page_title="AI Automation Agent", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def _load_demo_requests() -> list[dict[str, Any]]:
    try:
        return json.loads(DEMO_REQUESTS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return []


def _api_get(path: str) -> Union[dict[str, Any], list[dict[str, Any]]]:
    response = requests.get(f"{API_BASE_URL}{path}", timeout=15)
    response.raise_for_status()
    return response.json()


def _api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def _safe_call(method: str, path: str, payload: Optional[dict[str, Any]] = None) -> tuple[Any, Optional[str]]:
    try:
        if method == "GET":
            return _api_get(path), None
        return _api_post(path, payload or {}), None
    except requests.RequestException as exc:
        return None, str(exc)


def _escape(value: Any) -> str:
    return html.escape(str(value))


def _html_block(content: str) -> str:
    return textwrap.dedent(content).strip()


def _badge(text: str, tone: str = "neutral", strong: bool = False) -> str:
    classes = ["pill"]
    tone_map = {
        "blue": "pill-blue",
        "green": "pill-green",
        "amber": "pill-amber",
        "red": "pill-red",
    }
    if tone in tone_map:
        classes.append(tone_map[tone])
    if strong:
        classes.append("pill-strong")
    return f'<span class="{" ".join(classes)}">{_escape(text)}</span>'


def _translated_value(prefix: str, value: str, fallback: Optional[str] = None) -> str:
    translated = t(f"{prefix}.{value}")
    if translated == f"{prefix}.{value}":
        return fallback or value
    return translated


def _format_datetime(raw_value: str) -> str:
    if not raw_value:
        return "-"
    formatted = raw_value.replace("T", " ").replace("Z", "")
    return formatted[:19]


def _provider_mode_label() -> str:
    if settings.llm_enabled and settings.llm_api_key:
        return t("provider.live")
    return t("provider.local")


def _risk_tone(risk_level: str) -> str:
    return {"low": "green", "medium": "amber", "high": "red"}.get(risk_level, "blue")


def _status_tone(status: str) -> str:
    return {"approved": "green", "pending_review": "amber", "failed": "red"}.get(status, "blue")


def _mode_index(mode_key: str) -> str:
    return t(f"mode.{mode_key}.index")


def _mode_label(mode_key: str) -> str:
    return t(f"mode.{mode_key}.label")


def _mode_description(mode_key: str) -> str:
    return t(f"mode.{mode_key}.description")


def _category_label(category: str) -> str:
    return _translated_value("category", category, category)


def _status_label(status: str) -> str:
    return _translated_value("status", status, status.replace("_", " "))


def _risk_label(risk: str) -> str:
    return _translated_value("risk", risk, risk)


def _output_label(output_type: str) -> str:
    return _translated_value("output", output_type, output_type)


def _input_type_label(input_type: str) -> str:
    return _translated_value("input.type", input_type, input_type)


def _strategy_label(strategy: str) -> str:
    fallback = strategy.replace("_", " ")
    return _translated_value("strategy", strategy, fallback)


def _field_label(field_name: str) -> str:
    fallback = field_name.replace("_", " ").title()
    return _translated_value("field", field_name, fallback)


def _feedback_type_label(feedback_type: str) -> str:
    return _translated_value("feedback", feedback_type, feedback_type)


def _recommended_next_action(detail: dict[str, Any]) -> str:
    if detail["status"] == "processing":
        return t("next_action.processing")
    if detail["status"] == "failed":
        return t("next_action.failed")
    if detail["status"] == "approved":
        return t("next_action.approved")
    if detail["risk_level"] == "high":
        return t("next_action.high_risk")
    if detail["output_type"] == "email_reply":
        return t("next_action.email_reply")
    return t("next_action.report")


def _hero_value_cards() -> str:
    cards = [
        ("hero.value.speed.title", "hero.value.speed.copy"),
        ("hero.value.decision.title", "hero.value.decision.copy"),
        ("hero.value.control.title", "hero.value.control.copy"),
    ]
    return "".join(
        f"""
        <div class="hero-value-card">
            <div class="hero-value-title">{_escape(t(title_key))}</div>
            <div class="hero-value-copy">{_escape(t(copy_key))}</div>
        </div>
        """
        for title_key, copy_key in cards
    )


def _render_language_switch() -> None:
    current = get_lang()
    st.markdown('<div class="top-controls"><div class="lang-shell">', unsafe_allow_html=True)
    st.markdown(f'<div class="lang-label">{_escape(t("language.label"))}</div>', unsafe_allow_html=True)
    languages = available_languages()
    short_labels = {value: t(f"language.option.{value}_short") for value in languages}
    if hasattr(st, "segmented_control"):
        selected_lang = st.segmented_control(
            t("language.label"),
            languages,
            default=current,
            format_func=lambda value: short_labels[value],
            label_visibility="collapsed",
        )
    else:
        selected_lang = st.radio(
            t("language.label"),
            languages,
            index=languages.index(current),
            format_func=lambda value: short_labels[value],
            horizontal=True,
            label_visibility="collapsed",
        )
    st.markdown("</div></div>", unsafe_allow_html=True)
    if selected_lang != current:
        st.session_state["lang"] = selected_lang
        st.rerun()


def _current_viewer_state(detail: Optional[dict[str, Any]]) -> dict[str, str]:
    if not detail:
        return {
            "badge": t("live.idle.badge"),
            "title": t("live.idle.title"),
            "copy": t("live.idle.copy"),
            "tone": "blue",
            "current": t("live.meta.none"),
            "next": t("step.input_received"),
        }
    if detail["status"] == "processing":
        current_step, next_step = _current_and_next_step(detail)
        return {
            "badge": t("live.running.badge"),
            "title": t("live.running.title"),
            "copy": t("live.processing.copy"),
            "tone": "blue",
            "current": current_step,
            "next": next_step,
        }
    if detail["status"] == "approved":
        return {
            "badge": t("live.approved.badge"),
            "title": t("live.approved.title"),
            "copy": t("live.approved.copy"),
            "tone": "green",
            "current": t("step.saved"),
            "next": t("live.meta.none"),
        }
    return {
        "badge": t("live.pending.badge"),
        "title": t("live.pending.title"),
        "copy": t("live.pending.copy"),
        "tone": "amber",
        "current": t("step.reviewed.pending"),
        "next": t("step.saved"),
    }


def _ordered_step_keys() -> list[str]:
    return [
        "input_received",
        "preprocessed",
        "classified",
        "extracted",
        "strategy_selection",
        "generated",
        "scored",
        "reviewed",
        "saved",
    ]


def _source_step_map(detail: dict[str, Any]) -> dict[str, dict[str, Any]]:
    source_steps = {item["step"]: item for item in detail["timeline"]}
    if any(step in source_steps for step in ["generated", "scored", "reviewed", "saved"]):
        source_steps.setdefault("strategy_selection", {"step": "strategy_selection", "status": "completed", "duration_ms": 0})
    return source_steps


def _current_and_next_step(detail: dict[str, Any]) -> tuple[str, str]:
    source_steps = _source_step_map(detail)
    for index, step_key in enumerate(_ordered_step_keys()):
        if step_key not in source_steps:
            current = t(f"step.{step_key}")
            next_step = t(f"step.{_ordered_step_keys()[index + 1]}") if index + 1 < len(_ordered_step_keys()) else t("live.meta.none")
            return current, next_step
    return t("step.saved"), t("live.meta.none")


def _step_label_from_timeline_event(event: dict[str, Any]) -> str:
    if event["step"] == "reviewed":
        return t("step.reviewed.approved") if event.get("status") == "completed" else t("step.reviewed.pending")
    translated = t(f"step.{event['step']}")
    if translated == f"step.{event['step']}":
        return event["step"].replace("_", " ")
    return translated


def _fetch_run_detail_with_retry(run_id: str, attempts: int = 8) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    last_error: Optional[str] = None
    for _ in range(attempts):
        detail, error = _safe_call("GET", f"/api/v1/runs/{run_id}")
        if not error and detail:
            return detail, None
        last_error = error
        time.sleep(0.12)
    return None, last_error or t("state.run_unavailable", error="timeline not ready")


def _render_live_trace_banner(
    progress_placeholder: Any,
    detail: dict[str, Any],
    completed_events: int,
    total_steps: int,
) -> None:
    current_step, next_step = _current_and_next_step(detail)
    progress_placeholder.markdown(
        _html_block(
            f"""
            <div class="live-banner live-banner-blue">
                <div class="live-banner-top">
                    <div class="badge-row">{_badge(t("live.running.badge"), "blue")}</div>
                    <div class="live-progress-pill">{completed_events}/{total_steps}</div>
                </div>
                <div class="live-banner-title">{_escape(t('live.running.title'))}</div>
                <div class="live-banner-copy">{_escape(t('live.processing.copy'))}</div>
                <div class="live-meta-grid">
                    <div class="live-meta-card">
                        <div class="live-meta-label">{_escape(t('live.meta.current'))}</div>
                        <div class="live-meta-value">{_escape(current_step)}</div>
                    </div>
                    <div class="live-meta-card">
                        <div class="live-meta-label">{_escape(t('live.meta.next'))}</div>
                        <div class="live-meta-value">{_escape(next_step)}</div>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def _apply_stream_event(detail: dict[str, Any], event: dict[str, Any]) -> bool:
    if event.get("type") == "run_status":
        detail["status"] = event.get("run_status", detail.get("status", "processing"))
        return False
    if event.get("type") == "run_snapshot":
        detail["status"] = event.get("run_status", detail.get("status", "processing"))
        detail["category"] = event.get("category", detail.get("category", "autre"))
        detail["confidence"] = event.get("confidence", detail.get("confidence", 0.0))
        detail["summary"] = event.get("summary", detail.get("summary", ""))
        detail["generated_output"] = event.get("generated_output", detail.get("generated_output", ""))
        detail["output_type"] = event.get("output_type", detail.get("output_type", "summary"))
        detail["automation_score"] = event.get("automation_score", detail.get("automation_score", 0))
        detail["risk_level"] = event.get("risk_level", detail.get("risk_level", "low"))
        detail["autonomy_mode"] = event.get("autonomy_mode", detail.get("autonomy_mode", detail.get("requested_mode", "assisted")))
        detail["estimated_time_saved_minutes"] = event.get(
            "estimated_time_saved_minutes",
            detail.get("estimated_time_saved_minutes", 0),
        )
        detail["strategy"] = event.get("strategy", detail.get("strategy", []))
        detail["extracted_fields"] = event.get("extracted_fields", detail.get("extracted_fields", {}))
        detail["used_preferences"] = event.get("used_preferences", detail.get("used_preferences", []))
        return True
    if event.get("type") != "timeline_event":
        return False

    detail["status"] = event.get("run_status", detail.get("status", "processing"))
    timeline = detail.setdefault("timeline", [])
    event_key = (event.get("step"), event.get("status"), event.get("timestamp"))
    existing_keys = {
        (item.get("step"), item.get("status"), item.get("timestamp"))
        for item in timeline
    }
    if event_key in existing_keys:
        return False
    timeline.append(
        {
            "step": event["step"],
            "status": event["status"],
            "detail": event.get("detail", ""),
            "timestamp": event.get("timestamp"),
            "duration_ms": event.get("duration_ms", 0),
            "output_summary": event.get("output_summary", ""),
        }
    )
    return True


def _snapshot_status_message(detail: dict[str, Any]) -> str:
    if detail.get("automation_score", 0) > 0:
        return t("live.snapshot.score", score=detail["automation_score"], mode=_mode_label(detail["autonomy_mode"]))
    if detail.get("generated_output"):
        return t("live.snapshot.output", output=_output_label(detail["output_type"]))
    if detail.get("summary") and detail["summary"] != "Traitement en cours...":
        return t("live.snapshot.summary")
    if detail.get("category") and detail.get("confidence", 0) > 0:
        return t(
            "live.snapshot.classification",
            category=_category_label(detail["category"]),
            confidence=f"{detail['confidence']:.0%}",
        )
    return t("live.snapshot.default")


def _stream_run_trace(
    run_id: str,
    detail: dict[str, Any],
    progress_placeholder: Any,
    status_box: Any,
    progress_bar: Any,
) -> tuple[dict[str, Any], Optional[str]]:
    total_steps = len(_ordered_step_keys())
    completed_events = max(len([event for event in detail.get("timeline", []) if event["step"] != "saved"]), 1)
    _render_live_trace_banner(progress_placeholder, detail, completed_events, total_steps)

    try:
        with requests.get(
            f"{API_BASE_URL}/api/v1/runs/{run_id}/stream",
            stream=True,
            timeout=(5, 60),
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                payload = json.loads(raw_line[6:])
                if payload.get("type") == "error":
                    return detail, payload.get("message", t("state.run_unavailable", error="stream error"))
                appended = _apply_stream_event(detail, payload)
                st.session_state["last_run_detail"] = detail
                completed_events = max(len([event for event in detail.get("timeline", []) if event["step"] != "saved"]), 1)
                _render_live_trace_banner(progress_placeholder, detail, completed_events, total_steps)
                progress_bar.progress(min(int((completed_events / total_steps) * 100), 96))
                if appended and status_box and payload.get("type") == "timeline_event":
                    status_box.write(
                        f"{_step_label_from_timeline_event(payload)}: {payload.get('detail', '')}".strip(": ")
                    )
                elif appended and status_box and payload.get("type") == "run_snapshot":
                    status_box.write(_snapshot_status_message(detail))
                if payload.get("type") == "run_status" and payload.get("run_status") != "processing":
                    break
    except (requests.RequestException, json.JSONDecodeError) as exc:
        return detail, str(exc)

    final_detail, detail_error = _fetch_run_detail_with_retry(run_id)
    if final_detail:
        return final_detail, None
    return detail, detail_error


def _create_run_with_trace(payload: dict[str, Any]) -> tuple[Optional[str], Optional[dict[str, Any]], Optional[str]]:
    progress_placeholder = st.empty()
    status_box = st.status(t("live.status_container"), expanded=True) if hasattr(st, "status") else None
    progress_bar = st.progress(0)

    try:
        progress_placeholder.markdown(
            _html_block(
                f"""
                <div class="live-banner live-banner-blue">
                    <div class="live-banner-top">
                        <div class="badge-row">{_badge(t("live.running.badge"), "blue")}</div>
                        <div class="live-progress-pill">0/1</div>
                    </div>
                    <div class="live-banner-title">{_escape(t('loading.title'))}</div>
                    <div class="live-banner-copy">{_escape(t('loading.copy'))}</div>
                    <div class="live-meta-grid">
                        <div class="live-meta-card">
                            <div class="live-meta-label">{_escape(t('live.meta.current'))}</div>
                            <div class="live-meta-value">{_escape(t('step.input_received'))}</div>
                        </div>
                        <div class="live-meta-card">
                            <div class="live-meta-label">{_escape(t('live.meta.next'))}</div>
                            <div class="live-meta-value">{_escape(t('live.meta.none'))}</div>
                        </div>
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        if status_box:
            status_box.write(t("loading.title"))
        progress_bar.progress(8)

        created, error = _safe_call("POST", "/api/v1/runs", payload)
        if error:
            if status_box:
                status_box.update(label=t("state.api_unavailable", error=error), state="error")
            progress_placeholder.empty()
            progress_bar.empty()
            return None, None, error

        run_id = created["run_id"]
        detail, detail_error = _fetch_run_detail_with_retry(run_id)
        if detail_error or not detail:
            if status_box:
                status_box.update(label=t("notice.run_created"), state="complete")
            progress_placeholder.empty()
            progress_bar.empty()
            return run_id, None, detail_error

        detail, detail_error = _stream_run_trace(run_id, detail, progress_placeholder, status_box, progress_bar)
        if detail_error:
            return run_id, detail, detail_error

        progress_bar.progress(100)
        if status_box:
            status_box.update(label=t("notice.run_created"), state="complete")
        progress_placeholder.empty()
        progress_bar.empty()
        return run_id, detail, None
    finally:
        if not hasattr(st, "status"):
            progress_placeholder.empty()
            progress_bar.empty()


def _localized_step_output(step_key: str, detail: dict[str, Any]) -> str:
    source_steps = _source_step_map(detail)
    if step_key not in source_steps and detail["status"] == "processing":
        if step_key == "strategy_selection":
            return t("step.output.strategy_selection.pending")
        return t("step.output.pending")
    if step_key == "input_received":
        return t("step.output.input_received", input_type=_input_type_label(detail["input_type"]))
    if step_key == "preprocessed":
        return t("step.output.preprocessed")
    if step_key == "classified":
        return t(
            "step.output.classified",
            category=_category_label(detail["category"]),
            confidence=f"{detail['confidence']:.0%}",
        )
    if step_key == "extracted":
        action = detail["extracted_fields"].get("action_requested") or t("misc.na")
        return t("step.output.extracted", action=action)
    if step_key == "strategy_selection":
        return t(
            "step.output.strategy_selection",
            strategy=", ".join(_strategy_label(item) for item in detail["strategy"]),
        )
    if step_key == "generated":
        return t("step.output.generated", output=_output_label(detail["output_type"]))
    if step_key == "scored":
        return t(
            "step.output.scored",
            score=detail["automation_score"],
            mode=_mode_label(detail["autonomy_mode"]),
        )
    if detail["status"] == "approved":
        return t("step.output.reviewed.approved")
    return t("step.output.reviewed.pending")


def _build_run_steps(detail: dict[str, Any]) -> list[dict[str, Any]]:
    source_steps = _source_step_map(detail)
    review_label = t("step.reviewed.approved") if detail["status"] == "approved" else t("step.reviewed.pending")

    ordered_steps = []
    current_processing_step, _ = _current_and_next_step(detail)
    for step_key in _ordered_step_keys()[:-1]:
        if step_key in source_steps:
            source_status = source_steps[step_key].get("status", "completed")
            display_status = "completed" if source_status == "completed" else source_status
            if step_key == "reviewed" and detail["status"] == "approved":
                display_status = "completed"
            ordered_steps.append(
                {
                    "step": step_key,
                    "status": display_status,
                    "duration_ms": source_steps[step_key].get("duration_ms", 0),
                    "display_label": review_label if step_key == "reviewed" else None,
                }
            )
            continue

        pending_status = "pending"
        if detail["status"] == "processing" and t(f"step.{step_key}") == current_processing_step:
            pending_status = "processing"
        ordered_steps.append(
            {
                "step": step_key,
                "status": pending_status,
                "duration_ms": 0,
                "display_label": review_label if step_key == "reviewed" else None,
            }
        )

    normalized = []
    for item in ordered_steps:
        step_key = item["step"]
        normalized.append(
            {
                "short": STEP_META[step_key]["short"],
                "label": item.get("display_label", t(f"step.{step_key}")),
                "status": item["status"],
                "status_label": _status_label(item["status"]),
                "duration_ms": item["duration_ms"],
                "output_summary": _localized_step_output(step_key, detail),
            }
        )
    return normalized


def _render_hero(detail: Optional[dict[str, Any]]) -> None:
    lang = get_lang().upper()
    run_status = _status_label(detail["status"]) if detail else t("hero.run.none")
    model_label = settings.llm_model if settings.llm_model else t("misc.na")
    autonomy_label = _mode_label(detail["autonomy_mode"]) if detail else _mode_label(st.session_state["mode_value"])
    current_output = _output_label(detail["output_type"]) if detail else t("hero.output.awaiting")

    summary_badges = [
        _badge(t("hero.badge"), "blue", strong=True),
        _badge(_provider_mode_label(), "green" if settings.llm_enabled and settings.llm_api_key else "amber"),
        _badge(f"Model: {model_label}", "blue"),
        _badge(f"API: {API_BASE_URL}", "blue"),
        _badge(t("language.badge", lang=lang), "blue"),
    ]
    stats = [
        (t("hero.stat.run_status"), run_status),
        (t("hero.stat.requested_mode"), autonomy_label),
        (t("hero.stat.current_output"), current_output),
    ]
    stat_cards = "".join(
        f"""
        <div class="stat-chip">
            <div class="stat-label">{_escape(label)}</div>
            <div class="stat-value">{_escape(value)}</div>
        </div>
        """
        for label, value in stats
    )
    st.markdown(
        _html_block(
            f"""
            <div class="hero-shell">
                <div class="hero-topline">
                    <div class="eyebrow">{_escape(t("hero.eyebrow"))}</div>
                    <div class="badge-row">{''.join(summary_badges)}</div>
                </div>
                <div class="hero-grid">
                    <div>
                        <h1 class="hero-title">{_escape(t("hero.title"))}</h1>
                        <p class="hero-copy">{_escape(t("hero.copy"))}</p>
                        <div class="hero-value-grid">{_hero_value_cards()}</div>
                    </div>
                    <div class="hero-stat-grid">{stat_cards}</div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def _render_section_intro(title: str, copy: str, eyebrow: str) -> None:
    st.markdown(
        f"""
        <div class="strong-card">
            <div class="eyebrow">{_escape(eyebrow)}</div>
            <div class="panel-title">{_escape(title)}</div>
            <p class="panel-copy">{_escape(copy)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_mode_cards(selected_mode: str, recommended_mode: Optional[str]) -> None:
    cards = []
    for mode_key in MODE_KEYS:
        classes = ["mode-card"]
        if mode_key == selected_mode:
            classes.append("mode-card-selected")
        if recommended_mode and mode_key == recommended_mode:
            classes.append("mode-card-recommended")
        footer_badges = []
        if mode_key == selected_mode:
            footer_badges.append(_badge(t("mode.badge.selected"), "blue"))
        if recommended_mode and mode_key == recommended_mode:
            footer_badges.append(_badge(t("mode.badge.recommended"), "green"))
        cards.append(
            _html_block(
                f"""
                <div class="{' '.join(classes)}">
                    <div class="mode-index">{_escape(_mode_index(mode_key))}</div>
                    <div class="mode-name">{_escape(_mode_label(mode_key))}</div>
                    <div class="mode-copy">{_escape(_mode_description(mode_key))}</div>
                    <div class="badge-row" style="margin-top:0.7rem;">{''.join(footer_badges)}</div>
                </div>
                """
            )
        )
    st.markdown(
        _html_block(f'<div class="mode-grid">{"".join(cards)}</div>'),
        unsafe_allow_html=True,
    )


def _render_input_panel(detail: Optional[dict[str, Any]]) -> None:
    demo_requests = _load_demo_requests()
    _render_section_intro(
        title=t("section.input.title"),
        copy=t("section.input.copy"),
        eyebrow=t("section.input.eyebrow"),
    )

    if demo_requests:
        demo_options = [-1] + list(range(len(demo_requests)))
        selected_demo = st.selectbox(
            t("input.preset.label"),
            demo_options,
            format_func=lambda value: t("input.preset.none") if value == -1 else f"{value + 1}. {demo_requests[value]['text'][:80]}...",
        )
        if st.button(t("input.preset.load"), use_container_width=True, key="load_preset"):
            if selected_demo != -1:
                payload = demo_requests[selected_demo]
                st.session_state["sample_text_input"] = payload["text"]
                st.session_state["input_type_value"] = payload["input_type"]
                st.session_state["mode_value"] = (
                    "suggestion_only" if payload["mode"] == "suggestion" else payload["mode"]
                )
                st.session_state["preferred_output_value"] = "auto"
                st.rerun()

    st.text_area(
        t("input.request.label"),
        height=260,
        placeholder=t("input.request.placeholder"),
        key="sample_text_input",
    )

    top_cols = st.columns(2)
    with top_cols[0]:
        st.selectbox(
            t("input.type.label"),
            INPUT_TYPES,
            key="input_type_value",
            format_func=_input_type_label,
        )
    with top_cols[1]:
        st.selectbox(
            t("input.output.label"),
            OUTPUT_TYPES,
            key="preferred_output_value",
            format_func=_output_label,
        )

    st.markdown(f"##### {t('input.autonomy.heading')}")
    selected_mode = st.radio(
        t("input.autonomy.label"),
        MODE_KEYS,
        key="mode_value",
        horizontal=True,
        format_func=_mode_label,
        label_visibility="collapsed",
    )
    recommended_mode = detail["autonomy_mode"] if detail else None
    _render_mode_cards(selected_mode, recommended_mode)

    st.caption(t("input.caption"))

    if st.button(t("input.cta"), type="primary", use_container_width=True, key="launch_run"):
        sample_text = st.session_state["sample_text_input"]
        if not sample_text.strip():
            st.warning(t("input.warning.empty"))
        else:
            loading_placeholder = st.empty()
            loading_placeholder.markdown(
                f"""
                <div class="soft-card">
                    <div class="eyebrow">{_escape(t('loading.eyebrow'))}</div>
                    <div class="panel-title">{_escape(t('loading.title'))}</div>
                    <p class="panel-copy">{_escape(t('loading.copy'))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            run_id, detail, error = _create_run_with_trace(
                {
                    "text": sample_text,
                    "input_type": st.session_state["input_type_value"],
                    "mode": st.session_state["mode_value"],
                    "preferred_output": None
                    if st.session_state["preferred_output_value"] == "auto"
                    else st.session_state["preferred_output_value"],
                }
            )
            loading_placeholder.empty()
            if run_id:
                st.session_state["last_run_id"] = run_id
                if detail:
                    st.session_state["last_run_detail"] = detail
            if error:
                st.warning(error)
            else:
                st.session_state["run_notice"] = t("notice.run_created")
                st.rerun()


def _render_run_viewer(detail: Optional[dict[str, Any]]) -> None:
    _render_section_intro(
        title=t("section.run_viewer.title"),
        copy=t("section.run_viewer.copy"),
        eyebrow=t("section.run_viewer.eyebrow"),
    )

    if not detail:
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('run.empty.title'))}</div>
                <p class="empty-copy">{_escape(t('run.empty.copy'))}</p>
                <p class="empty-copy" style="margin-top:0.7rem;">{_escape(t('run.empty.blueprint'))}</p>
                <div class="badge-row" style="margin-top:0.95rem;">
                    {_badge(t('step.input_received'), 'blue')}
                    {_badge(t('step.preprocessed'), 'blue')}
                    {_badge(t('step.classified'), 'amber')}
                    {_badge(t('step.extracted'), 'amber')}
                    {_badge(t('step.strategy_selection'), 'blue')}
                    {_badge(t('step.generated'), 'green')}
                    {_badge(t('step.scored'), 'blue')}
                    {_badge(t('step.reviewed.pending'), 'amber')}
                    {_badge(t('step.saved'), 'green')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    viewer_state = _current_viewer_state(detail)
    built_steps = _build_run_steps(detail)
    total_steps = 9
    source_steps = _source_step_map(detail)
    if detail["status"] == "processing":
        active_step = next((key for key in _ordered_step_keys() if key not in _source_step_map(detail)), "saved")
    elif detail["status"] == "pending_review":
        active_step = "reviewed"
    else:
        active_step = "saved"
    saved_status = "completed" if "saved" in source_steps else ("processing" if detail["status"] == "processing" and active_step == "saved" else "pending")
    steps_payload = built_steps + [
        {
            "short": STEP_META["saved"]["short"],
            "label": t("step.saved"),
            "status": saved_status,
            "status_label": _status_label(saved_status),
            "duration_ms": source_steps.get("saved", {}).get("duration_ms", 0),
            "output_summary": t("step.output.saved") if "saved" in source_steps else t("step.output.pending"),
            "step_key": "saved",
        }
    ]
    completed_steps = len([step for step in steps_payload if step["status"] == "completed"])
    top_badges = "".join(
        [
            _badge(t("run.badge.id", run_id=detail["run_id"][:8]), "blue"),
            _badge(t("run.badge.status", status=_status_label(detail["status"])), _status_tone(detail["status"])),
            _badge(t("run.badge.category", category=_category_label(detail["category"])), "blue"),
            _badge(t("run.badge.risk", risk=_risk_label(detail["risk_level"])), _risk_tone(detail["risk_level"])),
        ]
    )
    st.markdown(
        f"""
        <div class="live-banner live-banner-{viewer_state['tone']}">
            <div class="live-banner-top">
                <div class="badge-row">
                    {_badge(viewer_state['badge'], viewer_state['tone'])}
                    {top_badges}
                </div>
                <div class="live-progress-pill">{completed_steps}/{total_steps}</div>
            </div>
            <div class="live-banner-title">{_escape(viewer_state['title'])}</div>
            <div class="live-banner-copy">{_escape(viewer_state['copy'])}</div>
            <div class="live-meta-grid">
                <div class="live-meta-card">
                    <div class="live-meta-label">{_escape(t('live.meta.current'))}</div>
                    <div class="live-meta-value">{_escape(viewer_state['current'])}</div>
                </div>
                <div class="live-meta-card">
                    <div class="live-meta-label">{_escape(t('live.meta.next'))}</div>
                    <div class="live-meta-value">{_escape(viewer_state['next'])}</div>
                </div>
            </div>
            <div class="live-progress-track">
                <div class="live-progress-fill" style="width:{int((completed_steps / total_steps) * 100)}%;"></div>
            </div>
        </div>
        <div class="soft-card">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(detail['automation_score'])}</div>
                    <div class="kpi-label">{_escape(t('run.kpi.score'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(detail['estimated_time_saved_minutes'])} min</div>
                    <div class="kpi-label">{_escape(t('run.kpi.time_saved'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{completed_steps}/{total_steps}</div>
                    <div class="kpi-label">{_escape(t('run.kpi.progress'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(viewer_state['current'])}</div>
                    <div class="kpi-label">{_escape(t('run.kpi.current_phase'))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps_html = []
    for step in steps_payload:
        step_key = step.get("step_key") or next(
            (key for key, meta in STEP_META.items() if meta["short"] == step["short"]),
            "",
        )
        is_active = step_key == active_step
        dot_class = "timeline-dot timeline-dot-completed"
        row_class = "timeline-step-card"
        if is_active:
            dot_class = "timeline-dot timeline-dot-pending pulse-dot"
            row_class = "timeline-step-card timeline-step-card-active"
        elif step["status"] in {"pending", "processing"}:
            dot_class = "timeline-dot timeline-dot-neutral"
        steps_html.append(
            _html_block(
                f"""
                <div class="{row_class}">
                    <div class="{dot_class}">{_escape(step['short'])}</div>
                    <div class="timeline-step-content">
                        <div class="timeline-step-title">
                            <span>{_escape(step['label'])}</span>
                            <span class="timeline-step-duration">{_escape(step['duration_ms'])} ms</span>
                        </div>
                        <div class="timeline-step-meta">{_escape(step.get('status_label', step['status']))}</div>
                        <div class="timeline-step-output">{_escape(step['output_summary'])}</div>
                    </div>
                </div>
                """
            )
        )
    st.markdown(
        _html_block(
            f"""
            <div class="strong-card">
                <div class="timeline timeline-premium">{"".join(steps_html)}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def _render_decision_panel(detail: Optional[dict[str, Any]]) -> None:
    _render_section_intro(
        title=t("section.decision.title"),
        copy=t("section.decision.copy"),
        eyebrow=t("section.decision.eyebrow"),
    )

    if not detail:
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('decision.empty.title'))}</div>
                <p class="empty-copy">{_escape(t('decision.empty.copy'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    explainability = detail["explainability"]
    cards = [
        (t("decision.card.category"), _category_label(detail["category"])),
        (t("decision.card.confidence"), f"{explainability['confidence']:.0%}"),
        (t("decision.card.risk"), _risk_label(detail["risk_level"])),
        (t("decision.card.output"), _output_label(detail["output_type"])),
    ]
    st.markdown(
        _html_block(
            '<div class="decision-grid">'
            + "".join(
                _html_block(
                    f"""
                    <div class="decision-card">
                        <div class="decision-label">{_escape(label)}</div>
                        <div class="decision-value">{_escape(value)}</div>
                    </div>
                    """
                )
                for label, value in cards
            )
            + "</div>"
        ),
        unsafe_allow_html=True,
    )

    translated_strategy = "".join(_badge(_strategy_label(item), "blue") for item in explainability["strategy"])
    translated_signals = "".join(_badge(item, "amber") for item in explainability["signals"])
    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(t('decision.strategy.title'))}</p>
                <p class="section-copy">{_escape(t('decision.strategy.copy'))}</p>
            </div>
            <div class="badge-row">{translated_strategy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(t('decision.signals.title'))}</p>
                <p class="section-copy">{_escape(t('decision.signals.copy'))}</p>
            </div>
            <div class="badge-row">{translated_signals}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(t('decision.rationale.title'))}</p>
                <p class="section-copy">{_escape(explainability['rationale'])}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_live_artifacts_panel(detail: Optional[dict[str, Any]]) -> None:
    _render_section_intro(
        title=t("section.live_artifacts.title"),
        copy=t("section.live_artifacts.copy"),
        eyebrow=t("section.live_artifacts.eyebrow"),
    )

    if not detail:
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('live_artifacts.empty.title'))}</div>
                <p class="empty-copy">{_escape(t('live_artifacts.empty.copy'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if detail.get("summary") and detail["summary"] != "Traitement en cours...":
        st.markdown(
            f"""
            <div class="result-section">
                <div class="section-header">
                    <p class="section-title">{_escape(t('live_artifacts.summary.title'))}</p>
                    <p class="section-copy">{_escape(t('live_artifacts.summary.copy'))}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="result-emphasis">{_escape(detail["summary"])}</div>', unsafe_allow_html=True)

    extracted_fields = detail.get("extracted_fields") or {}
    visible_fields = {
        key: value
        for key, value in extracted_fields.items()
        if value not in {None, "", "assess_request"}
    }
    if visible_fields:
        st.markdown(
            f"""
            <div class="result-section">
                <div class="section-header">
                    <p class="section-title">{_escape(t('live_artifacts.fields.title'))}</p>
                    <p class="section-copy">{_escape(t('live_artifacts.fields.copy'))}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        artifact_df = pd.DataFrame(
            [
                {
                    t("field.label"): _field_label(key),
                    t("field.value"): value,
                }
                for key, value in visible_fields.items()
            ]
        )
        st.dataframe(artifact_df, use_container_width=True, hide_index=True)

    generated_output = detail.get("generated_output", "").strip()
    if generated_output:
        st.markdown(
            f"""
            <div class="result-section">
                <div class="section-header">
                    <p class="section-title">{_escape(t('live_artifacts.output.title'))}</p>
                    <p class="section-copy">{_escape(t('live_artifacts.output.copy'))}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(generated_output, language="markdown")

    if not visible_fields and not generated_output and (not detail.get("summary") or detail["summary"] == "Traitement en cours..."):
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('live_artifacts.waiting.title'))}</div>
                <p class="empty-copy">{_escape(t('live_artifacts.waiting.copy'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_score_panel(detail: Optional[dict[str, Any]]) -> None:
    if not detail:
        return

    score = detail["score_breakdown"]
    recommended_badges = "".join(
        [
            _badge(t("score.recommended_mode", mode=_mode_label(detail["autonomy_mode"])), "green"),
            _badge(t("score.requested_mode", mode=_mode_label(detail["requested_mode"])), "blue"),
        ]
    )
    st.markdown(
        f"""
        <div class="strong-card">
            <div class="eyebrow">{_escape(t('score.eyebrow'))}</div>
            <div class="panel-title">{_escape(t('score.title'))}</div>
            <p class="panel-copy">{_escape(t('score.copy'))}</p>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(score['global_score'])}</div>
                    <div class="kpi-label">{_escape(t('score.global'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(detail['estimated_time_saved_minutes'])} min</div>
                    <div class="kpi-label">{_escape(t('score.time_saved'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(score['confidence_score'])}</div>
                    <div class="kpi-label">{_escape(t('score.confidence'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(score['risk_score'])}</div>
                    <div class="kpi-label">{_escape(t('score.risk'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(score['completeness_score'])}</div>
                    <div class="kpi-label">{_escape(t('score.completeness'))}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{_escape(_risk_label(detail['risk_level']))}</div>
                    <div class="kpi-label">{_escape(t('score.risk_level'))}</div>
                </div>
            </div>
            <div class="badge-row" style="margin-top:0.9rem;">{recommended_badges}</div>
            <p class="panel-copy" style="margin-top:0.9rem;">{_escape(score['rationale'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _result_feedback_rows(feedback_items: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in feedback_items:
        rows.append(
            {
                t("field.label"): _field_label(item["field_name"]),
                t("actions.correction.type"): _feedback_type_label(item["feedback_type"]),
                t("field.value"): item["corrected_value"],
                t("actions.correction.comment"): item.get("comment") or "-",
            }
        )
    return pd.DataFrame(rows)


def _render_result_sections(detail: Optional[dict[str, Any]], feedback_items: list[dict[str, Any]]) -> None:
    if not detail:
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('result.empty.title'))}</div>
                <p class="empty-copy">{_escape(t('result.empty.copy'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if detail["status"] == "processing":
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('result.processing.title'))}</div>
                <p class="empty-copy">{_escape(t('result.processing.copy'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="strong-card">
            <div class="eyebrow">{_escape(t('section.result.eyebrow'))}</div>
            <div class="panel-title">{_escape(t('section.result.title'))}</div>
            <p class="panel-copy">{_escape(t('section.result.copy'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    status_tone = _status_tone(detail["status"])
    overview_badges = "".join(
        [
            _badge(t("run.badge.id", run_id=detail["run_id"][:8]), "blue"),
            _badge(t("run.badge.status", status=_status_label(detail["status"])), status_tone),
            _badge(t("run.badge.category", category=_category_label(detail["category"])), "blue"),
            _badge(t("run.badge.risk", risk=_risk_label(detail["risk_level"])), _risk_tone(detail["risk_level"])),
        ]
    )
    st.markdown(
        f"""
        <div class="review-banner">
            <div class="eyebrow">{_escape(t('page.result.eyebrow'))}</div>
            <div class="badge-row" style="margin-top:0.55rem;">{overview_badges}</div>
            <div class="review-banner-title">{_escape(t('page.result.lead'))}</div>
            <p class="review-banner-copy">{_escape(t('page.result.copy'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(t('result.summary.title'))}</p>
                <p class="section-copy">{_escape(t('result.summary.copy'))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="result-emphasis">{_escape(detail["summary"])}</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(t('result.fields.title'))}</p>
                <p class="section-copy">{_escape(t('result.fields.copy'))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    extracted_df = pd.DataFrame(
        [
            {
                t("field.label"): _field_label(key),
                t("field.value"): value if value not in {None, ""} else "-",
            }
            for key, value in detail["extracted_fields"].items()
        ]
    )
    st.dataframe(extracted_df, use_container_width=True, hide_index=True)

    output_title = t("result.output.email") if detail["output_type"] == "email_reply" else t("result.output.report")
    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(output_title)}</p>
                <p class="section-copy">{_escape(t('result.output.copy'))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(detail["generated_output"], language="markdown")

    st.markdown(
        f"""
        <div class="result-section">
            <div class="section-header">
                <p class="section-title">{_escape(t('result.next_action.title'))}</p>
                <p class="section-copy">{_escape(t('result.next_action.copy'))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="result-success">{_escape(_recommended_next_action(detail))}</div>',
        unsafe_allow_html=True,
    )

    preference_badges = "".join(_badge(item, "green") for item in detail["used_preferences"])
    if preference_badges:
        st.markdown(
            f"""
            <div class="result-section">
                <div class="section-header">
                    <p class="section-title">{_escape(t('result.reuse.title'))}</p>
                    <p class="section-copy">{_escape(t('result.reuse.copy'))}</p>
                </div>
                <div class="badge-row">{preference_badges}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if feedback_items:
        st.markdown(
            f"""
            <div class="result-section">
                <div class="section-header">
                    <p class="section-title">{_escape(t('result.feedback.title'))}</p>
                    <p class="section-copy">{_escape(t('result.feedback.copy'))}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(_result_feedback_rows(feedback_items), use_container_width=True, hide_index=True)


def _render_action_panel(detail: Optional[dict[str, Any]]) -> None:
    if not detail:
        return

    if detail["status"] == "processing":
        st.info(t("actions.processing_locked"))
        return

    st.markdown(
        f"""
        <div class="strong-card">
            <div class="eyebrow">{_escape(t('section.actions.eyebrow'))}</div>
            <div class="panel-title">{_escape(t('section.actions.title'))}</div>
            <p class="panel-copy">{_escape(t('section.actions.copy'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(t("actions.approve"), use_container_width=True, key="approve_run"):
        _, error = _safe_call("POST", f"/api/v1/runs/{detail['run_id']}/approve", {})
        if error:
            st.error(t("state.api_unavailable", error=error))
        else:
            st.session_state["run_notice"] = t("notice.run_approved")
            st.rerun()

    regenerate_choice = st.selectbox(
        t("actions.regenerate_as"),
        REGENERATE_OUTPUTS,
        key="regenerate_choice",
        format_func=_output_label,
    )
    secondary_actions = st.columns(2, gap="small")
    with secondary_actions[0]:
        if st.button(t("actions.regenerate"), use_container_width=True, key="regenerate_run"):
            data, error = _safe_call(
                "POST",
                f"/api/v1/runs/{detail['run_id']}/regenerate",
                {"preferred_output": regenerate_choice, "strategy_hint": regenerate_choice},
            )
            if error:
                st.error(t("state.api_unavailable", error=error))
            else:
                st.session_state["last_run_id"] = data["run_id"]
                st.session_state["run_notice"] = t("notice.run_regenerated", output=_output_label(regenerate_choice))
                st.rerun()
    with secondary_actions[1]:
        if st.button(t("actions.escalate"), use_container_width=True, key="escalate_run"):
            st.session_state["escalation_note"] = t("actions.escalation.note", run_id=detail["run_id"])

    with st.expander(t("actions.correction.expander"), expanded=False):
        feedback_type = st.selectbox(
            t("actions.correction.type"),
            FEEDBACK_TYPES,
            key="feedback_type",
            format_func=_feedback_type_label,
        )
        field_options = {
            "category": ["category"],
            "priority": ["priority"],
            "tone": ["tone"],
            "extracted_field": ["subject", "deadline", "actor", "action_requested", "channel"],
        }
        field_name = st.selectbox(
            t("actions.correction.field"),
            field_options[feedback_type],
            key="feedback_field_name",
            format_func=_field_label,
        )
        corrected_value = st.text_area(t("actions.correction.value"), height=100, key="feedback_corrected_value")
        comment = st.text_input(t("actions.correction.comment"), key="feedback_comment")
        if st.button(t("actions.correction.save"), use_container_width=True, key="save_feedback"):
            _, error = _safe_call(
                "POST",
                f"/api/v1/runs/{detail['run_id']}/feedback",
                {
                    "field_name": field_name,
                    "feedback_type": feedback_type,
                    "corrected_value": corrected_value,
                    "comment": comment,
                },
            )
            if error:
                st.error(t("state.api_unavailable", error=error))
            else:
                st.session_state["run_notice"] = t("notice.correction_saved")
                st.rerun()

    if st.session_state.get("escalation_note"):
        st.warning(st.session_state["escalation_note"])


def _render_history_page(runs: list[dict[str, Any]]) -> None:
    _render_section_intro(
        title=t("history.title"),
        copy=t("history.copy"),
        eyebrow=t("history.eyebrow"),
    )

    category_filter = st.selectbox(
        t("history.filter.category"),
        CATEGORY_FILTERS,
        format_func=_category_label,
    )
    status_filter = st.selectbox(
        t("history.filter.status"),
        STATUS_FILTERS,
        format_func=lambda value: _translated_value("status", value, value.title()),
    )

    filtered = [
        item
        for item in runs
        if (category_filter == "all" or item["category"] == category_filter)
        and (status_filter == "all" or item["status"] == status_filter)
    ]

    kpis = st.columns(4)
    kpis[0].metric(t("history.kpi.runs"), len(filtered))
    kpis[1].metric(t("history.kpi.approved"), len([item for item in filtered if item["status"] == "approved"]))
    kpis[2].metric(
        t("history.kpi.pending"),
        len([item for item in filtered if item["status"] in {"processing", "pending_review"}]),
    )
    average_score = round(sum(item["automation_score"] for item in filtered) / len(filtered), 1) if filtered else 0
    kpis[3].metric(t("history.kpi.avg_score"), average_score)

    if not filtered:
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="empty-title">{_escape(t('history.empty.title'))}</div>
                <p class="empty-copy">{_escape(t('history.empty.copy'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for item in filtered:
        created_text = t("history.card.created", created_at=_format_datetime(item["created_at"]))
        requested_mode = t("history.card.requested_mode", mode=_mode_label(item["requested_mode"]))
        recommended_mode = t("history.card.recommended_mode", mode=_mode_label(item["autonomy_mode"]))
        st.markdown(
            f"""
            <div class="history-item">
                <div class="badge-row">
                    {_badge(_category_label(item['category']), 'blue')}
                    {_badge(_status_label(item['status']), _status_tone(item['status']))}
                    {_badge(t('misc.score_label', score=item['automation_score']), 'green')}
                    {_badge(_risk_label(item['risk_level']), _risk_tone(item['risk_level']))}
                </div>
                <div class="panel-title" style="margin-top:0.8rem;">Run {item['run_id'][:8]}</div>
                <div class="history-meta">{_escape(created_text)} | {_escape(requested_mode)} | {_escape(recommended_mode)}</div>
                <p class="panel-copy" style="margin-top:0.55rem;">{_escape(item['summary'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(t("history.inspect", run_id=item["run_id"][:8]), expanded=False):
            info_col, output_col = st.columns([0.95, 1.05])
            with info_col:
                st.write(t("history.timeline"))
                for step in _build_run_steps(item):
                    st.write(f"- {step['label']} | {step['status_label']} | {step['output_summary']}")
            with output_col:
                st.write(t("history.output"))
                st.code(item["generated_output"], language="markdown")


def _render_analytics_page(metrics: dict[str, Any], runs: list[dict[str, Any]]) -> None:
    _render_section_intro(
        title=t("analytics.title"),
        copy=t("analytics.copy"),
        eyebrow=t("analytics.eyebrow"),
    )

    avg_latency = (
        round(sum(metrics["average_step_latency_ms"].values()) / len(metrics["average_step_latency_ms"]), 2)
        if metrics["average_step_latency_ms"]
        else 0
    )
    top_cards = st.columns(4)
    top_cards[0].metric(t("analytics.kpi.total_runs"), metrics["total_runs"])
    top_cards[1].metric(t("analytics.kpi.approval_rate"), metrics["approval_rate"])
    top_cards[2].metric(t("analytics.kpi.average_score"), metrics["average_score"])
    top_cards[3].metric(t("analytics.kpi.avg_latency"), f"{avg_latency} ms")

    if runs:
        score_bands = {"0-39": 0, "40-59": 0, "60-79": 0, "80-100": 0}
        for item in runs:
            score = item["automation_score"]
            if score < 40:
                score_bands["0-39"] += 1
            elif score < 60:
                score_bands["40-59"] += 1
            elif score < 80:
                score_bands["60-79"] += 1
            else:
                score_bands["80-100"] += 1
        recent_runs_df = pd.DataFrame(
            [
                {
                    t("analytics.column.run_id"): item["run_id"][:8],
                    t("analytics.column.category"): _category_label(item["category"]),
                    t("analytics.column.score"): item["automation_score"],
                    t("analytics.column.risk"): _risk_label(item["risk_level"]),
                    t("analytics.column.status"): _status_label(item["status"]),
                }
                for item in runs[:8]
            ]
        )
    else:
        score_bands = {}
        recent_runs_df = pd.DataFrame()

    left, right = st.columns(2)
    with left:
        st.markdown(f"### {t('analytics.section.category')}")
        category_df = pd.DataFrame(
            [{"category": _category_label(key), "runs": value} for key, value in metrics["category_distribution"].items()]
        )
        if not category_df.empty:
            st.bar_chart(category_df.set_index("category"))
            st.dataframe(category_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.category"))

        st.markdown(f"### {t('analytics.section.mode')}")
        mode_df = pd.DataFrame(
            [{"mode": _mode_label(key), "runs": value} for key, value in metrics["autonomy_mode_distribution"].items()]
        )
        if not mode_df.empty:
            st.bar_chart(mode_df.set_index("mode"))
            st.dataframe(mode_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.mode"))

        st.markdown(f"### {t('analytics.section.score_bands')}")
        band_df = pd.DataFrame([{"band": key, "runs": value} for key, value in score_bands.items()])
        if not band_df.empty:
            st.bar_chart(band_df.set_index("band"))
            st.dataframe(band_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.score_bands"))

    with right:
        st.markdown(f"### {t('analytics.section.feedback')}")
        feedback_df = pd.DataFrame(
            [{"feedback": key, "count": value} for key, value in metrics["frequent_feedback"].items()]
        )
        if not feedback_df.empty:
            st.dataframe(feedback_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.feedback"))

        st.markdown(f"### {t('analytics.section.latency')}")
        latency_df = pd.DataFrame(
            [{"step": _translated_value("step", key, key), "avg_latency_ms": value} for key, value in metrics["average_step_latency_ms"].items()]
        )
        if not latency_df.empty:
            st.dataframe(latency_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.latency"))

        st.markdown(f"### {t('analytics.section.risk')}")
        risk_df = pd.DataFrame(
            [{"risk": _risk_label(key), "runs": value} for key, value in metrics["risk_distribution"].items()]
        )
        if not risk_df.empty:
            st.bar_chart(risk_df.set_index("risk"))
            st.dataframe(risk_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.risk"))

        st.markdown(f"### {t('analytics.section.snapshot')}")
        if not recent_runs_df.empty:
            st.dataframe(recent_runs_df, use_container_width=True, hide_index=True)
        else:
            st.caption(t("analytics.empty.snapshot"))


def _initialize_state() -> None:
    init_i18n()
    st.session_state.setdefault("sample_text_input", "")
    st.session_state.setdefault("input_type_value", "email")
    st.session_state.setdefault("mode_value", "assisted")
    st.session_state.setdefault("preferred_output_value", "auto")
    st.session_state.setdefault("last_run_detail", None)
    st.session_state.setdefault("run_notice", "")
    st.session_state.setdefault("escalation_note", "")


def _fetch_current_run() -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    run_id = st.session_state.get("last_run_id")
    if not run_id:
        return None, []
    cached_detail = st.session_state.get("last_run_detail")
    detail, detail_error = _safe_call("GET", f"/api/v1/runs/{run_id}")
    feedback_items, feedback_error = _safe_call("GET", f"/api/v1/runs/{run_id}/feedback")
    if detail_error:
        if cached_detail and cached_detail.get("run_id") == run_id:
            detail = cached_detail
        else:
            st.error(t("state.run_unavailable", error=detail_error))
            return None, []
    else:
        st.session_state["last_run_detail"] = detail
    if feedback_error:
        feedback_items = []
    return detail, feedback_items


def _render_run_page() -> None:
    detail, feedback_items = _fetch_current_run()
    _render_hero(detail)

    notice = st.session_state.get("run_notice")
    if notice:
        st.success(notice)
        st.session_state["run_notice"] = ""

    left, center, right = st.columns([1.05, 1.3, 1.05], gap="large")
    with left:
        _render_input_panel(detail)
    with center:
        _render_run_viewer(detail)
    with right:
        _render_decision_panel(detail)
        _render_live_artifacts_panel(detail)
        _render_score_panel(detail)

    st.markdown(
        f"""
        <div class="soft-card" style="margin-top:1rem;">
            <div class="eyebrow">{_escape(t('page.execution.next.eyebrow'))}</div>
            <div class="panel-title">{_escape(t('page.execution.next.title'))}</div>
            <p class="panel-copy">{_escape(t('page.execution.next.copy'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result_page() -> None:
    detail, feedback_items = _fetch_current_run()
    _render_hero(detail)

    notice = st.session_state.get("run_notice")
    if notice:
        st.success(notice)
        st.session_state["run_notice"] = ""

    result_col, action_col = st.columns([1.45, 0.95], gap="large")
    with result_col:
        _render_result_sections(detail, feedback_items)
    with action_col:
        _render_action_panel(detail)


def main() -> None:
    _initialize_state()

    _render_language_switch()
    page = st.sidebar.radio(
        t("nav.label"),
        PAGE_KEYS,
        format_func=lambda value: t(f"nav.{value}"),
    )

    if page == "execution":
        _render_run_page()
        return

    if page == "result":
        _render_result_page()
        return

    if page == "history":
        runs, error = _safe_call("GET", "/api/v1/runs")
        if error:
            st.error(t("state.api_unavailable", error=error))
            return
        _render_hero(None)
        _render_history_page(runs)
        return

    metrics, error = _safe_call("GET", "/api/v1/metrics")
    runs, runs_error = _safe_call("GET", "/api/v1/runs")
    if error:
        st.error(t("state.api_unavailable", error=error))
        return
    if runs_error:
        runs = []
    _render_hero(None)
    _render_analytics_page(metrics, runs)


main()
