"""QuoteGuard: deterministic synthetic quote-to-cash risk analysis.

All dollars, scores, and scenarios are illustrative. No real customer data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED = ['invoice_id','customer','segment','invoice_date','due_date','contract_mrr','billed_mrr','discount_pct','approved_discount_pct','payment_date','status']


def demo_data(n=900, seed=27):
    rng=np.random.default_rng(seed)
    segments=['Enterprise','Mid-Market','SMB']
    seg=rng.choice(segments,n,p=[.25,.36,.39]); base=np.select([seg=='Enterprise',seg=='Mid-Market'],[rng.uniform(4500,18000,n),rng.uniform(1000,5500,n)],default=rng.uniform(180,1500,n))
    dates=pd.to_datetime('2025-10-01')+pd.to_timedelta(rng.integers(0,365,n),unit='D')
    contracted=np.round(base,2); billed=contracted.copy(); discount=rng.uniform(0,.12,n).round(3); approved=np.where(seg=='Enterprise',.15,.10)
    under=rng.random(n)<.095; billed[under]*=rng.uniform(.65,.96,under.sum())
    overdiscount=rng.random(n)<.082; discount[overdiscount]=approved[overdiscount]+rng.uniform(.02,.16,overdiscount.sum())
    billed=np.round(billed*(1-discount),2)
    due=dates+pd.to_timedelta(30,unit='D'); late_days=rng.integers(-8,55,n)
    unpaid=rng.random(n)<.105; pay=due+pd.to_timedelta(late_days,unit='D')
    pay=pd.Series(pay);pay.loc[unpaid]=pd.NaT
    status=np.where(unpaid,'Unpaid','Paid')
    return pd.DataFrame({'invoice_id':[f'INV-{i:05}' for i in range(1,n+1)],'customer':[f'Account {k:03}' for k in rng.integers(1,210,n)],'segment':seg,'invoice_date':dates,'due_date':due,'contract_mrr':contracted,'billed_mrr':billed,'discount_pct':discount,'approved_discount_pct':approved,'payment_date':pay,'status':status})


def validate(df):
    missing=set(REQUIRED)-set(df.columns)
    if missing: raise ValueError('Missing required columns: '+', '.join(sorted(missing)))
    x=df.copy()
    if x['invoice_id'].isna().any() or x['invoice_id'].duplicated().any():raise ValueError('invoice_id values must be unique and nonempty.')
    for c in ['contract_mrr','billed_mrr','discount_pct','approved_discount_pct']:
        x[c]=pd.to_numeric(x[c],errors='raise')
        if not np.isfinite(x[c]).all():raise ValueError(f'{c} must be finite.')
    if (x[['contract_mrr','billed_mrr']]<0).any().any():raise ValueError('Amounts cannot be negative.')
    if ((x[['discount_pct','approved_discount_pct']]<0)|(x[['discount_pct','approved_discount_pct']]>1)).any().any():raise ValueError('Discounts must be fractions from 0 to 1.')
    for c in ['invoice_date','due_date','payment_date']:x[c]=pd.to_datetime(x[c],errors='coerce')
    if x[['invoice_date','due_date']].isna().any().any():raise ValueError('Invoice and due dates must be valid.')
    if (x['due_date']<x['invoice_date']).any():raise ValueError('Due dates must not precede invoice dates.')
    if not x['status'].isin(['Paid','Unpaid']).all():raise ValueError('status must be Paid or Unpaid.')
    if ((x['status']=='Paid') & x['payment_date'].isna()).any():raise ValueError('Paid invoices require a payment_date.')
    return x


def analyze(df, as_of='2026-10-01', recovery_rate=.65, collection_rate=.30):
    x=validate(df)
    asof=pd.Timestamp(as_of)
    # Amount net of approved discount is an illustrative baseline, not a legal entitlement.
    x['expected_billing']=x.contract_mrr*(1-np.minimum(x.discount_pct,x.approved_discount_pct))
    x['billing_gap']=np.maximum(0,x.expected_billing-x.billed_mrr).round(2)
    x['excess_discount']=np.maximum(0,x.discount_pct-x.approved_discount_pct).round(4)
    x['discount_exposure']=(x.contract_mrr*x.excess_discount).round(2)
    x['days_past_due']=np.where(x.status=='Unpaid',np.maximum(0,(asof-x.due_date).dt.days),np.maximum(0,(x.payment_date-x.due_date).dt.days))
    x['overdue_balance']=np.where((x.status=='Unpaid')&(x.days_past_due>0)&(x.due_date<=asof),x.billed_mrr,0.)
    x['risk_flags']=((x.billing_gap>1).astype(int)+(x.excess_discount>.001).astype(int)+(x.overdue_balance>0).astype(int))
    x['risk_score']=np.minimum(100,(x.billing_gap/np.maximum(1,x.contract_mrr)*190 + x.excess_discount*170 + np.minimum(x.days_past_due,90)*.40 + x.risk_flags*12)).round(0).astype(int)
    x['risk_tier']=pd.cut(x.risk_score,[-1,29,59,100],labels=['Low','Medium','High'])
    x['recoverable_estimate']=(x.billing_gap*recovery_rate+x.overdue_balance*collection_rate).round(2)
    # Do not add discount_exposure: it overlaps billing_gap and would double count.
    x['recommended_action']=np.select([x.billing_gap>1,x.overdue_balance>0,x.excess_discount>.001],['Review invoice against contract','Prioritize collections follow-up','Review discount approval'],default='Monitor')
    return x


def summary(x):
    return {'invoices':len(x),'billed':float(x.billed_mrr.sum()),'billing_gap':float(x.billing_gap.sum()),'overdue':float(x.overdue_balance.sum()),'recoverable':float(x.recoverable_estimate.sum()),'high_risk':int((x.risk_tier=='High').sum())}


def sensitivity(x, recovery_rates=(.25,.5,.75,.9), collection_rates=(.15,.3,.45)):
    return pd.DataFrame([{'billing_recovery_rate':r,'overdue_collection_rate':c,'scenario_recovery':round(float(x.billing_gap.sum()*r+x.overdue_balance.sum()*c),2)} for r in recovery_rates for c in collection_rates])
