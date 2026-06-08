---
name: lilly-media-coverage
description: >-
  Load and analyze the recurring Lilly media-coverage export (a UTF-16,
  tab-separated CSV of news articles from a Meltwater/Onclusive-style monitoring
  tool, tracking Eli Lilly / VERVE-102 / PCSK9 coverage). Use this skill whenever
  the user uploads or names a "Lilly Sample Data" file, a media/PR coverage export,
  a news-monitoring CSV with columns like Document ID, Hit Sentence, Reach, AVE,
  Sentiment, and Source Domain, or asks to analyze coverage volume, sentiment,
  top outlets, reach/AVE, or geography for Lilly or VERVE-102. Trigger even if the
  user just says "analyze this coverage export" or "run the Lilly report" without
  naming the format — the export's odd UTF-16/tab encoding and many empty columns
  make the bundled loader the reliable way in.
---

# Lilly media-coverage export

This skill handles the recurring news-monitoring export for Eli Lilly's
VERVE-102 (a gene-editing therapy targeting PCSK9 to lower LDL cholesterol).
Each row is one news article. The export's format is fixed across weekly pulls,
so the parsing is solved once here and you can focus on the analysis.

## What makes this export tricky (why the loader exists)

- **Encoding**: UTF-16 with a BOM, **tab-separated** — not plain CSV. Naive
  `read_csv` produces garbage.
- **~18 columns are entirely empty** (social-engagement fields, EMV, custom
  fields) because the search is news-only. They add noise and tokens.
- **`Reach` and `AVE` are numbers stored as formatted strings** (`"1,392,071.89"`).
- **`Keywords`, `Keyphrases`, `Links`** pack multiple values into one cell,
  `;`-separated.

`scripts/load_export.py` handles all of this deterministically.

## Step 1 — Load the data

Always load through the bundled script rather than re-deriving the encoding:

```python
import sys
sys.path.insert(0, "scripts")
from load_export import load_export, split_multi

df = load_export("<path-to-export.csv>")   # drops empty cols, fixes numerics
```

Or get a fast profile from the command line:

```bash
python scripts/load_export.py "<path-to-export.csv>" --summary
```

After loading you have ~32 populated columns. The full meaning, format, and
fill rate of every column lives in **`references/columns.md`** — read it only
when you need column-level detail (it's kept out of this file to save tokens).

## Step 2 — Sanity checks before analyzing

- Confirm row count and `Date` range match what the user expects for the pull.
- `Reach` and `AVE` are heavily skewed by a few large outlets — report **sums
  and medians**, not means, unless asked otherwise.
- Dedupe on `Document ID` (primary key); near-duplicates also show up as
  repeated `URL` / `Source Domain` from syndication.
- If `load_export` reports a previously-empty column now has data, tell the
  user — it signals the export config or source mix changed.

## Step 3 — Analysis

<!-- ============================================================ -->
<!-- ANALYSIS PLACEHOLDER                                          -->
<!-- The user is providing the analysis spec separately. When it  -->
<!-- arrives, replace this section with the concrete steps,        -->
<!-- metrics, groupings, and output format they want. Likely      -->
<!-- building blocks given the data:                               -->
<!--   - Coverage volume over time (Date) and by Source/Country    -->
<!--   - Sentiment breakdown (positive/neutral/unknown)            -->
<!--   - Top outlets by article count and by Reach/AVE             -->
<!--   - Reach & AVE totals/medians; flag top-reach articles       -->
<!--   - Geography (Country/State) and Language mix                 -->
<!--   - Theme clustering from Keyphrases (use split_multi)         -->
<!-- Keep output format (docx / xlsx / chat) per the user's spec.  -->
<!-- ============================================================ -->

_Analysis specification pending from the user._ Until it's defined, on request
produce a neutral profile: volume by day, sentiment split, top 10 outlets by
count and by Reach, Reach/AVE totals and medians, and country/language mix.

## Files

- `scripts/load_export.py` — robust loader (UTF-16/tab, drops empty cols,
  normalizes numerics, `split_multi` helper).
- `references/columns.md` — full 50-column reference; read on demand.
