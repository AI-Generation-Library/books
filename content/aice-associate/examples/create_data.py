"""Generate fictional, independent tabular rows for this book; no real people."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent / "data"

def main():
    ROOT.mkdir(exist_ok=True)
    rng = np.random.default_rng(20261013)
    n = 600
    tenure = rng.integers(1, 61, n)
    fee = np.round(rng.uniform(15, 110, n), 2)
    calls = rng.poisson(2, n)
    usage = np.round(rng.uniform(0, 100, n), 2)
    contract = rng.choice(["monthly", "yearly"], n, p=[0.65, 0.35])
    region = rng.choice(["east", "west", "south"], n)
    logit = -0.7 + 0.45*calls - 0.03*tenure - 0.015*usage + 0.65*(contract == "monthly")
    churn = (rng.random(n) < 1/(1+np.exp(-logit))).astype(int)
    customer = pd.DataFrame(dict(customer_id=np.arange(1001,1001+n), tenure_months=tenure,
        monthly_fee=fee, support_calls=calls, last_usage=usage, contract_type=contract,
        region=region, churn=churn))
    customer.loc[rng.choice(n, 30, replace=False), "monthly_fee"] = np.nan
    customer.loc[rng.choice(n, 18, replace=False), "contract_type"] = np.nan
    customer.loc[0,"monthly_fee"] = -10
    customer.loc[1,"last_usage"] = -5
    customer.loc[2,"monthly_fee"] = 10000
    # The 10000 value is unusual, not automatically invalid under the data dictionary.
    customer.to_csv(ROOT / "customers.csv", index=False)
    users = rng.integers(1, 160, n)
    days = rng.integers(1, 31, n)
    storage = np.round(rng.uniform(0, 250, n),2)
    plan = rng.choice(["basic", "pro"], n)
    hours = np.maximum(0, 2.5*users + 4*days + 0.3*storage + 35*(plan=="pro") + rng.normal(0,20,n))
    services = pd.DataFrame(dict(record_id=np.arange(1,n+1), active_users=users,
        active_days=days, storage_gb=storage, plan=plan, region=rng.choice(["east","west","south"],n),
        usage_hours=np.round(hours,2)))
    services.loc[rng.choice(n,24,replace=False),"storage_gb"] = np.nan
    services.to_csv(ROOT / "service_usage.csv",index=False)
    pd.DataFrame(dict(region=["east","west","south"], zone=["A","B","C"])).to_csv(ROOT / "regions.csv",index=False)
    print(f"Created {n} fictional customer rows and {n} independent service rows")

if __name__ == "__main__":
    main()
