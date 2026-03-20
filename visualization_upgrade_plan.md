# AI Data Investigator Visualization Upgrade Plan

## Objective

Upgrade the analytics layer from basic summary outputs to premium, decision-oriented visuals that help users answer:

- What changed?
- Why did it change?
- How severe is it?
- What should I do next?

The target stack is:

- Plotly for charts
- Streamlit for layout and interaction
- Insight cards above each chart
- Business annotations directly on the figures

---

## Design Principles

Each visualization should be:

- insight-driven: lead with the takeaway, not the chart
- annotated: call out anomalies, breakpoints, drivers, and business events
- business-oriented: translate statistics into impact language
- decision-focused: suggest what action or interpretation matters

Each chart block should follow the same structure:

1. Insight panel
2. Chart
3. Short interpretation or next-step note

---

## Visual System

Use a strict semantic palette:

```python
COLORS = {
    "risk": "#D84C4C",
    "opportunity": "#2E9B5F",
    "neutral": "#2F6BFF",
    "text": "#1F2937",
    "muted": "#6B7280",
    "grid": "#E5E7EB",
    "background": "#FFFFFF",
    "highlight": "#F4B740",
}
```

Meaning:

- red = risk
- green = opportunity
- blue = neutral

Use consistent rules:

- negative delta: red
- positive delta: green
- baseline/reference series: blue
- uncertain or mixed signal: muted neutral tones

---

## Recommended Streamlit Layout

Use a scrollable analytics narrative:

1. Executive KPI strip
2. Trend and anomaly section
3. Root cause section
4. Scenario simulation section
5. Segment performance section
6. Data quality section

Suggested page flow:

```python
st.title("AI Data Investigator")

render_kpi_strip(summary_metrics)

st.markdown("## Performance Monitoring")
render_insight_panel(...)
st.plotly_chart(build_trend_chart(...), use_container_width=True)

st.markdown("## Root Cause Analysis")
left, right = st.columns([1.2, 1])
with left:
    render_insight_panel(...)
    st.plotly_chart(build_correlation_heatmap(...), use_container_width=True)
with right:
    render_insight_panel(...)
    st.plotly_chart(build_feature_importance_chart(...), use_container_width=True)

st.markdown("## Scenario Explorer")
render_insight_panel(...)
st.plotly_chart(build_scenario_comparison_chart(...), use_container_width=True)

st.markdown("## Segment Performance")
render_insight_panel(...)
st.plotly_chart(build_segment_comparison_chart(...), use_container_width=True)

st.markdown("## Data Reliability")
render_insight_panel(...)
st.plotly_chart(build_data_quality_chart(...), use_container_width=True)
```

---

## Shared UI Component: Insight Panel

Display a compact business summary above every chart.

```python
import streamlit as st


def render_insight_panel(message: str, impact: str, confidence: float, tone: str = "neutral") -> None:
    tone_map = {
        "risk": {"bg": "#FDECEC", "border": "#D84C4C", "text": "#7F1D1D"},
        "opportunity": {"bg": "#EAF8F0", "border": "#2E9B5F", "text": "#14532D"},
        "neutral": {"bg": "#EDF4FF", "border": "#2F6BFF", "text": "#1D4ED8"},
    }
    palette = tone_map[tone]
    st.markdown(
        f"""
        <div style="
            padding: 14px 16px;
            border-radius: 16px;
            background: {palette['bg']};
            border-left: 6px solid {palette['border']};
            margin-bottom: 12px;
        ">
            <div style="font-size: 0.85rem; color: {palette['text']}; font-weight: 700;">KEY MESSAGE</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #111827; margin-top: 4px;">{message}</div>
            <div style="display: flex; gap: 18px; margin-top: 8px; color: #374151; font-size: 0.92rem;">
                <span><strong>Impact:</strong> {impact}</span>
                <span><strong>Confidence:</strong> {confidence:.0%}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
```

Example messages:

- "Revenue drop starts in week 34 and accelerated after the price increase."
- "Demand sensitivity is concentrated in price and discount depth."
- "Scenario B recovers margin but increases churn risk in the SME segment."

---

## Shared Plotly Theme

```python
import plotly.graph_objects as go


def apply_figure_theme(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", size=13, color="#1F2937"),
        margin=dict(l=40, r=24, t=70, b=40),
        hoverlabel=dict(bgcolor="white", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E5E7EB", zeroline=False)
    return fig
```

---

## 1. Trend Chart With Anomaly Detection

Purpose:

