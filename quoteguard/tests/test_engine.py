from engine import demo_data, analyze, summary, validate
import pandas as pd
import pytest

def test_demo_is_deterministic():
    assert demo_data(10).equals(demo_data(10))

def test_does_not_double_count_discount_exposure():
    x=analyze(demo_data(200),recovery_rate=.6,collection_rate=.25)
    assert ((x.recoverable_estimate - (x.billing_gap*.6+x.overdue_balance*.25)).abs()<.02).all()
    assert summary(x)['billing_gap']>=0

def test_duplicate_rejected():
    x=demo_data(2)
    x.loc[1,'invoice_id']=x.loc[0,'invoice_id']
    with pytest.raises(ValueError):validate(x)

def test_exposure_nonnegative():
    x=analyze(demo_data(40))
    assert (x[['billing_gap','overdue_balance','recoverable_estimate']]>=0).all().all()
