# 4samples_average

Batch-averaged yield trend across the 48 batches of the autonomous Suzuki–Miyaura optimization campaign described in the manuscript.

## Files

| File | Description |
|---|---|
| `192experiments_average.csv` | Per-batch averaged yield of compound **3** (mono-functionalized product). Each batch contains four reactions. Empty rows correspond to batches in which all four reactions failed the SFC error-screening procedure (one batch in this campaign, batch 27). |
| `optimization_average_for_4_samples.ipynb` | Jupyter notebook that produced the CSV from the raw `candidates.csv` of the optimization campaign. |

## How this relates to the v18 manuscript

* The CSV is referenced in the main text of the v18 manuscript (paragraph beginning *"The autonomous campaign comprised 192 attempted conditions..."*).
* It is also the source data for **Figure S14** in the v18 Supporting Information (batch-averaged yield trend plot).
* The plot itself can be regenerated from this CSV using `make_figS14.py` shipped with the manuscript revision package.

## Reproducibility

```bash
# Re-derive 192experiments_average.csv from raw candidates.csv:
jupyter nbconvert --to notebook --execute optimization_average_for_4_samples.ipynb

# Re-render the manuscript Fig. S14 from the CSV:
python /path/to/manuscript-revision/make_figS14.py
```

## Key observations

* Initial random batches 1–4 give batch-averaged yields of 3.9%, 5.9%, 4.4%, and 6.5%.
* Subsequent autonomous batches (5–48) move into the 16–29% range, with one batch reaching 36%.
* The shift demonstrates that the closed-loop campaign concentrated subsequent sampling on higher-yielding regions of the discrete search space, even though individual high-yield combinations remained sparsely scattered. This is consistent with the moderate test-set R² of the GPR model that drives the campaign.