- show trend over time
- detect spikes, drops, and structural breaks
- annotate the moment the business impact starts

```python
import pandas as pd
import plotly.graph_objects as go


def build_trend_chart(df: pd.DataFrame) -> go.Figure:
    working = df.copy()
    working["rolling_mean"] = working["value"].rolling(7, min_periods=3).mean()
    working["rolling_std"] = working["value"].rolling(7, min_periods=3).std().fillna(0)
    working["upper_band"] = working["rolling_mean"] + 2 * working["rolling_std"]
    working["lower_band"] = working["rolling_mean"] - 2 * working["rolling_std"]
    working["is_anomaly"] = (
        (working["value"] > working["upper_band"]) |
        (working["value"] < working["lower_band"])
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=working["date"],
        y=working["value"],
        mode="lines+markers",
        name="Observed",
        line=dict(color="#2F6BFF", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=working["date"],
        y=working["rolling_mean"],
        mode="lines",
        name="Trend",
        line=dict(color="#7C8DB5", width=2, dash="dash"),
    ))
    anomalies = working[working["is_anomaly"]]
    fig.add_trace(go.Scatter(
        x=anomalies["date"],
        y=anomalies["value"],
        mode="markers",
        name="Anomalies",
        marker=dict(color="#D84C4C", size=11, line=dict(color="white", width=1)),
    ))

    if not anomalies.empty:
        first_anomaly = anomalies.iloc[0]
        fig.add_annotation(
            x=first_anomaly["date"],
            y=first_anomaly["value"],
            text="Anomaly detected",
            showarrow=True,
            arrowcolor="#D84C4C",
            bgcolor="#FDECEC",
            bordercolor="#D84C4C",
        )

    if len(working) > 10:
        drop_index = working["value"].diff().idxmin()
        drop_row = working.loc[drop_index]
        fig.add_vline(x=drop_row["date"], line_dash="dot", line_color="#D84C4C")
        fig.add_annotation(
            x=drop_row["date"],
            y=drop_row["value"],
            text="Revenue drop starts here",
            showarrow=True,
            arrowcolor="#D84C4C",
            bgcolor="#FDECEC",
        )

    fig = apply_figure_theme(fig, "Trend and anomaly detection")
    fig.update_yaxes(title="Metric value")
    return fig
```

Business annotation examples:

- "Revenue drop starts here"
- "Promotion lift begins"
- "Anomaly detected after supply disruption"

---

## 2. Correlation Heatmap

Purpose:

- surface relationships between business variables
- support root cause analysis
- highlight suspicious or high-leverage dependencies

```python
import plotly.express as px


def build_correlation_heatmap(df: pd.DataFrame, columns: list[str]):
    corr = df[columns].corr(numeric_only=True)
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale=[
            [0.0, "#D84C4C"],
            [0.5, "#F8FAFC"],
            [1.0, "#2E9B5F"],
        ],
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig = apply_figure_theme(fig, "Correlation heatmap")
    fig.add_annotation(
        x="demand",
        y="price",
        text="Price increase -> demand drop",
        showarrow=True,
        arrowhead=2,
        ax=80,
        ay=-40,
        bgcolor="#FDECEC",
        bordercolor="#D84C4C",
    )
    return fig
```

Interpretation guidance:

- strong negative correlation: probable tradeoff
- strong positive correlation: reinforcing movement
- near zero: weak linear relationship, not necessarily no causality

---

## 3. Feature Importance Chart

Purpose:

- show top drivers from a model or root cause engine
- rank contributions clearly
- separate beneficial from harmful drivers

```python
import plotly.graph_objects as go


def build_feature_importance_chart(features_df: pd.DataFrame) -> go.Figure:
    working = features_df.sort_values("importance", ascending=True).copy()
    working["color"] = working["direction"].map({
        "negative": "#D84C4C",
        "positive": "#2E9B5F",
        "neutral": "#2F6BFF",
    })

    fig = go.Figure(go.Bar(
        x=working["importance"],
        y=working["feature"],
        orientation="h",
        marker=dict(color=working["color"]),
        text=working["importance"].round(2),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Contribution: %{x:.2f}<extra></extra>",
    ))

    top_driver = working.iloc[-1]
    fig.add_annotation(
        x=top_driver["importance"],
        y=top_driver["feature"],
        text=f"Top driver: {top_driver['feature']}",
        showarrow=True,
        arrowcolor="#2F6BFF",
        bgcolor="#EDF4FF",
        bordercolor="#2F6BFF",
    )

    fig = apply_figure_theme(fig, "Top drivers and ranked contribution")
    fig.update_xaxes(title="Contribution score")
    fig.update_yaxes(title="")
    return fig
```

