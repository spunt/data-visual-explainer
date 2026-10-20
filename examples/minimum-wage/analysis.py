"""Reproduce Card & Krueger (1994) Table 3 and Table 4 column (i) from the public data.

Run `python examples/fetch_data.py minimum-wage` first. Writes results/table3.csv and
results/checks.csv; prints both.

FTE follows the authors' check.sas lines 54-55: full-time + managers + 0.5 x part-time.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "public.dat"
OUT = HERE / "results"

# Column order from the codebook (also the INPUT order in check.sas lines 7-52).
COLUMNS = (
    "SHEET CHAIN CO_OWNED STATE SOUTHJ CENTRALJ NORTHJ PA1 PA2 SHORE NCALLS EMPFT EMPPT NMGRS "
    "WAGE_ST INCTIME FIRSTINC BONUS PCTAFF MEALS OPEN HRSOPEN PSODA PFRY PENTREE NREGS NREGS11 "
    "TYPE2 STATUS2 DATE2 NCALLS2 EMPFT2 EMPPT2 NMGRS2 WAGE_ST2 INCTIME2 FIRSTIN2 SPECIAL2 MEALS2 "
    "OPEN2R HRSOPEN2 PSODA2 PFRY2 PENTREE2 NREGS2 NREGS112"
).split()
TEMPORARILY_CLOSED = [2, 4, 5]  # renovations, highway construction, mall fire (codebook)


def load() -> pd.DataFrame:
    d = pd.read_csv(DATA, sep=r"\s+", header=None, names=COLUMNS, na_values=".")
    d["fte1"] = d.EMPFT + d.NMGRS + 0.5 * d.EMPPT
    d["fte2"] = d.EMPFT2 + d.NMGRS2 + 0.5 * d.EMPPT2
    d["state"] = np.where(d.STATE == 1, "NJ", "PA")
    return d


def mean_se(x: pd.Series) -> tuple[float, float, int]:
    x = x.dropna()
    return x.mean(), x.std(ddof=1) / np.sqrt(len(x)), len(x)


def table3(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for st in ("PA", "NJ"):
        s = d[d.state == st]
        for wave, col in (("before", "fte1"), ("after", "fte2")):
            m, se, n = mean_se(s[col])
            rows.append({"row": f"FTE {wave}, all available", "group": f"{st}_{'pre' if wave == 'before' else 'post'}",
                         "value": m, "se": se, "n": n})
    lv = {r["group"]: r for r in rows}
    did = (lv["NJ_post"]["value"] - lv["NJ_pre"]["value"]) - (lv["PA_post"]["value"] - lv["PA_pre"]["value"])
    se_indep = np.sqrt(sum(r["se"] ** 2 for r in rows))
    rows.append({"row": "Row 3 DiD (difference of mean changes)", "group": "NJ-PA", "value": did, "se": se_indep,
                 "n": None, "note": "SE assumes the four means are independent samples"})

    bal = d.dropna(subset=["fte1", "fte2"]).assign(chg=lambda x: x.fte2 - x.fte1)
    ch = {st: mean_se(bal[bal.state == st].chg) for st in ("PA", "NJ")}
    for st, (m, se, n) in ch.items():
        rows.append({"row": "Row 4 change, balanced sample", "group": st, "value": m, "se": se, "n": n})
    rows.append({"row": "Row 4 DiD, balanced sample", "group": "NJ-PA", "value": ch["NJ"][0] - ch["PA"][0],
                 "se": np.hypot(ch["NJ"][1], ch["PA"][1]), "n": ch["NJ"][2] + ch["PA"][2]})

    tc = d.copy()
    tc.loc[tc.STATUS2.isin(TEMPORARILY_CLOSED), "fte2"] = 0
    bal5 = tc.dropna(subset=["fte1", "fte2"]).assign(chg=lambda x: x.fte2 - x.fte1)
    c5 = {st: mean_se(bal5[bal5.state == st].chg) for st in ("PA", "NJ")}
    rows.append({"row": "Row 5 DiD, temporarily closed set to 0", "group": "NJ-PA", "value": c5["NJ"][0] - c5["PA"][0],
                 "se": np.hypot(c5["NJ"][1], c5["PA"][1]), "n": c5["NJ"][2] + c5["PA"][2]})

    nj = bal[bal.state == "NJ"]
    for label, mask in (("$4.25", nj.WAGE_ST == 4.25), ("$4.26-$4.99", (nj.WAGE_ST > 4.25) & (nj.WAGE_ST < 5)),
                        ("$5.00+", nj.WAGE_ST >= 5)):
        m, se, n = mean_se(nj[mask].chg)
        rows.append({"row": "Row 4 change, NJ by wave-1 starting wage", "group": label, "value": m, "se": se, "n": n})
    return pd.DataFrame(rows)


def checks(d: pd.DataFrame) -> pd.DataFrame:
    t4 = d[d.fte1.notna() & d.fte2.notna() & ((d.STATUS2 == 3) | (d.WAGE_ST2 - d.WAGE_ST).notna())]
    t4 = t4.assign(chg=t4.fte2 - t4.fte1, nj=(t4.state == "NJ").astype(int))
    fit = smf.ols("chg ~ nj", t4).fit()
    dup = d[d.SHEET.duplicated(keep=False)]
    closed = d[d.STATUS2 == 3]
    nj = d[d.state == "NJ"]
    out = [
        ("Stores in file", len(d), "Paper: 410"),
        ("Table 4 sample (n)", len(t4), "Paper: 357"),
        ("Table 4 col (i) NJ coefficient", round(fit.params.nj, 3), "Paper: 2.33"),
        ("Table 4 col (i) SE", round(fit.bse.nj, 3), "Paper: 1.19"),
        ("Table 4 mean change", round(t4.chg.mean(), 3), "Paper: -0.237"),
        ("Table 4 SD of change", round(t4.chg.std(), 3), "Paper: 8.825"),
        ("SHEET values used twice", ", ".join(map(str, sorted(dup.SHEET.unique()))) or "none",
         "Codebook: 'sheet number (unique store id)'"),
        ("Permanently closed stores (STATUS2=3)", len(closed), "Paper: six"),
        ("  of which wave-2 FTE already 0 in the file", int((closed.fte2 == 0).sum()), "Zeroing is in the data, not in check.sas"),
        ("Temporarily closed stores", int(d.STATUS2.isin(TEMPORARILY_CLOSED).sum()), "Paper: four"),
        ("  of which in NJ", int(d[d.STATUS2.isin(TEMPORARILY_CLOSED)].state.eq("NJ").sum()), ""),
        ("NJ stores without a wave-1 starting wage", int(nj.WAGE_ST.isna().sum()), "Excluded from Table 3 cols (iv)-(vi)"),
        ("Wave-2 interview dates", f"{int(d.DATE2.min())} to {int(d.DATE2.max())} (MMDDYY)", "Paper: Nov 5 - Dec 31, 1992"),
    ]
    return pd.DataFrame(out, columns=["check", "value", "reference"])


def main() -> None:
    d = load()
    OUT.mkdir(exist_ok=True)
    t3, ck = table3(d), checks(d)
    t3.round(4).to_csv(OUT / "table3.csv", index=False)
    ck.to_csv(OUT / "checks.csv", index=False)
    with pd.option_context("display.width", 140, "display.max_columns", 10):
        print(t3.round(3).to_string(index=False))
        print()
        print(ck.to_string(index=False))


if __name__ == "__main__":
    main()
