---
name: lilly-announcement-report
description: >-
  Produce the Lilly ANNOUNCEMENT coverage report (a "Monitoring Report") and its
  companion email from an agency media-monitoring export (UTF-16, tab-separated
  CSV with columns like Document ID, Information Type, Hit Sentence, Reach, AVE,
  Sentiment, Source Name). Use this skill whenever the user uploads or names a
  Lilly coverage export, a "Monitoring Report", a VERVE-102 / Zepbound / Foundayo
  (or other Lilly product) announcement, or asks to build the client deliverable
  with Key Message Pull Through, Sentiment Analysis, Type of Coverage by Reach,
  Social Media Volume Breakdown, Competitor Share of Voice, or a Top News tier
  list. Trigger even if they just say "run the announcement report", "build the
  monitoring report", or "do the coverage deck" — the export's UTF-16/tab format,
  the interview-driven inputs, and the exact chart color scheme make this skill
  the reliable path. (For Congress reports the flow is the same plus Competitor
  Share of Voice.)
---

# Lilly announcement coverage report

This skill turns an agency coverage export into the two client deliverables: a
formatted **.docx Monitoring Report** and a **separate email**. The analysis is
specified in `references/calculations.md`; the deliverable layout in
`references/deliverable-format.md`; every column in `references/columns.md`. The
scripts do the deterministic work so you can focus on the judgment calls.

## Step 0 — Interview the analyst (do this first)

The report depends on inputs only the analyst has. Ask up front, in one pass:

1. **Announcement vs Congress**, the topic/study name, the `[Code]` and date for
   the filename (e.g., `EAS`, `5.26.26`).
2. **Key messages** — the list, each with a few keywords/phrases to match
   (keyword matching is the agreed method). Cover obvious paraphrases.
3. **Information Type buckets** — which `Information Type` values to include and
   how to bucket them into News / Social / Podcasts (and where blogs/other go).
4. **Competitors** (Congress or on request) — names + keywords; and whether
   competitor data is in the agency export or needs a Meltwater (MW) pull.
5. **Full-text articles?** — if the agency sent full text, use it for Key Message
   Pull Through; otherwise matching runs on Title + Hit Sentence + Keyphrases.

Capture all of this into a `config.json` (schema in `calculations.md`).

## Step 1 — Load and sanity-check

```python
import sys; sys.path.insert(0, "scripts")
from load_export import load_export
df = load_export("<export.csv>")   # UTF-16/tab, drops empty cols, numerics fixed
```

Confirm row count, `Date` range, and the `Information Type` values present match
the analyst's expectation. If a value appears that isn't in any bucket, flag it.

## Step 2 — Validate sentiment in Lilly context

The export's `Sentiment` tag is general tone, not Lilly impact. Re-score rows
where they diverge and write `sentiment_overrides.json`
(`{Document ID: "positive"|"neutral"|"negative"}`). See `calculations.md §2` for
the decision rule. This is the one step that genuinely needs your reading — don't
skip it; it's a brief explicit requirement.

## Step 3 — Run the analysis and render charts

```bash
python scripts/analyze.py "<export.csv>" config.json \
    --overrides sentiment_overrides.json --out metrics.json
python scripts/make_charts.py metrics.json --outdir charts/
```

`metrics.json` holds every number (sentiment %, reach %, social volume, Key
Message Pull Through, SOV, ranked Top News, volume summary). `make_charts.py`
renders only the charts whose data is present, all in the locked color scheme.

## Step 4 — Assemble the deliverables

Follow `references/deliverable-format.md`:

- Write the **Coverage Takeaways** and **snapshot** from the actual articles
  (themes from Keyphrases, verbatim quotes from Title/Hit Sentence).
- Assign **Top News** tiers from `top_news_ranked` using the rubric.
- Build the **.docx** with the `docx` skill, inserting the chart PNGs, named
  `[Code] Monitoring Report_[M.DD.YY].docx`.
- Write the **email** to a companion `..._email.txt`.

Then present both files to the user.

## Color scheme (locked — never change between charts)

Positive `#7BA75B` · Neutral `#F2C310` · Negative `#C0241C` · News & Digital /
Lilly maroon `#521204` · Social Media peach `#F7CCAA` · Broadcast `#A86B4E` ·
Podcasts brown `#8A4B3A` · Competitor gold `#FABF3A`. These maroon/peach/gold
hexes are taken directly from the client's native Office charts. All enforced in
`make_charts.py`.

## Files

- `scripts/load_export.py` — robust UTF-16/tab loader (drops empty cols, fixes
  Reach/AVE, `split_multi` helper).
- `scripts/analyze.py` — computes all metrics from export + config (+ optional
  sentiment overrides) → `metrics.json`.
- `scripts/make_charts.py` — renders the four charts in the locked palette.
- `references/calculations.md` — exact methodology per metric. Read for the how.
- `references/deliverable-format.md` — docx + email structure, naming, Top News
  tiers. Read before assembling.
- `references/columns.md` — full 50-column reference. Read for column detail.
