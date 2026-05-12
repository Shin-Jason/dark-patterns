#!/usr/bin/env python3
"""
Social Proof Dark Patterns — Streamlit Dashboard

A local "one-stop shop" to explore research results:
  • Overview metrics & summary charts
  • Deep-dive per-image explorer with model responses
  • Raw CSV data table

Run:
    streamlit run app.py
"""

import os
import re
import pathlib
from collections import Counter

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# CONFIGURATION
# =============================================================================

CSV_PATH = "social_proof_results_v5.csv"
HEATMAP_PATH = "heatmap_scores_v5.png"
DELTA_PATH = "delta_skepticism_v5.png"
SCREENSHOTS_DIR = "v5-ss"

# Experiment version configs
EXPERIMENT_VERSIONS = {
    "v6 (Current)": {
        "csv": "social_proof_results_v5.csv",
        "heatmap": "heatmap_scores_v5.png",
        "delta": "delta_skepticism_v5.png",
        "screenshots_dir": "v5-ss",
        "tag_count_map": "v6",
    },
    "v7 (Figma)": {
        "csv": "social_proof_results_v7.csv",
        "heatmap": "heatmap_scores_v7.png",
        "delta": "delta_skepticism_v7.png",
        "screenshots_dir": "v7-figma",
        "tag_count_map": "v7",
    },
    "v8 (Adapter)": {
        "csv": "social_proof_results_v8.csv",
        "heatmap": "heatmap_scores_v8.png",
        "delta": "delta_skepticism_v8.png",
        "screenshots_dir": "v8-adapter",
        "tag_count_map": "v8",
    },
    "v9 (Control)": {
        "csv": "social_proof_results_v9.csv",
        "heatmap": "heatmap_scores_v9.png",
        "delta": "delta_skepticism_v9.png",
        "screenshots_dir": "v9-control",
        "tag_count_map": "v9",
    },
}

CONDITION_LABELS = {
    "AVERAGE_CONSUMER": "🟢 Average Consumer",
    "CONSUMER_ADVOCATE": "🔴 Consumer Advocate",
}

MODEL_SHORT_NAMES = {
    "google/gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview",
    "google/gemini-3-pro-preview": "Gemini 3 Pro Preview",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "anthropic/claude-opus-4.6": "Claude Opus 4.6",
    "anthropic/claude-haiku-4.5": "Claude Haiku 4.5",
    "openai/gpt-5.2": "GPT-5.2",
    "openai/gpt-4o-mini": "GPT-4o Mini",
}

PROVIDER_COLORS = {
    "Google": "#4285F4",
    "Anthropic": "#D97757",
    "OpenAI": "#10A37F",
}

# Tag-count mapping for dose-response analysis
TAG_COUNT_MAP = {
    "control.png": 0,
    "expert-tag.png": 1,
    "review-tags.png": 1,
    "voted-best-tag.png": 1,
    "voted-best-expert-tags.png": 2,
    "voted-best-review-tags.png": 2,
    "three-tags.png": 3,
}

TAG_COUNT_MAP_V7 = {
    "control.png": 0,
    "expert.png": 1,
    "review.png": 1,
    "voted.png": 1,
    "voted_expert.png": 2,
    "review_expert.png": 2,
    "review_voted.png": 2,
    "review_expert_voted.png": 3,
}

TAG_COUNT_MAP_V8 = {
    "control.png": 0,
    "expert_tag.png": 1,
    "review_tag.png": 1,
    "voted_best.png": 1,
    "expert_voted_best.png": 2,
    "review_expert_tag.png": 2,
    "review_voted_best.png": 2,
    "all_tags.png": 3,
}

# v9 control images — standalone product images with 0 social proof tags
TAG_COUNT_MAP_V9 = {
    "control-A.png": 0,
    "control-B.png": 0,
}

# Model tier groupings
MODEL_TIERS = {
    "Gemini 3.1 Pro Preview": "High Reasoning",
    "Gemini 3 Pro Preview": "High Reasoning",
    "Claude Opus 4.6": "High Reasoning",
    "GPT-5.2": "High Reasoning",
    "Gemini 2.5 Flash": "Efficient",
    "Claude Haiku 4.5": "Efficient",
    "GPT-4o Mini": "Efficient",
}

# Skepticism keywords to scan in CoT reasoning
SKEPTICISM_KEYWORDS = [
    "manipulat",
    "dark pattern",
    "fomo",
    "pressure",
    "fake",
    "incentivized",
    "suspicious",
    "misleading",
    "deceptive",
    "red flag",
    "manufactured",
    "artificial",
]

