# Calculation methodology — Announcement coverage report

Every metric below is computed by `scripts/analyze.py` from the agency export,
driven by a `config.json` the analyst fills in during the interview. Read this
when you need to know exactly how a number or chart is derived, or to explain a
figure to the analyst. The two judgment steps (sentiment validation, Top News
tiering) are done by you, the model — the script handles the deterministic math.

## Segmentation: the Information Type buckets

Coverage is split into buckets the analyst defines in `config.json →
info_type_buckets`, mapping raw `Information Type` values to display labels.
Default mapping:

```json
"info_type_buckets": {
  "News & Digital Articles": ["news"],
  "Social Media": ["social media", "social"],
  "Podcasts": ["podcast", "podcasts"]
}
```

Anything not listed (e.g., "blog", "forum") is excluded from the charts unless
the analyst assigns it to a bucket — confirm during the interview where blogs/
other types should go. Rows whose Information Type isn't in any bucket are
dropped from all metrics (and reported in the summary so nothing is silent).

## 1. Key Message Pull Through (keyword matching)

**Denominator matters — this is the #1 thing that goes wrong.** The client report
measures pull-through as the **share of PRIORITIZED OUTLETS** that carried each
message — *not* the share of all raw articles. In the client's own workbook the
formula is `mentions ÷ total outlets` over a curated set (~70 priority outlets),
which is why their figures read 91% / 91% / 91% / 32%. Running it over all ~1,300+
raw articles instead produces wildly lower numbers (e.g., 33%) — that is the
classic mismatch. Default to the outlets method.

For each key message the analyst supplies a short keyword/phrase list. An outlet
"carries" the message if **any** keyword appears in any of its articles —
case-insensitive, whole-word (so "LDL" won't match "muddled").

- `config → km_method`: **`"outlets"` (default, matches the client)** or
  `"articles"` (legacy % of all articles).
- `config → km_prioritized_sources`: the curated outlet list (Source Names) that
  forms the denominator — usually the Top News / prioritized coverage set. If
  omitted, the denominator is the count of distinct outlets in scope.
- `% = outlets carrying the message ÷ total prioritized outlets × 100`, rounded.
- Searchable text per article = `Title + Hit Sentence + Keyphrases`. **If the
  analyst provides full-text articles, use those** — the client computes on full
  text, and snippets undercount badly.
- Output format: **`XX% [key message]`** (matching the client deliverable), one
  per line, in the analyst's message order unless they ask to sort by %.

Keyword matching is transparent and reproducible (the analyst's choice) but only
catches the words you list. Build each keyword list to cover paraphrases (e.g.,
"one-time", "one-and-done", "single infusion", "single dose") so pull-through
isn't undercounted.

## 2. Sentiment (validate in Lilly context, then chart)

**Step 1 — validate (your job).** The export's `Sentiment` tag reflects general
tone, not impact on Lilly. Re-score where they diverge: coverage can be tonally
neutral but clearly favorable or unfavorable *to Lilly and its products*. Read
`Title + Hit Sentence` and decide:

- Positive for Lilly: efficacy/trial success, pipeline strength, analyst upgrades,
  positive product framing.
- Negative for Lilly: safety concerns, trial failure/doubt, competitive losses,
  stock downgrades, criticism of Lilly or its drug.
- Neutral: factual reporting with no clear Lilly-favorable or -unfavorable lean.

Record your changes as `sentiment_overrides.json` (`{Document ID: "positive"|
"neutral"|"negative"}`). Only include rows you actually re-scored. Pass this file
to `analyze.py --overrides`; everything else falls back to the export tag.
Resolve `unknown` tags here too (assign a class, or leave out if truly
unclassifiable — note the count).

**Step 2 — chart.** `analyze.py` computes Positive/Neutral/Negative % within
**News**, **Social**, and **Overall** (denominator excludes unclassifiable rows).
Rendered by `sentiment_chart` (green / gold / red).

## 3. Type of Coverage by Reach

Sum the `Reach` column per bucket, express each as a % of total reach. Rendered
by `reach_by_coverage_chart` (News maroon, Social peach, Podcasts brown). Per the
brief, **any bucket under 1% gets a footnote** — `analyze.py` emits
`reach_footnote` automatically when that happens; include it under the chart.

Reach is heavily skewed by a few huge outlets, so this chart is about share of
*potential audience*, not article counts (which the volume metrics cover).

## 4. Social Media Volume Breakdown

Count articles per channel using **`Source Name`** among the Social bucket rows
(e.g., X, Bluesky, Reddit). Rendered by `social_volume_chart` (maroon bars,
"Mentions" axis). This is raw post volume, not reach.

## 5. Competitor Share of Voice (Congresses, or when requested)

Usually only for Congresses. The analyst names competitors and keyword lists in
`config → competitors`. SOV = each entity's matched-article count as a % of the
total across all entities.

- If the agency coverage already includes competitor articles, that's the source.
- If not, pull competitor coverage from Meltwater (MW) data and merge before
  running. Rendered by `sov_chart` (Lilly maroon, competitor gold).

For a pure Announcement, skip this section unless the analyst asks for it.

## 6. Top News (ranked by reach, tiered by you)

`analyze.py` returns `top_news_ranked` — the top ~40 articles by `Reach` with
source, title, country, URL. Assign each to a tier using this rubric (adjust to
the analyst's house style):

- **Top Tier** — major mainstream + broadcast (NYT, BBC, Washington Post, CNN…).
- **Investor Influence** — financial/markets wires (Dow Jones, Barron's,
  Bloomberg, Reuters markets, MarketWatch…).
- **Industry / Trade & Policy** — pharma/biotech trade (STAT, Fierce Biotech,
  Endpoints, BioPharma Dive, Scrip, FirstWord, BioSpace, Pharma Letter…).
- **General Population** — consumer/lifestyle (Daily Mail, NY Post, People…).
- **OUS / Global Media** — non-US outlets (use the `Country` field).

List a handful of the highest-reach, most relevant items per tier — it's a
curated snapshot, not an exhaustive dump. Lead with the line the example uses:
"The coverage below reflects a snapshot of the highest-impact publications within
each media tier based on reach; it is not exhaustive."