Recommended data schema:

- `feature`
- `importance`
- `direction`
- `business_label`
- `explanation`

---

## 4. Scenario Comparison Chart

Purpose:

- compare baseline vs proposed scenario
- show delta percentage
- make tradeoffs visible immediately

```python
def build_scenario_comparison_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["metric"],
        y=df["baseline"],
        name="Baseline",
        marker_color="#2F6BFF",
    ))
    fig.add_trace(go.Bar(
        x=df["metric"],
        y=df["scenario"],
        name="Scenario",
        marker_color=[
            "#2E9B5F" if delta >= 0 else "#D84C4C"
            for delta in df["delta_pct"]
        ],
    ))

    for _, row in df.iterrows():
        label = f"{row['delta_pct']:+.1f}%"
        fig.add_annotation(
            x=row["metric"],
            y=max(row["baseline"], row["scenario"]),
            text=label,
            showarrow=False,
            yshift=16,
            bgcolor="#F8FAFC",
            bordercolor="#CBD5E1",
        )

    fig = apply_figure_theme(fig, "Baseline vs scenario comparison")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Value")
    return fig
```

Recommended metrics:

- revenue
- margin
- churn
- conversion
- retention
- service cost

Insight examples:

- "Scenario B improves margin by 8.4% but reduces conversion by 3.1%."
- "Scenario C is safer for revenue preservation."

---

## 5. Segment Comparison Chart

Purpose:

- compare performance across customers, regions, products, or channels
- detect where risk or opportunity is concentrated

```python
def build_segment_comparison_chart(df: pd.DataFrame) -> go.Figure:
    working = df.sort_values("value", ascending=False).copy()
    working["color"] = working["performance_flag"].map({
        "risk": "#D84C4C",
        "opportunity": "#2E9B5F",
        "neutral": "#2F6BFF",
    })

    fig = go.Figure(go.Bar(
        x=working["segment"],
        y=working["value"],
        marker_color=working["color"],
        text=working["value"].round(1),
        textposition="outside",
    ))

    weakest = working.iloc[-1]
    fig.add_annotation(
        x=weakest["segment"],
        y=weakest["value"],
        text="Underperforming segment",
        showarrow=True,
        arrowcolor="#D84C4C",
        bgcolor="#FDECEC",
    )

    fig = apply_figure_theme(fig, "Segment comparison")
    fig.update_yaxes(title="Performance metric")
    return fig
```

Use cases:

- region performance
- product category comparison
- enterprise vs SME
- paid vs organic

---

## 6. Data Quality Chart

Purpose:

- make reliability visible before users trust the analysis
- separate insight quality from data quality

```python
def build_data_quality_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["dimension"],
        y=df["score"],
        marker_color=[
            "#2E9B5F" if score >= 95 else "#2F6BFF" if score >= 85 else "#D84C4C"
            for score in df["score"]
        ],
        text=df["score"].astype(str) + "%",
        textposition="outside",
    ))

    issue_row = df.loc[df["score"].idxmin()]
    fig.add_annotation(
        x=issue_row["dimension"],
        y=issue_row["score"],
        text="Primary data quality risk",
        showarrow=True,
        arrowcolor="#D84C4C",
        bgcolor="#FDECEC",
        bordercolor="#D84C4C",
    )

    fig = apply_figure_theme(fig, "Data quality status")
    fig.update_yaxes(title="Completeness / reliability score", range=[0, 105])
    return fig
```

Recommended dimensions:

- completeness
- freshness
- validity
- consistency
- uniqueness

---

## Root Cause Visual

The root cause section should combine:

- correlation heatmap
- feature importance chart
- ranked driver table

Recommended supporting table:

```python
st.dataframe(
    drivers_df[["feature", "importance", "direction", "explanation"]]
    .sort_values("importance", ascending=False),
    use_container_width=True,
)
```

Message examples:

- "Top drivers explain 72% of the variance."
- "Price and discount depth are the two strongest demand levers."
- "Channel mix shift is a secondary but rising contributor."

---

## Example Annotated Chart Inputs

Example trend dataset:

```python
trend_df = pd.DataFrame({
    "date": pd.date_range("2026-01-01", periods=30, freq="D"),
    "value": [102, 103, 101, 104, 105, 106, 104, 107, 108, 106,
              105, 104, 103, 100, 96, 92, 90, 91, 89, 88,
              87, 85, 83, 82, 84, 83, 81, 80, 79, 78]
})
```