# Confound categories — keywords that indicate the model was distracted
# by factors unrelated to social proof
CONFOUND_CATEGORIES = {
    "Price Missing": ["price", "cost", "value for money", "pricing"],
    "Specs/Safety Missing": [
        "specifications", "voltage", "safety", "UL", "CE",
        "amperage", "compatibility",
    ],
    "Fake/Manipulated Flag": [
        "fake", "manipulated", "unusual", "suspicious", "marketing tactic",
    ],
    "Identical Image Flag": [
        "visually identical", "identical", "same image", "distinguish",
    ],
}

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Social Proof Dark Patterns Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown(
    """
<style>
/* ── Global ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Metric cards ────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e1e2e 0%, #2a2a40 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}
div[data-testid="stMetric"] label {
    color: #a0a0b8 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-weight: 700;
    font-size: 2rem !important;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}
section[data-testid="stSidebar"] h1 {
    font-size: 1.3rem !important;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── Tabs ─────────────────────────────────────────────────── */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px;
}

/* ── Expander ─────────────────────────────────────────────── */
details[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    margin-bottom: 8px;
}

/* ── Score badges ─────────────────────────────────────────── */
.score-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
    color: #fff;
}
.score-1 { background: #dc2626; }
.score-2 { background: #ea580c; }
.score-3 { background: #d97706; }
.score-4 { background: #16a34a; }
.score-5 { background: #059669; }
.score-na { background: #6b7280; }
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# DATA LOADING
# =============================================================================


@st.cache_data
def load_data(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    df["Short Model"] = df["Model"].map(MODEL_SHORT_NAMES).fillna(df["Model"])
    df["Condition Label"] = df["Condition"].map(CONDITION_LABELS).fillna(df["Condition"])
    df["Provider"] = df["Model"].apply(
        lambda m: m.split("/")[0].title() if "/" in m else "Other"
    )
    return df


def score_badge(score) -> str:
    if pd.isna(score) or score is None:
        return '<span class="score-badge score-na">N/A</span>'
    s = int(score)
    return f'<span class="score-badge score-{s}">{s}/5</span>'


# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.markdown("# 🔍 Dark Patterns Lab")
st.sidebar.markdown("---")

# ── Experiment version selector ──────────────────────────────
version_options = list(EXPERIMENT_VERSIONS.keys())
selected_version = st.sidebar.selectbox(
    "📁 Select Experiment Version",
    options=version_options,
    index=0,
)

# Resolve dynamic paths from selected version
version_config = EXPERIMENT_VERSIONS[selected_version]
active_csv = version_config["csv"]
active_heatmap = version_config["heatmap"]
active_delta = version_config["delta"]
active_screenshots_dir = version_config["screenshots_dir"]
if version_config["tag_count_map"] == "v7":
    active_tag_map = TAG_COUNT_MAP_V7
elif version_config["tag_count_map"] == "v8":
    active_tag_map = TAG_COUNT_MAP_V8
elif version_config["tag_count_map"] == "v9":
    active_tag_map = TAG_COUNT_MAP_V9
else:
    active_tag_map = TAG_COUNT_MAP

st.sidebar.markdown("---")

df = load_data(active_csv)

if df.empty:
    st.error(
        f"**CSV not found:** `{active_csv}`\n\n"
        "Run `python main.py` first to generate results, then reload this dashboard."
    )
    st.stop()

# Filters
all_models = sorted(df["Short Model"].unique())
selected_models = st.sidebar.multiselect(
    "🤖 Models",
    options=all_models,
    default=all_models,
)

all_conditions = sorted(df["Condition"].unique())
selected_conditions = st.sidebar.multiselect(
    "📋 Conditions",
    options=all_conditions,
    default=all_conditions,
    format_func=lambda c: CONDITION_LABELS.get(c, c),
)

all_images = sorted(df["Image"].unique())
selected_image = st.sidebar.selectbox(
    "📸 Focus Image (Deep Dive)",
    options=all_images,
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Built with Streamlit · Data from OpenRouter API"
)

# Apply filters
mask = df["Short Model"].isin(selected_models) & df["Condition"].isin(selected_conditions)
filtered = df[mask]

# =============================================================================
# TABS
# =============================================================================

tab_overview, tab_deepdive, tab_research, tab_confound, tab_raw = st.tabs(
    ["📊 Overview", "🔬 Deep Dive", "📈 Research Insights", "🧪 Confound Analysis", "📋 Raw Data"]
)

# ─── TAB 1: OVERVIEW ────────────────────────────────────────────────────────

with tab_overview:
    st.markdown("## 📊 Overview & Summary")
    st.markdown("High-level metrics and pre-generated visualizations from the study.")

    # ── Metric cards ──────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Images Analyzed", f"{df['Image'].nunique()}")
    with col2:
        st.metric("Models Tested", f"{df['Model'].nunique()}")
    with col3:
        avg_naive = (
            filtered.loc[filtered["Condition"] == "AVERAGE_CONSUMER", "Raw Score"]
            .dropna()
            .mean()
        )
        st.metric(
            "Avg Score (Consumer)",
            f"{avg_naive:.2f}" if pd.notna(avg_naive) else "—",
        )
    with col4:
        avg_crit = (
            filtered.loc[filtered["Condition"] == "CONSUMER_ADVOCATE", "Raw Score"]
            .dropna()
            .mean()
        )
        st.metric(
            "Avg Score (Advocate)",
            f"{avg_crit:.2f}" if pd.notna(avg_crit) else "—",
        )

    st.markdown("---")

    # ── Per-condition breakdown ──────────────────────────────────
    st.markdown("### Score Distribution by Condition")
    cond_summary = (
        filtered.groupby(["Condition Label", "Short Model"])["Raw Score"]
        .mean()
        .reset_index()
        .rename(columns={"Raw Score": "Mean Score"})
    )
    if not cond_summary.empty:
        col_l, col_r = st.columns(2)
        for i, cond in enumerate(selected_conditions):
            label = CONDITION_LABELS.get(cond, cond)
            chunk = cond_summary[cond_summary["Condition Label"] == label]
            target = col_l if i % 2 == 0 else col_r
            with target:
                st.markdown(f"**{label}**")
                st.bar_chart(
                    chunk.set_index("Short Model")["Mean Score"],
                    height=280,
                    use_container_width=True,
                )

    st.markdown("---")

    # ── Summary charts ──────────────────────────────────────────
    st.markdown("### Generated Summary Charts")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        if os.path.exists(active_heatmap):
            st.image(active_heatmap, caption="Mean Score Heatmap (Model × Image)", use_container_width=True)
        else:
            st.info(f"`{active_heatmap}` not found — run `main.py` to generate.")
    with chart_col2:
        if os.path.exists(active_delta):
            st.image(active_delta, caption="Skepticism Delta by Model", use_container_width=True)
        else:
            st.info(f"`{active_delta}` not found — run `main.py` to generate.")


# ─── TAB 2: DEEP DIVE ───────────────────────────────────────────────────────

with tab_deepdive:
    st.markdown(f"## 🔬 Deep Dive: `{selected_image}`")

    # Show the source screenshot
    img_path = os.path.join(active_screenshots_dir, selected_image)
    if os.path.exists(img_path):
        st.image(img_path, caption=f"Source Screenshot — {selected_image}", use_container_width=True)
    else:
        st.warning(f"Screenshot not found: `{img_path}`")

    st.markdown("---")

    # Filter to the selected image
    img_df = filtered[filtered["Image"] == selected_image]

    if img_df.empty:
        st.info("No results for this image with the current filters.")
    else:
        # ── Score comparison table ───────────────────────────────
        st.markdown("### Score Comparison")

        pivot = img_df.pivot_table(
            values="Raw Score",
            index="Short Model",
            columns="Condition Label",
            aggfunc="first",
        )

        # Build an HTML table with score badges
        html_rows = []
        for model_name in pivot.index:
            cells = f"<td style='padding:10px 16px;font-weight:600;'>{model_name}</td>"
            for col in pivot.columns:
                val = pivot.loc[model_name, col] if col in pivot.columns else None
                cells += f"<td style='padding:10px 16px;text-align:center;'>{score_badge(val)}</td>"
            html_rows.append(f"<tr>{cells}</tr>")

        header_cells = "<th style='padding:10px 16px;'>Model</th>"
        for col in pivot.columns:
            header_cells += f"<th style='padding:10px 16px;text-align:center;'>{col}</th>"

        st.markdown(
            f"""
            <table style="width:100%; border-collapse:collapse; border:1px solid rgba(255,255,255,0.08); border-radius:12px; overflow:hidden;">
                <thead><tr style="background:rgba(255,255,255,0.04);">{header_cells}</tr></thead>
                <tbody>{"".join(html_rows)}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Per-model detailed responses ──────────────────────────
        st.markdown("### Model Responses")

        models_in_image = img_df["Short Model"].unique()
        for model_short in sorted(models_in_image):
            model_rows = img_df[img_df["Short Model"] == model_short]
            provider = model_rows["Provider"].iloc[0]
            accent = PROVIDER_COLORS.get(provider, "#6b7280")

            st.markdown(
                f"<div style='border-left:4px solid {accent}; padding-left:12px; "
                f"margin-bottom:4px;'>"
                f"<strong style='font-size:1.05rem;'>{model_short}</strong> "
                f"<span style='color:{accent}; font-size:0.85rem;'>({provider})</span></div>",
                unsafe_allow_html=True,
            )

            for _, row in model_rows.iterrows():
                cond_label = row["Condition Label"]
                score_val = row["Raw Score"]
                explanation = row.get("Explanation", "")
                reasoning = row.get("Reasoning", "")

                with st.expander(f"{cond_label}  —  Score: {int(score_val) if pd.notna(score_val) else 'N/A'}/5"):
                    # Explanation
                    st.markdown("**📝 Explanation**")
                    st.markdown(explanation if explanation else "*No explanation provided.*")

                    # Chain of Thought
                    if reasoning and str(reasoning).strip():
                        st.markdown("**🧠 Chain of Thought / Reasoning**")
                        st.code(reasoning, language=None)
                    else:
                        st.caption("_No chain of thought captured for this response._")

            st.markdown("")  # spacer


# ─── TAB 3: RESEARCH INSIGHTS ────────────────────────────────────────────────

with tab_research:
    st.markdown("## 📈 Research Insights")
    st.markdown("Research-grade analyses for evaluating social proof dark pattern susceptibility across models.")

    # ── 1. Dose-Response Analysis ────────────────────────────────
    st.markdown("---")
    st.markdown("### 1 · Dose-Response Analysis (Tag Additivity)")
    st.caption(
        "How does stacking social proof tags (0 → 3) affect the recommendation score? "
        "Separate lines per condition."
    )

    dose_df = filtered.copy()
    dose_df["Tag Count"] = dose_df["Image"].map(active_tag_map)
    dose_valid = dose_df.dropna(subset=["Tag Count", "Raw Score"])

    if dose_valid.empty:
        st.info("No tag-mapped data available for dose-response chart.")
    else:
        dose_agg = (
            dose_valid.groupby(["Tag Count", "Condition Label"])["Raw Score"]
            .agg(["mean", "sem", "count"])
            .reset_index()
        )
        dose_agg.columns = ["Tag Count", "Condition", "Mean Score", "SEM", "N"]

        fig_dose = go.Figure()
        colors = {"🟢 Average Consumer": "#22c55e", "🔴 Consumer Advocate": "#ef4444"}
        for cond in dose_agg["Condition"].unique():
            subset = dose_agg[dose_agg["Condition"] == cond].sort_values("Tag Count")
            fig_dose.add_trace(go.Scatter(
                x=subset["Tag Count"],
                y=subset["Mean Score"],
                mode="lines+markers",
                name=cond,
                line=dict(width=3, color=colors.get(cond, "#888")),
                marker=dict(size=10),
                error_y=dict(type="data", array=subset["SEM"].tolist(), visible=True),
                hovertemplate="Tags: %{x}<br>Mean: %{y:.2f} ± %{error_y.array:.2f}<br>N=%{customdata}",
                customdata=subset["N"].tolist(),
            ))

        fig_dose.update_layout(
            xaxis=dict(title="Number of Social Proof Tags", dtick=1, range=[-0.3, 3.3]),
            yaxis=dict(title="Mean Recommendation Score", range=[0.5, 5.5], dtick=1),
            template="plotly_dark",
            height=420,
            margin=dict(l=60, r=30, t=40, b=60),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_dose, use_container_width=True)

    # ── 2. Model Tier Comparison ─────────────────────────────────
    st.markdown("---")
    st.markdown("### 2 · Model Tier Comparison")
    st.caption(
        "**High Reasoning** (Gemini 3 Pro, Claude Opus, GPT-5.2) vs. "
        "**Efficient** (Flash, Haiku, 4o-mini). Are \"smarter\" models more skeptical?"
    )

    tier_df = filtered.copy()
    tier_df["Tier"] = tier_df["Short Model"].map(MODEL_TIERS)
    tier_valid = tier_df.dropna(subset=["Tier", "Raw Score"])

    if tier_valid.empty:
        st.info("No tier data available.")
    else:
        tier_agg = (
            tier_valid.groupby(["Tier", "Condition Label"])["Raw Score"]
            .agg(["mean", "sem", "count"])
            .reset_index()
        )
        tier_agg.columns = ["Tier", "Condition", "Mean Score", "SEM", "N"]

        fig_tier = px.bar(
            tier_agg,
            x="Tier",
            y="Mean Score",
            color="Condition",
            barmode="group",
            error_y="SEM",
            color_discrete_map={"🟢 Average Consumer": "#22c55e", "🔴 Consumer Advocate": "#ef4444"},
            text=tier_agg["Mean Score"].round(2),
        )
        fig_tier.update_layout(
            yaxis=dict(title="Mean Recommendation Score", range=[0, 5.5], dtick=1),
            xaxis_title="",
            template="plotly_dark",
            height=400,
            margin=dict(l=60, r=30, t=40, b=60),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        )
        fig_tier.update_traces(textposition="outside")
        st.plotly_chart(fig_tier, use_container_width=True)

    # ── 3. Score Distribution (Box Plot) ─────────────────────────
    st.markdown("---")
    st.markdown("### 3 · Score Distribution by Model")
    st.caption(
        "Box plots showing the full distribution, median, quartiles, and outliers "
        "for each model's scores across all images and conditions."
    )

    box_valid = filtered.dropna(subset=["Raw Score"])
    if box_valid.empty:
        st.info("No score data available for box plot.")
    else:
        fig_box = px.box(
            box_valid,
            x="Short Model",
            y="Raw Score",
            color="Condition Label",
            points="all",
            color_discrete_map={"🟢 Average Consumer": "#22c55e", "🔴 Consumer Advocate": "#ef4444"},
        )
        fig_box.update_layout(
            yaxis=dict(title="Recommendation Score", dtick=1, range=[0.5, 5.5]),
            xaxis_title="",
            template="plotly_dark",
            height=450,
            margin=dict(l=60, r=30, t=40, b=100),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        )
        fig_box.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_box, use_container_width=True)

    # ── 4. CoT Keyword Flagging ──────────────────────────────────
    st.markdown("---")
    st.markdown("### 4 · Chain-of-Thought Skepticism Keywords")
    st.caption(
        "What % of each model's internal reasoning mentions skepticism-related concepts? "
        "Higher rates may indicate the model is \"noticing\" dark patterns even if its score stays high."
    )

    cot_df = filtered.copy()
    cot_df["has_reasoning"] = cot_df["Reasoning"].fillna("").str.strip().astype(bool)
    cot_with = cot_df[cot_df["has_reasoning"]].copy()

    if cot_with.empty:
        st.info("No chain-of-thought data available for keyword analysis.")
    else:
        keyword_pattern = "|".join(re.escape(kw) for kw in SKEPTICISM_KEYWORDS)

        for kw in SKEPTICISM_KEYWORDS:
            col_name = f"kw_{kw}"
            cot_with[col_name] = cot_with["Reasoning"].str.contains(
                re.escape(kw), case=False, na=False
            )

        kw_cols = [f"kw_{kw}" for kw in SKEPTICISM_KEYWORDS]
        kw_by_model = cot_with.groupby("Short Model")[kw_cols].mean() * 100
        kw_by_model.columns = SKEPTICISM_KEYWORDS

        # Melt for grouped bar
        kw_melted = kw_by_model.reset_index().melt(
            id_vars="Short Model", var_name="Keyword", value_name="% Flagged"
        )
        # Filter to keywords that actually appear
        active_kw = kw_melted.groupby("Keyword")["% Flagged"].sum()
        active_kw = active_kw[active_kw > 0].index.tolist()
        kw_melted = kw_melted[kw_melted["Keyword"].isin(active_kw)]

        if kw_melted.empty:
            st.info("None of the tracked keywords were found in any model's reasoning.")
        else:
            fig_kw = px.bar(
                kw_melted,
                x="Keyword",
                y="% Flagged",
                color="Short Model",
                barmode="group",
                text=kw_melted["% Flagged"].round(0).astype(int),
            )
            fig_kw.update_layout(
                yaxis=dict(title="% of Responses Flagging Keyword", range=[0, 105]),
                xaxis_title="",
                template="plotly_dark",
                height=450,
                margin=dict(l=60, r=30, t=40, b=80),
                legend=dict(title="Model"),
            )
            fig_kw.update_traces(textposition="outside")
            fig_kw.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_kw, use_container_width=True)

        # Summary table
        with st.expander("📋 Full Keyword × Model Heatmap (%)"):
            display_kw = kw_by_model[active_kw] if active_kw else kw_by_model
            st.dataframe(
                display_kw.style.format("{:.0f}%").background_gradient(cmap="YlOrRd", axis=None),
                use_container_width=True,
            )


