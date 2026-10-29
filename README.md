# Lab 17 — Point-in-Time Audit

**Question:** Was each number knowable on the day I would have traded on it, and may Project 2 use it?

## Run

```bash
python -m pip install -r requirements.txt
python -m streamlit run asof_app.py
```

The app downloads current FRED and historical ALFRED CSVs without a key. Its default series are BAA, FEDFUNDS, DGS10 and MORTGAGE30US; DGS10 is also entered as the selected audit series. Change the custom ID to PAYEMS for the revision probe. The chart starts on January 1, 2020; comparison counts use full histories. A dot or blank is missing, never zero. Each download is cached for an hour; Refresh downloads clears the cache. Fetch timestamps appear below each chart.

[App](asof_app.py) · [Live validation results](validation.md) · [Reproduce validation](validate.py)

```bash
python validate.py
```

The expected numbers in `validate.py` are assertions from the assignment, never inputs to the app. The app independently downloads every displayed value.

## Data card — DGS10

| Field | Evidence / interpretation |
|---|---|
| Source and link | Federal Reserve Board, H.15 Selected Interest Rates, distributed by [FRED](https://fred.stlouisfed.org/series/DGS10); historical vintages from [ALFRED](https://alfred.stlouisfed.org/series?seid=DGS10). |
| Measure | Market yield on U.S. Treasury securities at 10-year constant maturity, quoted on an investment basis. This is a yield interpolated from the Treasury curve, not a fund price or a realized total return. |
| Units and frequency | Percent per annum, not seasonally adjusted; daily business-day observations. A value of 4.99 means 4.99%, or 0.0499 in decimal calculations. |
| Publication lag | The [H.15 release](https://www.federalreserve.gov/releases/h15/) is posted on business days at 4:15 p.m. Eastern, excluding holidays and closures. On the inspected October 28 release, the latest observation is October 27: roughly one business day in this sample. FRED ingestion may add delay; neither a same-day assumption nor a universal calendar-day lag is safe. |
| Revisions | Daily market yields are generally less revised than payroll estimates, but FRED explicitly says data are subject to revision. Compare matching dates in ALFRED and FRED; the observed revision count is evidence for the tested window, not proof that corrections never occur. |
| Download / inspection date | October 29, 2026. Actual downloads and their timestamps are shown by the app; the saved validation records this run. |
| Relevance | For the SGOV/BND/VT universe, long-term Treasury yields help describe duration risk in BND and discount-rate conditions for VT. SGOV has much shorter rate exposure. This is an economic rationale for a candidate input, not evidence of predictive performance. |

## Evidence and interpretation

The four October 5, 2026 reference checks and the PAYEMS January 15, 2025 probe are recorded in [validation.md](validation.md). PAYEMS is compared on the **same December 2024 observation date**, so later payroll growth cannot be mistaken for a revision.

The selected DGS10 series is also compared as known on September 30, 2026 and on the download date. The older vintage ends before the current file: subsequent observations were unavailable then. The source-page comparison records October 23, 26 and 27 against FRED. Those preparation checks were AI-assisted; the student's own checks will be done in class.

The observation date identifies what day the rate measures. The vintage date determines which historical file is retrieved. Dropping future observation dates from today's file would not remove revised values and is therefore insufficient. The app compares values only on shared, nonmissing dates and separately counts observations after the vintage's last observation date.

## Project 2 call — admit conditionally

Admit DGS10 only when each historical decision uses its corresponding ALFRED vintage and the last observation available by that decision. For a decision before the day's publication time, use the preceding business day's end-of-day vintage, or a documented earlier available vintage; a date-only vintage does not establish intraday availability. Preserve missing observations and document any use of the latest previously published value.

This admission concerns data availability, not profitability. Quarantine any period where the vintage cannot be retrieved, the release timing cannot support the trade timestamp, or a source discrepancy is unresolved. Re-admit only after timestamped source evidence or a valid archived vintage resolves the gap. Never replace a failed historical download with today's values.

## In class — left for the actual activities

- Explain the selected rate's economic relevance to the partner before using the screen.
- Personally check three observations against FRED.
- Explain `download_asof` line by line without AI; answer the partner's code question.
- Record the actual partner attack on publication timing, revisions or units and answer it in two evidence-based sentences under this card.
- Discuss the publication lag and what a backtest using today's file could overstate; complete the individual Brightspace checkout with the GitHub file links.

Partner statements and no-AI activities have not been invented. The separate open-ended challenge is an after-class extension and is not included in this required submission.