Example feature importance dataset:

```python
features_df = pd.DataFrame({
    "feature": ["Price", "Discount depth", "Stock availability", "Channel mix", "Delivery delay"],
    "importance": [0.41, 0.22, 0.16, 0.12, 0.09],
    "direction": ["negative", "positive", "positive", "neutral", "negative"],
})
```

Example scenario dataset:

```python
scenario_df = pd.DataFrame({
    "metric": ["Revenue", "Margin", "Conversion", "Churn"],
    "baseline": [100, 32, 4.8, 6.2],
    "scenario": [104, 35, 4.5, 6.8],
})
scenario_df["delta_pct"] = (
    (scenario_df["scenario"] - scenario_df["baseline"]) / scenario_df["baseline"] * 100
)
```

---

## Streamlit Integration Pattern

This pattern fits directly into the existing analytics page in [ui/streamlit_app.py](/Users/guillaumeverbiguie/Desktop/ai automation agent/ui/streamlit_app.py).

```python
elif page == "Analytics":
    st.subheader("Analytics")

    summary_metrics = {
        "revenue_at_risk": "$184K",
        "critical_anomalies": 3,
        "data_quality_score": "88%",
    }
    render_kpi_strip(summary_metrics)

    render_insight_panel(
        message="Revenue decline begins mid-month and is paired with two anomaly points.",
        impact="High",
        confidence=0.91,
        tone="risk",
    )
    st.plotly_chart(build_trend_chart(trend_df), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        render_insight_panel(
            message="Price is the strongest inverse driver of demand.",
            impact="High",
            confidence=0.87,
            tone="risk",
        )
        st.plotly_chart(
            build_correlation_heatmap(model_df, ["price", "demand", "discount", "stockout_rate"]),
            use_container_width=True,
        )
    with col2:
        render_insight_panel(
            message="Three drivers explain most of the outcome variance.",
            impact="Medium",
            confidence=0.84,
            tone="neutral",
        )
        st.plotly_chart(build_feature_importance_chart(features_df), use_container_width=True)

    render_insight_panel(
        message="Scenario B improves margin but slightly hurts conversion.",
        impact="Medium",
        confidence=0.79,
        tone="opportunity",
    )
    st.plotly_chart(build_scenario_comparison_chart(scenario_df), use_container_width=True)

    render_insight_panel(
        message="SME and South region are the weakest segments and should be prioritized.",
        impact="High",
        confidence=0.82,
        tone="risk",
    )
    st.plotly_chart(build_segment_comparison_chart(segment_df), use_container_width=True)

    render_insight_panel(
        message="Freshness and completeness are acceptable, but validity remains a decision risk.",
        impact="Medium",
        confidence=0.93,
        tone="neutral",
    )
    st.plotly_chart(build_data_quality_chart(data_quality_df), use_container_width=True)
```

Optional KPI strip:

```python
def render_kpi_strip(metrics: dict) -> None:
    cols = st.columns(len(metrics))
    for idx, (label, value) in enumerate(metrics.items()):
        cols[idx].metric(label.replace("_", " ").title(), value)
```

---

## Backend Data Recommendations

To support these visuals cleanly, expose analytics-ready payloads rather than only aggregate counters.

Recommended API payload groups:

- `timeseries_metrics`
- `correlation_matrix`
- `feature_importance`
- `scenario_comparison`
- `segment_metrics`
- `data_quality_metrics`

Example response shape:

```python
{
    "summary": {
        "revenue_at_risk": 184000,
        "critical_anomalies": 3,
        "data_quality_score": 88
    },
    "timeseries_metrics": [...],
    "correlation_matrix": [...],
    "feature_importance": [...],
    "scenario_comparison": [...],
    "segment_metrics": [...],
    "data_quality_metrics": [...]
}
```

---

## Implementation Priorities

Phase 1:

- add Plotly dependency
- build shared theme
- build insight panel
- implement trend, feature importance, scenario comparison

Phase 2:

- add correlation heatmap
- add segment comparison
- add data quality chart
- add richer analytics endpoint

Phase 3:

- add filters by segment, region, timeframe
- add drill-down interactions
- add export to PNG or PDF

---

## Final Recommendation

The strongest premium experience comes from pairing every figure with:

- one explicit key message
- one impact level
- one confidence score
- one or two business annotations

That structure turns charts from descriptive visuals into decision tools.