# ─── TAB 4: CONFOUND ANALYSIS ────────────────────────────────────────────────

with tab_confound:
    st.markdown("## 🧪 Confound Analysis")
    st.markdown(
        "Identify when models scored lower due to **confounding factors** "
        "(missing prices, specs, flagging fakes, identical images) rather than "
        "the social proof manipulation itself."
    )

    # ── Build confound flags ─────────────────────────────────────
    conf_df = filtered.copy()
    # Combine Reasoning + Explanation into one searchable text column
    conf_df["_combined"] = (
        conf_df["Reasoning"].fillna("") + " " + conf_df["Explanation"].fillna("")
    )

    for cat, keywords in CONFOUND_CATEGORIES.items():
        pattern = "|".join(re.escape(kw) for kw in keywords)
        conf_df[cat] = conf_df["_combined"].str.contains(
            pattern, case=False, na=False
        )

    confound_cols = list(CONFOUND_CATEGORIES.keys())

    # ── 1. Confound Keyword Matrix (Heatmap) ────────────────────
    st.markdown("---")
    st.markdown("### 1 · Confound Keyword Matrix")
    st.caption(
        "Each cell shows the **percentage of responses** where a model mentioned "
        "keywords from that confound category (across all images and conditions)."
    )

    matrix = conf_df.groupby("Short Model")[confound_cols].mean() * 100

    if matrix.empty or matrix.sum().sum() == 0:
        st.info("No confound keywords were detected in any model responses.")
    else:
        # Plotly heatmap
        fig_conf = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns.tolist(),
            y=matrix.index.tolist(),
            colorscale=[
                [0, "#1a1a2e"],
                [0.25, "#2d1b69"],
                [0.5, "#e74c3c"],
                [0.75, "#f39c12"],
                [1, "#f1c40f"],
            ],
            text=matrix.values.round(0).astype(int),
            texttemplate="%{text}%",
            textfont=dict(size=14, color="white"),
            hovertemplate="Model: %{y}<br>Confound: %{x}<br>Flagged: %{z:.1f}%<extra></extra>",
            colorbar=dict(title="% Flagged", ticksuffix="%"),
            zmin=0,
            zmax=max(100, matrix.values.max()),
        ))
        fig_conf.update_layout(
            template="plotly_dark",
            height=max(350, len(matrix) * 55 + 100),
            margin=dict(l=150, r=40, t=40, b=80),
            xaxis=dict(title="Confound Category", side="bottom"),
            yaxis=dict(title="", autorange="reversed"),
        )
        st.plotly_chart(fig_conf, use_container_width=True)

        # Summary table in expander
        with st.expander("📋 Full Confound Matrix (% values)"):
            st.dataframe(
                matrix.style.format("{:.0f}%").background_gradient(
                    cmap="YlOrRd", axis=None
                ),
                use_container_width=True,
            )

    # ── 2. Filtered Confound View ────────────────────────────────
    st.markdown("---")
    st.markdown("### 2 · Filtered Confound View")
    st.caption(
        "Select one or more confound categories to filter the data and read the "
        "exact quotes where models got distracted."
    )

    selected_confounds = st.multiselect(
        "Filter by Confound Category",
        options=confound_cols,
        default=[],
        help="Show only rows where the model mentioned keywords from these categories.",
    )

    if not selected_confounds:
        st.info("👆 Select one or more confound categories above to filter the data.")
    else:
        # Row matches if ANY selected confound is True
        confound_mask = conf_df[selected_confounds].any(axis=1)
        confound_filtered = conf_df[confound_mask]

        st.markdown(
            f"Showing **{len(confound_filtered)}** rows matching: "
            f"**{', '.join(selected_confounds)}**"
        )

        if confound_filtered.empty:
            st.warning("No rows matched the selected confound categories.")
        else:
            # Show which confounds each row triggered
            confound_filtered = confound_filtered.copy()
            confound_filtered["Confounds Triggered"] = confound_filtered[confound_cols].apply(
                lambda row: ", ".join(
                    cat for cat, val in row.items() if val
                ),
                axis=1,
            )

            display_conf_cols = [
                "Image", "Short Model", "Condition Label", "Raw Score",
                "Confounds Triggered", "Explanation", "Reasoning",
            ]
            available_conf = [c for c in display_conf_cols if c in confound_filtered.columns]

            st.dataframe(
                confound_filtered[available_conf].reset_index(drop=True),
                use_container_width=True,
                height=500,
                column_config={
                    "Raw Score": st.column_config.NumberColumn("Score", format="%d"),
                    "Short Model": "Model",
                    "Condition Label": "Condition",
                    "Confounds Triggered": st.column_config.TextColumn(
                        "Confounds", width="medium"
                    ),
                },
            )

            # Download button
            csv_conf = confound_filtered[available_conf].to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️  Download confound-filtered CSV",
                data=csv_conf,
                file_name="confound_filtered_results.csv",
                mime="text/csv",
            )

    # ── 3. Discovery Mode ────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 3 · 🔬 Discovery Mode")
    st.caption(
        "Automatically surfaces the most common phrases from model reasoning (CoT) "
        "to help you identify **new confounds** you haven't defined yet. "
        "Phrases from existing confound categories are dimmed for contrast."
    )

    # Gather reasoning text
    disc_df = filtered.copy()
    disc_df["_reasoning"] = disc_df["Reasoning"].fillna("").str.strip()
    disc_with_cot = disc_df[disc_df["_reasoning"].astype(bool)]

    if disc_with_cot.empty:
        st.info("No chain-of-thought reasoning available for discovery analysis.")
    else:
        # ── Stopwords to exclude from n-grams ──
        STOPWORDS = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "it", "its", "this", "that", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may", "might",
            "can", "shall", "not", "no", "if", "as", "so", "than", "then",
            "also", "just", "more", "most", "very", "too", "each", "both",
            "all", "any", "such", "only", "own", "same", "other", "which",
            "who", "whom", "what", "when", "where", "how", "why", "there",
            "here", "about", "into", "through", "during", "before", "after",
            "above", "below", "between", "out", "up", "down", "over", "under",
            "again", "further", "once", "i", "me", "my", "we", "our", "you",
            "your", "he", "she", "they", "them", "their", "his", "her",
            "while", "because", "since", "however", "although", "though",
            "yet", "still", "even", "whether", "either", "neither",
            "some", "many", "much", "few", "several", "these", "those",
            # domain-generic words to reduce noise
            "product", "products", "based", "given", "one", "two", "seem",
            "like", "well", "make", "made", "see", "look", "looking",
            "doesn", "don", "isn", "aren", "wasn", "weren", "won", "wouldn",
            "couldn", "shouldn", "let", "get", "got",
        }

        # Controls for discovery
        disc_col1, disc_col2, disc_col3 = st.columns(3)
        with disc_col1:
            ngram_size = st.selectbox("N-gram size", options=[2, 3, 4], index=1, help="Length of phrase fragments to extract")
        with disc_col2:
            top_n = st.slider("Top phrases to show", min_value=10, max_value=50, value=25)
        with disc_col3:
            disc_scope = st.radio("Scope", ["All Models", "Per Model"], horizontal=True)

        def extract_ngrams(text: str, n: int) -> list[str]:
            """Extract n-grams from text, filtering stopwords."""
            words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
            words = [w for w in words if w not in STOPWORDS and len(w) > 2]
            return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]

        # Flatten existing confound keywords for dimming
        existing_kw_set = set()
        for kws in CONFOUND_CATEGORIES.values():
            for kw in kws:
                existing_kw_set.add(kw.lower())

        if disc_scope == "All Models":
            # Global n-gram frequency
            all_ngrams = []
            for text in disc_with_cot["_reasoning"]:
                all_ngrams.extend(extract_ngrams(text, ngram_size))

            counts = Counter(all_ngrams).most_common(top_n)

            if not counts:
                st.info("No phrases extracted — reasoning text may be too short.")
            else:
                phrases, freqs = zip(*counts)

                # Mark phrases that overlap with existing confound keywords
                colors = []
                for p in phrases:
                    is_existing = any(kw in p for kw in existing_kw_set)
                    colors.append("#6b7280" if is_existing else "#8b5cf6")

                fig_disc = go.Figure(go.Bar(
                    x=list(reversed(freqs)),
                    y=list(reversed(phrases)),
                    orientation="h",
                    marker_color=list(reversed(colors)),
                    text=list(reversed(freqs)),
                    textposition="outside",
                ))
                fig_disc.update_layout(
                    title=f"Top {top_n} {ngram_size}-grams in CoT Reasoning",
                    xaxis=dict(title="Frequency (across all responses)"),
                    yaxis=dict(title=""),
                    template="plotly_dark",
                    height=max(450, top_n * 22),
                    margin=dict(l=250, r=60, t=50, b=50),
                )
                st.plotly_chart(fig_disc, use_container_width=True)
                st.caption("🟣 = novel phrases · ⬜ = overlaps with existing confound keywords")

        else:
            # Per-model n-gram frequency
            model_ngrams = {}
            for model_name in sorted(disc_with_cot["Short Model"].unique()):
                model_texts = disc_with_cot[disc_with_cot["Short Model"] == model_name]["_reasoning"]
                ngrams = []
                for text in model_texts:
                    ngrams.extend(extract_ngrams(text, ngram_size))
                model_ngrams[model_name] = Counter(ngrams)

            # Get union of top phrases across all models
            global_counter = Counter()
            for c in model_ngrams.values():
                global_counter.update(c)
            top_phrases = [p for p, _ in global_counter.most_common(top_n)]

            if not top_phrases:
                st.info("No phrases extracted — reasoning text may be too short.")
            else:
                # Build a matrix: phrase × model
                matrix_data = {}
                for model_name, counter in model_ngrams.items():
                    matrix_data[model_name] = [counter.get(p, 0) for p in top_phrases]

                disc_matrix = pd.DataFrame(matrix_data, index=top_phrases)

                fig_disc_hm = go.Figure(data=go.Heatmap(
                    z=disc_matrix.values,
                    x=disc_matrix.columns.tolist(),
                    y=disc_matrix.index.tolist(),
                    colorscale="Viridis",
                    text=disc_matrix.values,
                    texttemplate="%{text}",
                    textfont=dict(size=11, color="white"),
                    hovertemplate="Phrase: %{y}<br>Model: %{x}<br>Count: %{z}<extra></extra>",
                    colorbar=dict(title="Count"),
                ))
                fig_disc_hm.update_layout(
                    title=f"Top {top_n} {ngram_size}-grams by Model",
                    template="plotly_dark",
                    height=max(500, top_n * 24),
                    margin=dict(l=250, r=40, t=50, b=80),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_disc_hm, use_container_width=True)

        # ── Example quotes for a selected phrase ──
        st.markdown("---")
        st.markdown("#### 🔎 Phrase Deep-Dive")
        st.caption("Select a phrase to see example quotes from model reasoning.")

        # Collect all n-grams for the search dropdown
        all_ngrams_for_search = []
        for text in disc_with_cot["_reasoning"]:
            all_ngrams_for_search.extend(extract_ngrams(text, ngram_size))
        search_options = [p for p, _ in Counter(all_ngrams_for_search).most_common(100)]

        if search_options:
            selected_phrase = st.selectbox(
                "Select phrase to inspect",
                options=search_options,
                index=0,
            )

            # Find rows containing this phrase
            phrase_mask = disc_with_cot["_reasoning"].str.contains(
                re.escape(selected_phrase), case=False, na=False
            )
            phrase_rows = disc_with_cot[phrase_mask]

            st.markdown(f"Found in **{len(phrase_rows)}** of {len(disc_with_cot)} responses with CoT.")

            # Show up to 5 example quotes with context
            for i, (_, row) in enumerate(phrase_rows.head(5).iterrows()):
                reasoning_text = row["_reasoning"]
                # Find the phrase and extract surrounding context (±80 chars)
                match = re.search(re.escape(selected_phrase), reasoning_text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 80)
                    end = min(len(reasoning_text), match.end() + 80)
                    snippet = reasoning_text[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(reasoning_text):
                        snippet = snippet + "..."
                else:
                    snippet = reasoning_text[:200] + "..."

                with st.expander(
                    f"{row['Short Model']} · {row.get('Condition Label', '')} · {row['Image']}"
                ):
                    st.markdown(f"**Score:** {row['Raw Score']}")
                    st.code(snippet, language=None)


# ─── TAB 5: RAW DATA ────────────────────────────────────────────────────────

with tab_raw:  # noqa: E303
    st.markdown("## 📋 Raw Data Explorer")
    st.markdown(f"Showing **{len(filtered)}** of {len(df)} total rows.")

    display_cols = [
        "Image",
        "Short Model",
        "Condition Label",
        "Raw Score",
        "Explanation",
        "Reasoning",
    ]
    available = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[available].reset_index(drop=True),
        use_container_width=True,
        height=600,
        column_config={
            "Raw Score": st.column_config.NumberColumn("Score", format="%d"),
            "Short Model": "Model",
            "Condition Label": "Condition",
        },
    )

    # Download button
    csv_bytes = filtered[available].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️  Download filtered CSV",
        data=csv_bytes,
        file_name="filtered_results.csv",
        mime="text/csv",
    )
