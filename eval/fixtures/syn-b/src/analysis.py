"""Welch t-test on per-user active days from the per_user CTE export."""
import numpy as np
from scipy import stats

def summarize(control, treatment):
    diff = treatment.mean() - control.mean()
    se = np.sqrt(treatment.var(ddof=1) / len(treatment) + control.var(ddof=1) / len(control))
    t, p = stats.ttest_ind(treatment, control, equal_var=False)
    return {"diff": diff, "ci_low": diff - 1.96 * se, "ci_high": diff + 1.96 * se, "p": p}
