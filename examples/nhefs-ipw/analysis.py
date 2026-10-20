"""Reproduce the inverse-probability-weighted effect of quitting smoking on weight gain.

Hernán & Robins, Causal Inference: What If, chapter 12, Programs 12.1-12.3 and 12.7, in Python.
Run `python examples/fetch_data.py nhefs-ipw` first. Writes results/estimates.csv and
results/weights.csv; prints both.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "nhefs.csv"
OUT = HERE / "results"
Z = 1.959964

# The nine confounders of section 12.2: linear and quadratic terms for the continuous ones.
CONFOUNDERS = (
    "C(sex) + C(race) + age + I(age**2) + C(education) + smokeintensity + I(smokeintensity**2)"
    " + smokeyrs + I(smokeyrs**2) + C(exercise) + C(active) + wt71 + I(wt71**2)"
)


def propensity(df: pd.DataFrame) -> pd.Series:
    return smf.glm(f"qsmk ~ {CONFOUNDERS}", df, family=sm.families.Binomial()).fit().predict(df)


def weighted_effect(df: pd.DataFrame, weights: pd.Series) -> dict:
    """Weighted least squares of wt82_71 on qsmk with a robust (HC0) variance, as GEE independence."""
    fit = smf.wls("wt82_71 ~ qsmk", df, weights=weights).fit(cov_type="HC0")
    b, se = fit.params.qsmk, fit.bse.qsmk
    return {"value": b, "low": b - Z * se, "high": b + Z * se, "se": se,
            "mean_quit": fit.params.Intercept + b, "mean_no_quit": fit.params.Intercept, "n": len(df)}


def main() -> None:
    all_ = pd.read_csv(DATA)
    unc = all_[all_.wt82.notna()].copy()  # Program 12.1 line 12

    rows, wrows = [], []
    crude = smf.ols("wt82_71 ~ qsmk", unc).fit()
    ci = crude.conf_int().loc["qsmk"]
    rows.append({"estimate": "Unadjusted difference (Program 12.1)", "value": crude.params.qsmk, "low": ci[0],
                 "high": ci[1], "mean_quit": unc[unc.qsmk == 1].wt82_71.mean(),
                 "mean_no_quit": unc[unc.qsmk == 0].wt82_71.mean(), "n": len(unc)})

    p = propensity(unc)
    w = np.where(unc.qsmk == 1, 1 / p, 1 / (1 - p))
    pn = unc.qsmk.mean()
    sw = np.where(unc.qsmk == 1, pn / p, (1 - pn) / (1 - p))
    rows.append({"estimate": "IP weighted, nonstabilized (Program 12.2)", **weighted_effect(unc, w)})
    rows.append({"estimate": "IP weighted, stabilized (Program 12.3)", **weighted_effect(unc, sw)})
    for name, x in (("W (nonstabilized)", w), ("SW (stabilized)", sw)):
        wrows.append({"weights": name, "min": x.min(), "max": x.max(), "mean": x.mean(), "n": len(x)})

    # Program 12.7: add censoring weights. The treatment model is refit on all 1629 people.
    all_ = all_.assign(cens=all_.wt82.isna().astype(int))
    pa = propensity(all_)
    pna = all_.qsmk.mean()
    sw_a = np.where(all_.qsmk == 1, pna / pa, (1 - pna) / (1 - pa))
    pd_c = 1 - smf.glm(f"cens ~ C(qsmk) + {CONFOUNDERS}", all_, family=sm.families.Binomial()).fit().predict(all_)
    pn_c = 1 - smf.glm("cens ~ C(qsmk)", all_, family=sm.families.Binomial()).fit().predict(all_)
    sw_c = np.where(all_.cens == 0, pn_c / pd_c, 0)
    keep = all_.cens == 0
    sw_ac = (sw_a * sw_c)[keep]
    rows.append({"estimate": "IP weighted for treatment and censoring (Program 12.7)",
                 **weighted_effect(all_[keep], sw_ac)})
    wrows.append({"weights": "SW_A x SW_C", "min": sw_ac.min(), "max": sw_ac.max(), "mean": sw_ac.mean(), "n": len(sw_ac)})

    est, wts = pd.DataFrame(rows), pd.DataFrame(wrows)
    OUT.mkdir(exist_ok=True)
    est.round(4).to_csv(OUT / "estimates.csv", index=False)
    wts.round(4).to_csv(OUT / "weights.csv", index=False)
    with pd.option_context("display.width", 160, "display.max_columns", 10):
        print(est.round(3).to_string(index=False))
        print()
        print(wts.round(3).to_string(index=False))
    print(f"\npeople in file: {len(all_)}; weight measured in 1982: {int(keep.sum())}; "
          f"quitters among them: {int(unc.qsmk.sum())}; ages {unc.age.min()}-{unc.age.max()}")


if __name__ == "__main__":
    main()
