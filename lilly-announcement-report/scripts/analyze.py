#!/usr/bin/env python3
"""
Analysis engine for a Lilly announcement coverage report.

Reads the agency export (via load_export) plus a config.json describing the
analyst's inputs (key messages, Information-Type buckets, competitors, etc.),
computes every metric the deliverable needs, and writes metrics.json. Pair with
make_charts.py to render the charts.

The two judgment-heavy steps — Lilly-context sentiment validation and Top News
tiering — are done by the model, not guessed by this script:
  * Sentiment: pass sentiment_overrides.json ({doc_id: "positive|neutral|negative"})
    produced by the model's validation pass. Rows without an override fall back to
    the export's Sentiment column.
  * Tiering: the script ranks outlets by reach; the model assigns tiers using the
    rubric in references/deliverable-format.md.

Usage:
  python analyze.py <export.csv> <config.json> [--overrides sentiment_overrides.json] \
      [--out metrics.json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from load_export import load_export, split_multi  # noqa: E402


def _bucket_of(info_type, buckets):
    """Map an Information Type value to a coverage bucket label (or None)."""
    it = str(info_type).strip().lower()
    for label, values in buckets.items():
        if it in [v.strip().lower() for v in values]:
            return label
    return None


def _km_text(row):
    """Concatenated searchable text for keyword matching (no full body in export)."""
    parts = [row.get("Title", ""), row.get("Hit Sentence", ""), row.get("Keyphrases", "")]
    return " ".join(str(p) for p in parts if pd.notna(p)).lower()


def _matches(text, keywords):
    """True if any keyword/phrase appears (case-insensitive, word-boundary aware)."""
    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue
        if re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", text):
            return True
    return False


def analyze(export_path, config, overrides=None):
    df = load_export(export_path)
    overrides = overrides or {}
    buckets = config.get("info_type_buckets", {"News & Digital Articles": ["news"]})

    # Assign each row a coverage bucket.
    df["_bucket"] = df["Information Type"].apply(lambda x: _bucket_of(x, buckets))
    included = df[df["_bucket"].notna()].copy()

    # Effective sentiment: model override if present, else export column.
    def eff_sent(r):
        did = str(r.get("Document ID", "")).strip().strip('"')
        return str(overrides.get(did, r.get("Sentiment", "unknown"))).lower()
    included["_sent"] = included.apply(eff_sent, axis=1)

    m = {}

    # --- Sentiment: News / Social / Overall (positive, neutral, negative %) ---
    news_buckets = config.get("sentiment_segments", {}).get(
        "News", ["News & Digital Articles"])
    social_buckets = config.get("sentiment_segments", {}).get("Social", ["Social Media"])

    def sent_pct(sub):
        sub = sub[sub["_sent"].isin(["positive", "neutral", "negative"])]
        n = len(sub)
        if n == 0:
            return None
        g = sub["_sent"].value_counts()
        return [round(100 * g.get("positive", 0) / n),
                round(100 * g.get("neutral", 0) / n),
                round(100 * g.get("negative", 0) / n)]

    sent_rows = []
    for label, blist in (("News", news_buckets), ("Social", social_buckets)):
        sub = included[included["_bucket"].isin(blist)]
        p = sent_pct(sub)
        if p:
            sent_rows.append([label] + p)
    overall = sent_pct(included)
    if overall:
        sent_rows.append(["Overall"] + overall)
    m["sentiment"] = sent_rows

    # --- Type of coverage by reach (% of total reach per bucket) ---
    reach = included.groupby("_bucket")["Reach"].sum()
    total_reach = reach.sum()
    reach_rows, footnote = [], []
    order = list(buckets.keys())
    for b in order:
        if b in reach.index and total_reach > 0:
            pct = 100 * reach[b] / total_reach
            reach_rows.append([b, round(pct, 1) if pct < 1 else round(pct)])
            if pct < 1:
                footnote.append(b)
    m["reach_by_coverage"] = reach_rows
    if footnote:
        m["reach_footnote"] = (
            "Note: " + ", ".join(footnote) +
            " each represent <1% of total reach.")

    # --- Social media volume by channel (Source Name) ---
    social = included[included["_bucket"].isin(social_buckets)]
    if len(social):
        vc = social["Source Name"].value_counts()
        m["social_volume"] = [[name, int(cnt)] for name, cnt in vc.items()]

    # --- Key Message Pull Through (keyword matching) ---
    # The client report measures pull-through as the share of PRIORITIZED OUTLETS
    # that carried each message (denominator = a curated outlet set, e.g. the Top
    # News list), using full text when available -- NOT % of all raw articles.
    # config:
    #   km_method: "outlets" (default, matches client) | "articles"
    #   km_prioritized_sources: [Source Name, ...]  curated denominator (optional)
    #   km_scope: "all" | "news"  (only used for the "articles" method)
    kms = config.get("key_messages", [])
    if kms:
        method = config.get("km_method", "outlets")
        if method == "outlets":
            pri = config.get("km_prioritized_sources")
            scope = included.copy()
            if pri:
                pri_lower = [p.strip().lower() for p in pri]
                scope = scope[scope["Source Name"].astype(str).str.strip().str.lower().isin(pri_lower)]
                denom = len(pri)              # total prioritized outlets
            else:
                denom = scope["Source Name"].nunique()
            scope["_text"] = scope.apply(_km_text, axis=1)
            kmpt = []
            for km in kms:
                hit_mask = scope["_text"].apply(lambda t: _matches(t, km["keywords"]))
                outlets_hit = scope.loc[hit_mask, "Source Name"].nunique()
                pct = round(100 * outlets_hit / denom) if denom else 0
                kmpt.append({"message": km["message"], "pct": pct,
                             "outlets_hit": int(outlets_hit), "total_outlets": int(denom)})
        else:  # "articles": % of all in-scope articles
            scope = included if config.get("km_scope", "all") == "all" else \
                included[included["_bucket"].isin(news_buckets)]
            scope = scope.copy(); scope["_text"] = scope.apply(_km_text, axis=1)
            n = len(scope); kmpt = []
            for km in kms:
                hits = scope["_text"].apply(lambda t: _matches(t, km["keywords"])).sum()
                pct = round(100 * hits / n) if n else 0
                kmpt.append({"message": km["message"], "pct": pct,
                             "hits": int(hits), "total": int(n)})
        m["key_messages"] = kmpt

    # --- Competitor Share of Voice (optional) ---
    comps = config.get("competitors", [])
    if comps:
        sub = included.copy(); sub["_text"] = sub.apply(_km_text, axis=1)
        counts = {}
        for c in comps:
            counts[c["name"]] = int(sub["_text"].apply(
                lambda t: _matches(t, c["keywords"])).sum())
        tot = sum(counts.values())
        if tot:
            m["sov"] = [[k, round(100 * v / tot)] for k, v in counts.items()]

    # --- Top News (ranked by reach; model assigns tiers) ---
    top = included.sort_values("Reach", ascending=False).head(40)
    m["top_news_ranked"] = [
        {"source": r["Source Name"], "title": r["Title"],
         "reach": int(r["Reach"]) if pd.notna(r["Reach"]) else 0,
         "country": r.get("Country", ""), "url": r.get("URL", "")}
        for _, r in top.iterrows()]

    # --- Volume summary for the takeaways narrative ---
    m["summary"] = {
        "total_articles": int(len(included)),
        "by_bucket": {k: int(v) for k, v in included["_bucket"].value_counts().items()},
        "date_range": [included["Date"].min(), included["Date"].max()],
        "total_reach": int(total_reach),
        "countries": int(included["Country"].nunique()),
    }
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("export")
    ap.add_argument("config")
    ap.add_argument("--overrides")
    ap.add_argument("--out", default="metrics.json")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    ov = json.load(open(a.overrides)) if a.overrides else {}
    metrics = analyze(a.export, cfg, ov)
    json.dump(metrics, open(a.out, "w"), indent=2, default=str)
    print(f"Wrote {a.out}")
    print(json.dumps(metrics.get("sentiment"), indent=2))
