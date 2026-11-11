import io
import pandas as pd
import plotly.express as px
import streamlit as st
from engine import demo_data, analyze, summary, sensitivity, REQUIRED

st.set_page_config(page_title='QuoteGuard | Revenue Assurance',page_icon='🛡️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
[data-testid="stAppViewContainer"]{background:#f6f8fc;color:#15233f}
[data-testid="stSidebar"]{background:#eaf0f8}
h1,h2,h3{color:#172c4b!important;letter-spacing:-.5px}
[data-testid="stMetric"]{background:white;border:1px solid #dce5f1;border-radius:12px;padding:15px}
div.stButton>button[kind="primary"]{background:#18497b;border:0}
.note{background:#e8eff8;border-left:4px solid #285d93;padding:12px 16px;border-radius:5px;color:#1b344f}
</style>''',unsafe_allow_html=True)

st.title('QuoteGuard')
st.caption('QUOTE-TO-CASH  /  REVENUE ASSURANCE & RECOVERY INTELLIGENCE')
st.markdown('<div class="note"><b>Business challenge:</b> Billing mismatches, unapproved discounts, and late collections create revenue leakage. QuoteGuard identifies and prioritizes review opportunities using auditable rules, exposure estimates, and what-if recovery scenarios.</div>',unsafe_allow_html=True)
st.warning('Portfolio demonstration: all default data is synthetic. Monetary exposure is not proven recoverable revenue. Scores are heuristic, not validated predictions. Uploads are processed in-session; do not upload confidential customer data.')

with st.sidebar:
    st.header('Analysis controls')
    uploaded=st.file_uploader('Optional CSV (defined schema)',type=['csv'])
    asof=st.date_input('Analysis as-of date',pd.Timestamp('2026-10-01'))
    rr=st.slider('Billing gap recovery assumption',0,100,65,5)/100
    cr=st.slider('Overdue balance collection assumption',0,100,30,5)/100
    st.divider()
    st.caption('A billing gap is the shortfall versus contract MRR after allowed discounts. Overdue balances are shown separately; discount exposure is diagnostic only to avoid double counting.')
    template=demo_data(6).to_csv(index=False)
    st.download_button('Download example CSV',template,'quoteguard_example.csv','text/csv',use_container_width=True)

try:
    data=pd.read_csv(uploaded) if uploaded is not None else demo_data()
    x=analyze(data,as_of=str(asof),recovery_rate=rr,collection_rate=cr)
except Exception as e:
    st.error(f'Data validation failed: {e}')
    st.stop()

s=summary(x)
a,b,c,d,e=st.columns(5)
a.metric('Invoices',f"{s['invoices']:,}")
b.metric('Billed value',f"${s['billed']:,.0f}")
c.metric('Billing gap',f"${s['billing_gap']:,.0f}")
d.metric('Overdue balance',f"${s['overdue']:,.0f}")
e.metric('Illustrative recovery',f"${s['recoverable']:,.0f}")

t1,t2,t3,t4=st.tabs(['Executive overview','Prioritized worklist','Scenario lab','Method & data dictionary'])
with t1:
    left,right=st.columns([1.2,1])
    with left:
        g=x.groupby('segment',as_index=False)[['billing_gap','overdue_balance']].sum().melt('segment',var_name='Exposure',value_name='USD')
        fig=px.bar(g,x='segment',y='USD',color='Exposure',barmode='group',title='Exposure by customer segment',color_discrete_map={'billing_gap':'#1e5d97','overdue_balance':'#d59c47'})
        fig.update_layout(plot_bgcolor='white',paper_bgcolor='white',legend_title_text='')
        st.plotly_chart(fig,use_container_width=True)
    with right:
        counts=x.risk_tier.value_counts().reindex(['High','Medium','Low'],fill_value=0).reset_index()
        counts.columns=['Risk tier','Invoices']
        fig=px.pie(counts,values='Invoices',names='Risk tier',hole=.58,title='Invoice risk distribution',color='Risk tier',color_discrete_map={'High':'#b4544c','Medium':'#d49b48','Low':'#3a867b'})
        st.plotly_chart(fig,use_container_width=True)
    st.subheader('Where to focus')
    by=x.groupby('recommended_action',as_index=False).agg(invoices=('invoice_id','count'),estimated_recovery=('recoverable_estimate','sum')).sort_values('estimated_recovery',ascending=False)
    st.dataframe(by,use_container_width=True,hide_index=True)
with t2:
    st.subheader('Actionable exception queue')
    tier=st.multiselect('Risk tiers',['High','Medium','Low'],default=['High','Medium'])
    segment=st.multiselect('Segments',sorted(x.segment.dropna().astype(str).unique()),default=sorted(x.segment.dropna().astype(str).unique()))
    work=x[x.risk_tier.astype(str).isin(tier)&x.segment.astype(str).isin(segment)].sort_values(['risk_score','recoverable_estimate'],ascending=False)
    cols=['invoice_id','customer','segment','risk_tier','risk_score','billing_gap','discount_exposure','overdue_balance','recoverable_estimate','recommended_action']
    st.dataframe(work[cols],use_container_width=True,hide_index=True)
    st.download_button('Export filtered exception queue',work[cols].to_csv(index=False),'quoteguard_review_queue.csv','text/csv')
    st.caption('Risk score ranks attention, not probability of fraud or expected actual recovery. Discount exposure may overlap with the gap and is never added to recovery estimate.')
with t3:
    st.subheader('What-if recovery planner')
    st.write(f'At **{rr:.0%}** recovery of billing gaps and **{cr:.0%}** collection of overdue balances, illustrative recovery is **${s["recoverable"]:,.0f}**. Change the sidebar controls to explore assumptions.')
    ss=sensitivity(x)
    fig=px.line(ss,x='billing_recovery_rate',y='scenario_recovery',color='overdue_collection_rate',markers=True,title='Recovery sensitivity to assumptions',labels={'billing_recovery_rate':'Billing gap recovery','scenario_recovery':'Estimated dollars','overdue_collection_rate':'Overdue collection'})
    fig.update_layout(plot_bgcolor='white',paper_bgcolor='white')
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(ss.style.format({'billing_recovery_rate':'{:.0%}','overdue_collection_rate':'{:.0%}','scenario_recovery':'${:,.0f}'}),use_container_width=True,hide_index=True)
    st.caption('Scenario outputs are linear estimates, not causal forecasts. Recovery assumptions are user inputs and should be replaced with historical resolution data before business use.')
with t4:
    st.subheader('How the logic works')
    st.markdown('''**1. Validate inputs.** Check columns, unique invoice IDs, valid dates, nonnegative amounts, and discounts between 0 and 1.\n\n**2. Calculate billing gap.** `max(0, contract_mrr × (1 − min(discount_pct, approved_discount_pct)) − billed_mrr)`. This is a *review signal*, not a confirmed underpayment.\n\n**3. Flag discount exceptions.** Discount above policy threshold triggers review, but is **not** added to monetary opportunity because it may overlap with the billing gap.\n\n**4. Age receivables.** Unpaid past-due invoices contribute outstanding billed value as of the selected date.\n\n**5. Rank.** Transparent weighted heuristic uses billing-gap ratio, excess discount, late days and exception count. It is not a calibrated risk model.\n\n**6. Estimate scenario recovery.** `billing_gap × assumed billing recovery rate + overdue_balance × assumed collection rate`. These are distinct review buckets, not a promise of cash.''')
    st.subheader('Required CSV columns')
    st.code(', '.join(REQUIRED),language='text')
    st.caption('Dates should be ISO YYYY-MM-DD. Discount columns are proportions (0.12 = 12%). Status is Paid or Unpaid. payment_date may be blank for Unpaid.')
    st.subheader('Portfolio relevance')
    st.write('Revenue Operations • Pricing Governance • FP&A • SQL/Python Analytics • Revenue Assurance • Executive Decision Support')

st.divider()
st.caption('QuoteGuard · Independent portfolio project · Synthetic-data demonstration · No affiliation with any named employer')
