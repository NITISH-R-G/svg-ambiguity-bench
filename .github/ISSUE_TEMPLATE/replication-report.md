---
name: Replication report
about: You re-ran a study — or applied the control in your own domain — and want the result recorded
title: "[replication] <what you ran>"
labels: independent-evidence
---

<!--
Replications are recorded whether they agree or disagree, and a disagreement will not be
argued away. TRUST.md currently lists "independent replications: 0"; that number is meant
to change, and to change honestly.

Nothing here needs permission first. Open the issue with whatever you have.
-->

## What did you run?

- [ ] Re-scored the committed responses with your own scorer (Tier 2 — no model needed)
- [ ] Re-ran a study against a model (Tier 4)
- [ ] Applied the format-matched control in a **different domain**
- [ ] Something else

## Setup

- **Study / arms:** <!-- e.g. V1 three-arm, V2 named-id, or your own -->
- **Model(s):**
- **Corpus / dataset:** <!-- the frozen corpus, or your own -->
- **Protocol version:** <!-- instrument-freeze-v1, abstention_rule_version, fmtcontrol spec version -->

## Result

<!--
Numbers as you measured them. If comparing against published values, please give both.
Confidence intervals and the clustering unit are more useful than point estimates alone.
-->

| quantity | your value | published value | agree? |
|---|---|---|---|
| | | | |

## If you applied it in a different domain

- **Representation permuted:**
- **Did it satisfy the applicability condition?** <!-- see METHOD.md: does the representation admit value permutation while preserving token count, field structure, ordering, width? -->
- **Did `check_control` pass?**
- **What broke, if anything:**

<!--
A domain where a valid control CANNOT be constructed is a genuinely important report.
It bounds the method, and the boundary is currently drawn from reasoning rather than
evidence.
-->

## Disagreements

<!--
If your numbers differ from the published ones, that is the point of this template rather
than a problem with it. Please say what you think the cause is, if you have a view - and
it is fine not to.
-->

## Anything you would want stated alongside this in TRUST.md
