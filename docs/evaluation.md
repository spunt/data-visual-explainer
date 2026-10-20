# Evaluating a metric card

Three checks, cheapest first. The first two run automatically. The third needs people, and
nothing replaces it: AI "reader personas" explain little of how real readers vary (Persona
Effect, ACL 2024) and are useful only to catch obvious failures before real testing.

## 1. Mechanical (automatic, every build)

```bash
python -m mcard lint cards --strict     # schema, references, recompute, maturity, plain language
python -m pytest tests -q               # model, linter and renderer tests; HTML is network-free
python tools/shoot.py /tmp/mc           # screenshots + interaction checks in real Chrome
```

`tools/shoot.py` checks that glossary toggletips open on keyboard focus and close on Escape,
that quiz feedback appears, and that the page has no script errors.

## 2. Accuracy audit (per card, before sharing)

Have a second person, or a separate agent with no access to the card's drafting history,
check every `exact` field and every number against the cited `src` line ranges. Record:

| Item | Verified / wrong / unverifiable | Note |
|---|---|---|

Wrong items are fixed in the YAML and the card is rebuilt. Unverifiable items get stated as
unknown in the card.

## 3. Comprehension with real readers (before a card becomes `validated`)

Recruit 5 or more readers from the intended audience (for example PMs and finance partners).
Give each person **only layer 1** for two minutes, then ask:

1. **Teach-back:** "Explain this number to a colleague in one or two sentences." Score it
   against the card's own teach-back checklist (who is counted, over what time, what counts,
   compared with what, the main limitation). Teach-back is the best-validated low-cost
   comprehension check (Talevski et al. 2020).
2. **Gist** (the card's `gist` quiz item): tests the bottom-line meaning, which is what people
   act on (fuzzy-trace theory; Reyna et al. 2022).
3. **Detail** (the `verbatim` item): tests the exact number and unit, for example pp vs %.
4. **Transfer** (the `transfer` item): apply the rule to a new case.
5. **Trust:** "How much would you rely on this number for a decision?" (1 to 5), and why.

Then allow full access for five minutes and repeat questions 1 and 4.

**Pass bar for `validated`:** at least 80% correct on gist, at least 80% of teach-backs name
who, when and what counts, and **no reader states a causal claim stronger than
`claim_strength`**. Any item most readers miss is a defect in the card. Fix the matching
`gist`, `misreadings` or `example` field and retest.
