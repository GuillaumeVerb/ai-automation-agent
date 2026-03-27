GLOBAL_CSS = """
<style>
:root {
    --bg-base: #f4f2ee;
    --bg-soft: rgba(255, 255, 255, 0.76);
    --bg-strong: rgba(255, 255, 255, 0.9);
    --text-strong: #111827;
    --text-muted: #5f6471;
    --line-soft: rgba(17, 24, 39, 0.08);
    --line-strong: rgba(17, 24, 39, 0.14);
    --accent: #0f172a;
    --accent-soft: #e8ecf8;
    --blue-soft: #eef4ff;
    --green-soft: #ecfdf3;
    --amber-soft: #fff7e8;
    --red-soft: #fff1f1;
    --shadow-soft: 0 24px 60px rgba(15, 23, 42, 0.08);
    --radius-xl: 28px;
    --radius-lg: 22px;
    --radius-md: 16px;
    --radius-sm: 12px;
}

.stApp {
    color: var(--text-strong);
    font-family: "Avenir Next", "Segoe UI", sans-serif;
    background:
        radial-gradient(circle at top left, rgba(129, 170, 255, 0.20), transparent 32%),
        radial-gradient(circle at top right, rgba(255, 210, 163, 0.24), transparent 28%),
        linear-gradient(180deg, #f7f5f0 0%, #f1efe9 100%);
}

.block-container {
    max-width: 1720px;
    padding-top: 1.55rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.68));
    border-right: 1px solid var(--line-soft);
    min-width: 228px;
}

[data-testid="stSidebar"] * {
    color: var(--text-strong);
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 0.45rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 0.5rem 0.55rem;
    border-radius: 12px;
    transition: background 160ms ease, border-color 160ms ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(15, 23, 42, 0.04);
}

h1, h2, h3, h4, h5 {
    color: var(--text-strong);
    letter-spacing: -0.03em;
}

.hero-shell {
    padding: 1.32rem 1.45rem;
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: var(--radius-xl);
    background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.80), rgba(255, 255, 255, 0.58)),
        linear-gradient(135deg, rgba(232, 236, 248, 0.75), rgba(246, 240, 231, 0.2));
    box-shadow: var(--shadow-soft);
    margin-bottom: 0.95rem;
}

.top-controls {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.8rem;
}

.lang-shell {
    min-width: 220px;
    padding: 0.7rem 0.85rem 0.55rem;
    border-radius: 18px;
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.72);
    box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
}

.lang-label {
    margin-bottom: 0.45rem;
    color: #64748b;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
}

.hero-topline {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 0.85rem;
}

.eyebrow {
    display: inline-block;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    font-weight: 700;
}

.hero-title {
    font-size: 2.46rem;
    line-height: 1.05;
    margin: 0;
    color: #0f172a;
    max-width: 780px;
}

.hero-copy {
    margin: 0.65rem 0 1rem;
    max-width: 860px;
    color: #475569;
    font-size: 0.98rem;
    line-height: 1.62;
}

.hero-value-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.85rem;
    margin-top: 1rem;
}

.hero-value-card {
    padding: 0.95rem 1rem;
    border-radius: var(--radius-md);
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid var(--line-soft);
}

.hero-value-title {
    color: #0f172a;
    font-size: 0.96rem;
    font-weight: 700;
}

.hero-value-copy {
    margin-top: 0.35rem;
    color: #64748b;
    line-height: 1.55;
    font-size: 0.88rem;
}

.hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.85fr);
    gap: 1.1rem;
    align-items: stretch;
}

.hero-stat-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.8rem;
    align-content: end;
}

.stat-chip {
    padding: 0.95rem 1rem;
    border-radius: var(--radius-md);
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid var(--line-soft);
}

.stat-label {
    font-size: 0.77rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.stat-value {
    margin-top: 0.35rem;
    font-size: 1.08rem;
    font-weight: 700;
    color: #0f172a;
}

.panel-title {
    margin: 0.15rem 0 0.35rem;
    color: #0f172a;
    font-size: 1.25rem;
    font-weight: 700;
}

.panel-copy {
    margin: 0 0 1rem;
    color: var(--text-muted);
    line-height: 1.6;
}

.soft-card {
    padding: 1.05rem 1.1rem;
    border-radius: var(--radius-lg);
    background: var(--bg-soft);
    border: 1px solid var(--line-soft);
    box-shadow: var(--shadow-soft);
    margin-bottom: 0.9rem;
}

.strong-card {
    padding: 1.12rem 1.16rem;
    border-radius: var(--radius-lg);
    background: var(--bg-strong);
    border: 1px solid var(--line-soft);
    box-shadow: var(--shadow-soft);
    margin-bottom: 1rem;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
}

.kpi-card {
    padding: 0.95rem 1rem;
    border-radius: var(--radius-md);
    background: rgba(249, 250, 251, 0.94);
    border: 1px solid var(--line-soft);
}

.kpi-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #0f172a;
}

.kpi-label {
    margin-top: 0.2rem;
    color: #64748b;
    font-size: 0.86rem;
}

.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.68rem;
    border-radius: 999px;
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.82);
    color: #334155;
    font-size: 0.82rem;
    font-weight: 600;
}

.pill-strong {
    background: #0f172a;
    color: white;
    border-color: #0f172a;
}

.pill-blue {
    background: var(--blue-soft);
    color: #2958a5;
}

.pill-green {
    background: var(--green-soft);
    color: #1f7a49;
}

.pill-amber {
    background: var(--amber-soft);
    color: #9a6700;
}

.pill-red {
    background: var(--red-soft);
    color: #b42318;
}

.mode-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.8rem;
}

.mode-card {
    padding: 1rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.72);
    min-height: 168px;
}

.mode-card-selected {
    border-color: rgba(37, 99, 235, 0.35);
    background: linear-gradient(180deg, rgba(238, 244, 255, 0.95), rgba(255, 255, 255, 0.92));
    box-shadow: 0 14px 36px rgba(37, 99, 235, 0.10);
}

.mode-card-recommended {
    border-color: rgba(46, 155, 95, 0.32);
}

.mode-index {
    font-size: 0.78rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748b;
    font-weight: 700;
}

.mode-name {
    margin-top: 0.4rem;
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
}

.mode-copy {
    margin-top: 0.4rem;
    color: #475569;
    line-height: 1.55;
    font-size: 0.9rem;
    max-width: 34ch;
}

.timeline {
    position: relative;
    margin-top: 0.9rem;
}

.timeline:before {
    content: "";
    position: absolute;
    left: 16px;
    top: 8px;
    bottom: 10px;
    width: 2px;
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.14), rgba(15, 23, 42, 0.04));
}

.timeline-step {
    position: relative;
    margin-left: 0;
    padding: 0 0 0.95rem 2.65rem;
}

.timeline-premium {
    display: grid;
    gap: 0.8rem;
}

.timeline-step-card {
    position: relative;
    display: grid;
    grid-template-columns: 30px 1fr;
    gap: 0.95rem;
    padding: 1rem 1.05rem;
    border-radius: 18px;
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.82);
}

.timeline-step-card-active {
    border-color: rgba(183, 121, 31, 0.26);
    background: linear-gradient(180deg, rgba(255, 247, 232, 0.96), rgba(255, 255, 255, 0.94));
    box-shadow: 0 16px 32px rgba(183, 121, 31, 0.08);
}

.timeline-dot {
    width: 22px;
    height: 22px;
    border-radius: 999px;
    border: 1px solid rgba(15, 23, 42, 0.10);
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    color: #475569;
}

.pulse-dot {
    box-shadow: 0 0 0 0 rgba(183, 121, 31, 0.45);
    animation: pulse-ring 1.8s infinite;
}

@keyframes pulse-ring {
    0% {
        box-shadow: 0 0 0 0 rgba(183, 121, 31, 0.42);
    }
    70% {
        box-shadow: 0 0 0 12px rgba(183, 121, 31, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(183, 121, 31, 0);
    }
}

.timeline-dot-completed {
    background: #eaf8f0;
    color: #1f7a49;
}

.timeline-dot-pending {
    background: #fff7e8;
    color: #9a6700;
}

.timeline-dot-neutral {
    background: #eef4ff;
    color: #2958a5;
}

.timeline-step-title {
    display: flex;
    justify-content: space-between;
    gap: 0.7rem;
    align-items: baseline;
    color: #111827;
    font-weight: 700;
}

.timeline-step-content {
    min-width: 0;
}

.timeline-step-duration {
    color: #64748b;
    font-size: 0.82rem;
    font-weight: 600;
}

.timeline-step-meta {
    margin-top: 0.18rem;
    color: #64748b;
    font-size: 0.84rem;
}

.timeline-step-output {
    margin-top: 0.34rem;
    color: #334155;
    font-size: 0.92rem;
    line-height: 1.5;
}

.decision-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.7rem;
}

.decision-card {
    padding: 0.95rem 1rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.82);
}

.decision-label {
    color: #64748b;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.decision-value {
    margin-top: 0.32rem;
    color: #111827;
    font-size: 1.02rem;
    font-weight: 700;
}

.result-section {
    padding: 1rem 1.05rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.84);
    margin-bottom: 0.85rem;
}

.review-banner {
    padding: 1rem 1.05rem;
    border-radius: var(--radius-lg);
    border: 1px solid rgba(37, 99, 235, 0.12);
    background: linear-gradient(135deg, rgba(238, 244, 255, 0.92), rgba(255, 255, 255, 0.96));
    box-shadow: var(--shadow-soft);
    margin-bottom: 1rem;
}

.review-banner-title {
    margin: 0.2rem 0 0.35rem;
    color: #0f172a;
    font-size: 1.16rem;
    font-weight: 800;
}

.review-banner-copy {
    margin: 0;
    color: #5f6471;
    line-height: 1.58;
}

.result-emphasis {
    padding: 0.95rem 1rem;
    border-radius: var(--radius-md);
    background: rgba(239, 246, 255, 0.78);
    border: 1px solid rgba(96, 165, 250, 0.16);
    color: #1e3a8a;
    line-height: 1.6;
    margin-bottom: 0.85rem;
}

.result-success {
    padding: 0.95rem 1rem;
    border-radius: var(--radius-md);
    background: rgba(236, 253, 243, 0.9);
    border: 1px solid rgba(52, 211, 153, 0.16);
    color: #166534;
    line-height: 1.6;
    margin-bottom: 0.85rem;
    font-weight: 600;
}

.section-header {
    margin-bottom: 0.5rem;
}

.section-title {
    margin: 0;
    color: #111827;
    font-size: 1rem;
    font-weight: 700;
}

.section-copy {
    margin: 0.2rem 0 0;
    color: #64748b;
    line-height: 1.5;
    font-size: 0.9rem;
}

.empty-state {
    padding: 1.55rem 1.3rem;
    border-radius: var(--radius-lg);
    border: 1px dashed rgba(15, 23, 42, 0.18);
    background: rgba(255, 255, 255, 0.55);
}

.live-banner {
    padding: 1.15rem 1.2rem;
    border-radius: var(--radius-lg);
    border: 1px solid var(--line-soft);
    box-shadow: var(--shadow-soft);
    margin-bottom: 0.95rem;
}

.live-banner-blue {
    background: linear-gradient(135deg, rgba(238, 244, 255, 0.96), rgba(255, 255, 255, 0.94));
}

.live-banner-green {
    background: linear-gradient(135deg, rgba(236, 253, 243, 0.96), rgba(255, 255, 255, 0.94));
}

.live-banner-amber {
    background: linear-gradient(135deg, rgba(255, 247, 232, 0.96), rgba(255, 255, 255, 0.94));
}

.live-banner-top {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: center;
    margin-bottom: 0.7rem;
    flex-wrap: wrap;
}

.live-banner-title {
    color: #0f172a;
    font-size: 1.18rem;
    font-weight: 800;
}

.live-banner-copy {
    margin-top: 0.3rem;
    color: #5f6471;
    line-height: 1.6;
}

.live-progress-pill {
    padding: 0.34rem 0.64rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid var(--line-soft);
    color: #334155;
    font-size: 0.8rem;
    font-weight: 700;
}

.live-progress-track {
    margin-top: 0.9rem;
    height: 8px;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.08);
    overflow: hidden;
}

.live-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #2f6bff 0%, #0f172a 100%);
}

.live-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 0.9rem;
}

.live-meta-card {
    padding: 0.82rem 0.9rem;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--line-soft);
}

.live-meta-label {
    color: #64748b;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
}

.live-meta-value {
    margin-top: 0.32rem;
    color: #0f172a;
    font-size: 0.94rem;
    font-weight: 700;
}

.empty-title {
    margin: 0 0 0.35rem;
    color: #0f172a;
    font-size: 1.08rem;
    font-weight: 700;
}

.empty-copy {
    margin: 0;
    color: #64748b;
    line-height: 1.6;
}

.history-item {
    padding: 1rem 1.05rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.82);
    margin-bottom: 0.8rem;
}

[data-testid="stTextArea"] textarea {
    min-height: 220px;
}

.history-meta {
    color: #64748b;
    font-size: 0.88rem;
}

[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input {
    border-radius: 16px !important;
    border: 1px solid var(--line-soft) !important;
    background: rgba(255, 255, 255, 0.84) !important;
    box-shadow: none !important;
}

[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    border-color: rgba(37, 99, 235, 0.45) !important;
    box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.15) !important;
}

button[kind="primary"] {
    border-radius: 16px !important;
    border: 1px solid #0f172a !important;
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%) !important;
    color: white !important;
    min-height: 2.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em;
    box-shadow: 0 14px 28px rgba(15, 23, 42, 0.16);
}

[data-testid="stSegmentedControl"] {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 14px;
    padding: 0.2rem;
    border: 1px solid var(--line-soft);
}

[data-testid="stSegmentedControl"] button {
    border-radius: 10px !important;
    min-height: 2.25rem !important;
    font-weight: 700 !important;
}

button[kind="secondary"] {
    border-radius: 14px !important;
    border: 1px solid var(--line-soft) !important;
    background: rgba(255, 255, 255, 0.82) !important;
    color: #0f172a !important;
    min-height: 2.7rem !important;
    font-weight: 600 !important;
}

button[kind="primary"]:hover,
button[kind="secondary"]:hover {
    border-color: rgba(15, 23, 42, 0.22) !important;
}

div[data-testid="stMetric"] {
    padding: 0.9rem 1rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--line-soft);
    background: rgba(255, 255, 255, 0.82);
}

div[data-testid="stMetric"] label {
    color: #64748b !important;
}

div[data-testid="stAlert"] {
    border-radius: var(--radius-md);
}

@media (max-width: 1080px) {
    .hero-grid,
    .hero-value-grid,
    .mode-grid,
    .decision-grid,
    .hero-stat-grid,
    .kpi-grid,
    .live-meta-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


MODE_META = {
    "suggestion_only": {
        "index": "Mode 0",
        "label": "Suggestion only",
        "description": "The agent analyzes and drafts, but every decision remains fully manual.",
    },
    "assisted": {
        "index": "Mode 1",
        "label": "Assisted",
        "description": "The agent structures the request, proposes output, then waits for human validation.",
    },
    "low_risk_auto": {
        "index": "Mode 2",
        "label": "Low-risk auto",
        "description": "The workflow simulates autonomous execution for low-risk cases while keeping review visible.",
    },
}


STEP_META = {
    "input_received": {"label": "Input received", "short": "IN"},
    "preprocessed": {"label": "Preprocessing", "short": "PR"},
    "classified": {"label": "Classification", "short": "CL"},
    "extracted": {"label": "Extraction", "short": "EX"},
    "strategy_selection": {"label": "Strategy selection", "short": "ST"},
    "generated": {"label": "Generation", "short": "GE"},
    "scored": {"label": "Scoring", "short": "SC"},
    "reviewed": {"label": "Awaiting validation", "short": "RV"},
    "saved": {"label": "Persistence", "short": "SV"},
}
