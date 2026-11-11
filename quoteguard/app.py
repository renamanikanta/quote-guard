"""QuoteGuard: accessible revenue-assurance decision dashboard (synthetic demo)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from engine import REQUIRED, analyze, demo_data, sensitivity, summary

st.set_page_config(page_title="QuoteGuard | Revenue Assurance", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

INK = "#152B3C"
MUTED = "#526577"
TEAL = "#155E75"
AMBER = "#B7791F"
CORAL = "#B54744"
GREEN = "#27765B"

st.markdown("""<style>
/* One consistent light color system; leave native keyboard controls intact. */
:root { color-scheme: light; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background:#F5F7FA!important; color:#152B3C!important;}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {background:#E9F0F2!important; color:#152B3C!important;}
[data-testid="stHeader"] {background:rgba(245,247,250,.96)!important;}
[data-testid="stToolbar"] {color:#152B3C!important;}
[data-testid="stMainBlockContainer"] {padding-top:2.4rem;max-width:1380px;}
h1,h2,h3,h4, p, label, small, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {color:#152B3C!important;}
h1 {letter-spacing:-1.2px!important;font-size:2.5rem!important;}
h2 {font-size:1.45rem!important;letter-spacing:-.3px!important;margin-top:.35rem!important;}
h3 {font-size:1.08rem!important;}
[data-testid="stCaptionContainer"], .stCaption {color:#526577!important;}
[data-testid="stMetric"] {background:#FFFFFF;border:1px solid #D5E1E7;border-radius:14px;padding:1.0rem 1.2rem;min-height:124px;box-shadow:0 3px 14px rgba(16,42,56,.035);}
[data-testid="stMetricLabel"] p {color:#526577!important;font-weight:650!important;font-size:.92rem!important;}
[data-testid="stMetricValue"] {color:#152B3C!important;font-weight:750!important;}
[data-testid="stTabs"] button {color:#435A6A!important;font-weight:650!important;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#155E75!important;border-bottom-color:#155E75!important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background-color:#155E75!important;}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {border-radius:12px;overflow:hidden;}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p {color:#152B3C!important;}
[data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] .stDownloadButton button {background:#FFFFFF!important;color:#155E75!important;border:1px solid #A8C1CA!important;}
[data-testid="stSidebar"] .stButton button:hover, [data-testid="stSidebar"] .stDownloadButton button:hover {border-color:#155E75!important;}
button:focus-visible, input:focus-visible, textarea:focus-visible {outline:3px solid #0A7897!important;outline-offset:2px;}
.qg-eyebrow{font-size:.77rem;letter-spacing:.14em;text-transform:uppercase;color:#155E75;font-weight:800;margin-bottom:.4rem;}
.qg-hero{background:linear-gradient(120deg,#123449,#17647B);border-radius:18px;padding:28px 32px;color:#FFF;margin-bottom:22px;}
.qg-hero h1{color:#FFF!important;margin:0 0 8px!important;}
.qg-hero p{color:#E8F4F6!important;margin:0;max-width:880px;line-height:1.55;font-size:1.06rem;}
.qg-hero .qg-eyebrow{color:#A9E5DD!important;}
.qg-explainer{background:#EAF3F5;border-left:4px solid #155E75;border-radius:10px;padding:15px 18px;margin:13px 0 22px;line-height:1.55;color:#152B3C;}
.qg-explainer b{color:#123449;}
.qg-card{background:#FFF;border:1px solid #D5E1E7;border-radius:12px;padding:17px 20px;margin:8px 0 17px;min-height:92px;color:#152B3C;}
.qg-card h4{font-size:1.03rem;margin:0 0 7px;color:#123449!important;}
.qg-card p{margin:0;color:#526577!important;line-height:1.5;}
.qg-kicker{font-size:.83rem;font-weight:700;color:#526577;margin:0 0 12px;}
.qg-disclaimer{font-size:.86rem;color:#435A6A;background:#F0F3F5;padding:12px 16px;border:1px solid #D5E1E7;border-radius:9px;margin:20px 0;line-height:1.55;}
@media(max-width:780px){.qg-hero{padding:22px 20px}.qg-hero h1{font-size:2rem!important}[data-testid="stMainBlockContainer"]{padding:1.3rem .7rem}}
</style>""", unsafe_allow_html=True)


def money(v):
    return f"${v:,.0f}"


def card(title, description):
    st.markdown(f'<div class="qg-card"><h4>{title}</h4><p>{description}</p></div>', unsafe_allow_html=True)


def polish(fig, height=335, percent=False):
    fig.update_layout(
        template="plotly_white", height=height,
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", size=13, color=INK),
        margin=dict(l=15, r=15, t=20, b=28),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
        hoverlabel=dict(bgcolor="white", font_color=INK),
    )
    fig.update_xaxes(showgrid=False, linecolor="#D5E1E7", tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor="#E8EEF1", zeroline=False, tickfont=dict(color=MUTED), tickprefix="" if percent else "$")
    return fig


with st.sidebar:
    st.markdown("### ◈ QuoteGuard")
    st.caption("Revenue assurance workspace")
    st.divider()
    st.markdown("**1 · Choose data**")
    uploaded = st.file_uploader("Upload invoices (CSV)", type="csv", help="Optional. Leave empty to explore the synthetic demonstration.")
    st.caption("No file? The built-in sample runs automatically.")
    st.download_button("Download sample CSV", demo_data(6).to_csv(index=False), "quoteguard_sample.csv", "text/csv", use_container_width=True)
    st.divider()
    st.markdown("**2 · Set analysis date**")
    asof = st.date_input("As-of date", pd.Timestamp("2026-10-01"), help="Determines whether unpaid invoices are overdue.")
    st.divider()
    st.markdown("**3 · Test recovery assumptions**")
    rr = st.slider("Billing gap recovery (%)", 0, 100, 65, 5, help="Illustrative portion of flagged billing differences that might be recovered.") / 100
    cr = st.slider("Overdue collection (%)", 0, 100, 30, 5, help="Illustrative portion of overdue unpaid balances that might be collected.") / 100
    st.caption("These are assumptions, not predictions. Changes update all estimated recovery values.")
    st.divider()
    st.caption("Demo data is synthetic. Do not upload confidential or personally identifiable information.")

try:
    data = pd.read_csv(uploaded) if uploaded is not None else demo_data()
    x = analyze(data, as_of=str(asof), recovery_rate=rr, collection_rate=cr)
except Exception as exc:
    st.error(f"Unable to analyze this dataset: {exc}")
    st.info("Download the sample CSV from the sidebar and compare its columns and formats with your file.")
    st.stop()

s = summary(x)
source = "Uploaded CSV" if uploaded is not None else "Synthetic demonstration"

st.markdown('''<section class="qg-hero" aria-label="QuoteGuard overview">
<div class="qg-eyebrow">Revenue operations / financial controls</div>
<h1>QuoteGuard</h1>
<p>Find possible revenue leakage, prioritize invoice reviews, and explore potential cash recovery — with transparent, explainable calculations.</p>
</section>''', unsafe_allow_html=True)
st.markdown(f'<div class="qg-kicker">DATASET: {source} &nbsp; · &nbsp; AS OF: {asof:%b %d, %Y} &nbsp; · &nbsp; {s["invoices"]:,} INVOICES</div>', unsafe_allow_html=True)

st.markdown("## Your revenue assurance snapshot")
st.caption("Potential issues to investigate — not verified losses or guaranteed recoveries.")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Potential billing gap", money(s["billing_gap"]), help="Possible shortfall compared with the contract-based billing benchmark.")
k2.metric("Overdue unpaid balance", money(s["overdue"]), help="Unpaid invoiced value past due as of the selected date.")
k3.metric("Illustrative cash recovery", money(s["recoverable"]), help="Billing gap × assumed recovery + overdue balance × assumed collection.")
k4.metric("High-priority invoices", f'{s["high_risk"]:,}', help="Invoices in the high tier of the illustrative risk score.")
st.markdown('<div class="qg-explainer"><b>How to read this:</b> A billing gap is a possible invoicing discrepancy; an overdue balance is money already invoiced but unpaid. The recovery number is a <b>what-if estimate</b> using the two sliders, not money already recovered. Start with the review queue to see which invoices need action.</div>', unsafe_allow_html=True)

worktab, overviewtab, scenario_tab, methodtab = st.tabs(["01 · What needs attention", "02 · Exposure overview", "03 · Recovery scenarios", "04 · How it works"])

with worktab:
    st.markdown("## Start here: prioritize reviews")
    st.caption("The queue combines possible billing differences, discount exceptions, and overdue invoices in one explainable workflow.")
    priority = x.sort_values(["risk_score", "recoverable_estimate"], ascending=False)
    priority_flags = priority[(priority.billing_gap > 1) | (priority.overdue_balance > 0) | (priority.excess_discount > .001)]
    focus = priority_flags.head(5)
    if focus.empty:
        st.success("No billing, discount, or overdue exceptions found under the current rules.")
    else:
        st.markdown("### Top five invoices to review")
        shown = focus[["invoice_id", "customer", "segment", "risk_tier", "billing_gap", "overdue_balance", "recoverable_estimate", "recommended_action"]].copy()
        shown.columns = ["Invoice", "Customer", "Segment", "Priority", "Billing gap ($)", "Overdue ($)", "Scenario recovery ($)", "Next action"]
        st.dataframe(shown, use_container_width=True, hide_index=True, column_config={
            "Billing gap ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Overdue ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Scenario recovery ($)": st.column_config.NumberColumn(format="$%.2f"),
        })
    st.markdown("### Full investigation queue")
    f1, f2 = st.columns(2)
    with f1:
        tier = st.multiselect("Filter by priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    with f2:
        segment = st.multiselect("Filter by customer segment", sorted(x.segment.dropna().astype(str).unique()), default=sorted(x.segment.dropna().astype(str).unique()))
    filtered = priority_flags[priority_flags.risk_tier.astype(str).isin(tier) & priority_flags.segment.astype(str).isin(segment)]
    st.caption(f"Showing {len(filtered):,} flagged invoices. Risk scores rank review attention; they are not probabilities of fraud.")
    columns = ["invoice_id", "customer", "segment", "risk_tier", "risk_score", "billing_gap", "discount_exposure", "overdue_balance", "recoverable_estimate", "recommended_action"]
    st.dataframe(filtered[columns], use_container_width=True, hide_index=True, height=390,
                 column_config={"billing_gap": st.column_config.NumberColumn("Billing gap ($)",format="$%.2f"),
                                "overdue_balance": st.column_config.NumberColumn("Overdue ($)",format="$%.2f"),
                                "recoverable_estimate": st.column_config.NumberColumn("Recovery scenario ($)",format="$%.2f"),
                                "discount_exposure": st.column_config.NumberColumn("Discount flag ($)",format="$%.2f")})
    st.download_button("Export filtered investigation queue", filtered[columns].to_csv(index=False), "quoteguard_review_queue.csv", "text/csv", use_container_width=False)

with overviewtab:
    st.markdown("## Where is the exposure concentrated?")
    st.caption("Compare possible billing gaps and overdue balances across customer segments; these are different types of exposure.")
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("### Exposure by customer segment")
        g = x.groupby("segment", as_index=False)[["billing_gap", "overdue_balance"]].sum().melt("segment", var_name="Signal", value_name="USD")
        g["Signal"] = g["Signal"].map({"billing_gap": "Potential billing gap", "overdue_balance": "Overdue unpaid"})
        fig = px.bar(g, x="segment", y="USD", color="Signal", barmode="group", color_discrete_map={"Potential billing gap": TEAL, "Overdue unpaid": AMBER}, labels={"segment": "Customer segment", "USD": "Amount (USD)"})
        fig.update_traces(hovertemplate="%{x}<br>$%{y:,.0f}<extra>%{fullData.name}</extra>")
        st.plotly_chart(polish(fig), use_container_width=True)
    with right:
        st.markdown("### Invoices by review priority")
        counts = x.risk_tier.value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
        fig = go.Figure(go.Bar(x=counts.index.tolist(), y=counts.values.tolist(), marker_color=[CORAL, AMBER, GREEN], text=counts.values.tolist(), textposition="outside", hovertemplate="%{x}: %{y} invoices<extra></extra>"))
        fig.update_layout(showlegend=False)
        st.plotly_chart(polish(fig), use_container_width=True)
    st.markdown("### What actions are recommended?")
    action_counts = x.groupby("recommended_action", as_index=False).agg(invoices=("invoice_id", "count"), scenario_recovery=("recoverable_estimate", "sum")).sort_values("scenario_recovery", ascending=False)
    action_counts.columns = ["Recommended action", "Invoices", "Scenario recovery ($)"]
    st.dataframe(action_counts, hide_index=True, use_container_width=True, column_config={"Scenario recovery ($)": st.column_config.NumberColumn(format="$%.2f")})
    st.caption("Total billed invoice value: " + money(s["billed"]) + ". Discount-policy exposure is reported separately in the queue to prevent double-counting it as a second billing gap.")

with scenario_tab:
    st.markdown("## What could recovery look like?")
    st.caption("Explore sensitivity instead of presenting a single assumption as a prediction.")
    a, b = st.columns(2)
    with a:
        card("Billing gap recovery", f"Assume {rr:.0%} of possible billing differences can be resolved and collected. Adjust this rate in the left sidebar.")
    with b:
        card("Overdue balance collection", f"Assume {cr:.0%} of overdue balances can be collected. Change this separately in the left sidebar.")
    st.metric("Current illustrative recovery scenario", money(s["recoverable"]))
    st.markdown("### Compare alternative assumptions")
    grid = sensitivity(x)
    grid["Billing recovery"] = grid.billing_recovery_rate.map(lambda z: f"{z:.0%}")
    grid["Overdue collection"] = grid.overdue_collection_rate.map(lambda z: f"{z:.0%}")
    pivot = grid.pivot(index="Billing recovery", columns="Overdue collection", values="scenario_recovery")
    fig = px.imshow(pivot, text_auto=",.0f", aspect="auto", color_continuous_scale=[[0,"#EAF3F5"],[.5,"#7DB6BC"],[1,"#155E75"]], labels=dict(x="Overdue collection assumption", y="Billing gap recovery assumption", color="USD"))
    fig.update_layout(coloraxis_colorbar=dict(tickprefix="$"))
    st.plotly_chart(polish(fig, 390), use_container_width=True)
    st.caption("Each cell is a hypothetical USD estimate, not a forecast. The model assumes a linear relationship between recovery rates and amounts. It is not validated against actual collection outcomes.")

with methodtab:
    st.markdown("## Transparent methods, not black-box predictions")
    card("1 · Detect a potential billing gap", "Compare billed value against contract MRR after permitted discounts. Differences are review signals; invoices may have valid commercial exceptions.")
    card("2 · Check approval limits", "Flag discounts exceeding the permitted threshold. These flags are not counted a second time in monetary recovery estimates.")
    card("3 · Identify overdue balances", "Flag outstanding unpaid invoices after their due date as of the selected analysis date.")
    card("4 · Rank the review queue", "Apply an explainable heuristic based on billing difference, overdue days, discount exceptions, and combined risk flags. High priority does not imply fraud.")
    card("5 · Test recovery scenarios", "Multiply billing gaps and overdue balances by separately adjustable recovery assumptions. Results are illustrative, not guaranteed cash inflows.")
    st.markdown("### Source data requirements")
    st.code(", ".join(REQUIRED), language="text")
    st.caption("Dates: YYYY-MM-DD. Discount inputs are decimal fractions (0.12 means 12%). Status is Paid or Unpaid; payment_date may be empty for Unpaid.")
    st.markdown("### Formula")
    st.code("potential_billing_gap = max(0, contract_mrr * (1 - min(discount_pct, approved_discount_pct)) - billed_mrr)\nscenario_recovery = potential_billing_gap * billing_recovery_assumption + overdue_balance * collection_assumption", language="python")

st.markdown('<div class="qg-disclaimer"><b>About this demo:</b> QuoteGuard is an independent portfolio project using synthetic sample data by default. Monetary exposure is not proof of recoverable revenue; scores are heuristic, not validated risk predictions. Do not upload sensitive customer data to this public demo.</div>', unsafe_allow_html=True)
st.caption("QuoteGuard · Revenue assurance & decision support · Independent portfolio project")
