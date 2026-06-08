# Column reference — Lilly media-coverage export

Read this only when you need column-level detail (meaning, format, fill rate).
The loader already drops the "empty-in-sample" columns, so for most analysis you
work with the ~32 populated columns. Fill rates are from the sample export
(1,339 rows, 2026-05-25 to 2026-05-31, search = VERVE-102).

## Table of contents
1. Identifiers & timing
2. Search / topic context
3. Source & author
4. Article content
5. Geography
6. Language & sentiment
7. Metrics
8. Empty-in-sample columns (dropped by default)

---

## 1. Identifiers & timing

| Column | Fill | Format / notes |
|---|---|---|
| Date | 100% | `YYYY-MM-DD`, publication date. |
| Time | 100% | `HH:MM` (24h). Pair with Date for a timestamp. |
| Document ID | 100% | Unique per article — the **primary key** (wrapped in extra quotes in raw file). |
| URL | 100% | Article link. A few duplicate URLs exist (syndication). |

## 2. Search / topic context

| Column | Fill | Format / notes |
|---|---|---|
| Input Name | 100% | The saved search that captured the row. Single value `VERVE-102` in sample. |
| Keywords | 100% | Matched query terms, `;`-separated. Case varies (Lilly/lilly). Top: VERVE-102, Eli Lilly, PCSK9, LDL-C, hypercholesterolemia. |
| Information Type | 100% | Constant `news` in sample. |
| Content Type | 100% | Constant `News Article` in sample. |

## 3. Source & author

| Column | Fill | Format / notes |
|---|---|---|
| Source Type | 100% | `online news` (~97%), `print`, `Unknown`. |
| Source Name | 100% | Outlet name (848 unique). Top: MarketBeat, Ad Hoc News, XPR Lifestyle. |
| Source Domain | 100% | Outlet domain (786 unique). Good for dedupe/grouping. |
| Author Name | 26% | Byline. Often blank — don't rely on it for grouping. |

## 4. Article content

| Column | Fill | Format / notes |
|---|---|---|
| Title | 100% | Headline. |
| Hit Sentence | 100% | The snippet where the keyword matched (may start/end with `...`). |
| Image | 64% | Lead image URL. |
| Links | 51% | Outbound links found in the article, `;`-separated, each wrapped in quotes. |
| Keyphrases | 99% | Auto-extracted phrases, `;`-separated. Useful for theme clustering. |

## 5. Geography

| Column | Fill | Format / notes |
|---|---|---|
| Country | 100% | 55 countries. US ~57%, then India, China, UK, Germany. |
| State | 42% | US states (and some intl. equivalents). |
| Region | 32% | County / sub-state region. |
| City | 29% | City name. |

## 6. Language & sentiment

| Column | Fill | Format / notes |
|---|---|---|
| Language | 100% | 34 languages. English ~75%, then Chinese (simpl.), German, Spanish. |
| Sentiment | 100% | `positive` / `neutral` / `unknown`. Sample: ~55% positive, ~45% neutral, 2 unknown. (No `negative` rows in sample but expect it generally.) |
| Brand Sentiment | 100% | Constant `unknown` in sample — effectively unused. |

## 7. Metrics

| Column | Fill | Format / notes |
|---|---|---|
| Reach | 100% | Potential audience (int). 0 → ~150M, median ~25K. Highly skewed — prefer median or sum, not mean. |
| AVE | 100% | Advertising Value Equivalent (USD). Stored with thousands separators in raw file; loader converts to float. Sample sum ≈ $34.9M. |
| Social Echo | 6% | Social pickups of the article. |
| Editorial Echo | 2% | Editorial/syndication pickups. |
| Engagement | 7% | Aggregate engagement count. |
| Shares | 2% | Share count. |
| Estimated Views | 45% | Estimated article views. |

> Skew warning: Reach and AVE are dominated by a few huge outlets. Report
> totals and medians; if you mean-average, a single NYT/MSN hit will distort it.

## 8. Empty-in-sample columns (dropped by default)

These had zero values in the sample and the loader drops them unless
`--keep-empty` is passed. If a future export populates any of them, surface it
to the user — it means the export config or source mix changed.

`Author Handle`, `Opening Text`, `Hashtags`, `Global Reach`, `National Reach`,
`Local Reach`, `Episode Reach`, `EMV`, `Quotes`, `Likes`, `Replies`, `Reposts`,
`Comments`, `Reactions`, `Views`, `Document Tags`, `Custom Categories`,
`Custom Fields`, `Body`.

Several of these (Likes, Comments, Views, Hashtags) are social-engagement
fields that stay empty because this export is news-only. They would populate
if the search included social sources.
