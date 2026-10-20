# Worked examples

Each folder holds the analysis code behind one card in `../cards/`. The source data are not in
this repository: `fetch_data.py` downloads them from the authors' sites into `<case>/data/`
(git-ignored) and checks each file's SHA-256 against the value recorded when the card was
written.

| Case | Card | Source | What is reproduced |
|---|---|---|---|
| `minimum-wage/` | `minimum-wage-did.yaml` | Card & Krueger (1994), *AER* 84(4); data and SAS program from davidcard.berkeley.edu/data_sets.html | Table 3 rows 1–5, Table 4 column (i), and checks against the paper's text |
| `nhefs-ipw/` | `smoking-cessation-ipw.yaml` | Hernán & Robins, *Causal Inference: What If*, chapter 12; data and R code from miguelhernan.org/whatifbook | Programs 12.1–12.3 and 12.7 |

```bash
python examples/fetch_data.py all
python examples/minimum-wage/analysis.py   # writes minimum-wage/results/*.csv
python examples/nhefs-ipw/analysis.py      # writes nhefs-ipw/results/*.csv
```

The `results/` CSVs are committed as receipts: they are the numbers each card cites.

**Licences.** Neither source states a licence for its data, so nothing is redistributed. If a
source changes a data file, `fetch_data.py` stops with an error rather than silently producing
different numbers. If a paper or book PDF changes, it warns: authors revise those in place, and
the cited passages should be rechecked.

**Adding a case.** Pick a published analysis whose data, code and reported numbers are all
public, so the card can be checked against an answer someone else wrote. Add its files to
`MANIFEST` in `fetch_data.py`, write an `analysis.py` that reproduces the published figures, and
then write the card by following `SKILL.md`.
