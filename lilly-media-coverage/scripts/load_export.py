#!/usr/bin/env python3
"""
Loader for the Lilly media-coverage export (Meltwater/Onclusive-style).

Why this exists: the export ships as UTF-16 (with BOM), tab-separated, with
~18 columns that are entirely empty and a couple of numeric columns stored as
formatted strings ("1,392,071.89"). Re-deriving all of that on every run wastes
tokens and invites parsing bugs, so this script handles it once, deterministically.

Usage:
    python load_export.py "<path-to-export.csv>" [--keep-empty] [--summary]

Returns (when imported):
    load_export(path) -> pandas.DataFrame   # cleaned, empty cols dropped
"""
import argparse
import sys

import pandas as pd

# Columns observed entirely empty in the sample export. They are dropped by
# default because they carry no signal and only add noise/tokens. If a future
# export actually populates one of these, pass --keep-empty (and tell the user).
KNOWN_EMPTY = [
    "Author Handle", "Opening Text", "Hashtags", "Global Reach",
    "National Reach", "Local Reach", "Episode Reach", "EMV", "Quotes",
    "Likes", "Replies", "Reposts", "Comments", "Reactions", "Views",
    "Document Tags", "Custom Categories", "Custom Fields", "Body",
]

# Numeric columns stored as strings. AVE uses thousands separators.
NUMERIC_COLS = [
    "Reach", "AVE", "Social Echo", "Editorial Echo", "Engagement",
    "Shares", "Estimated Views",
]

# Fields holding multiple values joined by ";". Kept as strings on load; split
# on demand with split_multi() so downstream code controls the shape.
MULTI_VALUE_COLS = ["Keywords", "Keyphrases", "Links"]


def load_export(path, keep_empty=False):
    """Read the export and return a cleaned DataFrame.

    Robust to the encoding: tries UTF-16 first (the observed format), then
    falls back to utf-8-sig in case a future export is re-saved differently.
    """
    last_err = None
    for enc in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            df = pd.read_csv(path, sep="\t", encoding=enc, dtype=str)
            break
        except (UnicodeError, UnicodeDecodeError) as e:
            last_err = e
            df = None
    if df is None:
        raise last_err

    df.columns = [c.strip() for c in df.columns]

    # Normalize numerics: strip commas, coerce to float (blanks -> NaN).
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )

    # Drop dead weight unless asked to keep it.
    if not keep_empty:
        drop = [c for c in df.columns if df[c].notna().sum() == 0]
        df = df.drop(columns=drop)

    return df


def split_multi(series):
    """Split a ';'-joined multi-value column into lists of trimmed strings."""
    return series.fillna("").apply(
        lambda v: [p.strip() for p in str(v).split(";") if p.strip()]
    )


def summarize(df):
    """Print a compact profile: shape, date range, fill rates, key counts."""
    print(f"Rows: {len(df)}   Columns kept: {len(df.columns)}")
    if "Date" in df:
        print(f"Date range: {df['Date'].min()} -> {df['Date'].max()}")
    if "Sentiment" in df:
        print("\nSentiment:")
        print(df["Sentiment"].value_counts().to_string())
    if "Country" in df:
        print("\nTop countries:")
        print(df["Country"].value_counts().head(5).to_string())
    for col in ("Reach", "AVE"):
        if col in df:
            s = df[col]
            print(f"\n{col}: sum={s.sum():,.0f}  median={s.median():,.0f}  max={s.max():,.0f}")
    print("\nColumns kept:", ", ".join(df.columns))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help="Path to the export CSV")
    ap.add_argument("--keep-empty", action="store_true",
                    help="Keep columns that are empty in this file")
    ap.add_argument("--summary", action="store_true",
                    help="Print a quick profile and exit")
    args = ap.parse_args()

    df = load_export(args.path, keep_empty=args.keep_empty)
    if args.summary:
        summarize(df)
    else:
        print(f"Loaded {len(df)} rows x {len(df.columns)} columns.")
        print("Columns:", ", ".join(df.columns))
