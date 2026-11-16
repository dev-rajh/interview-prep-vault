#!/usr/bin/env python3
"""Merge raw LinkedIn post batches, dedupe by urn, output all-posts.json."""
import json
import glob
import os

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

posts = {}
for path in sorted(glob.glob(os.path.join(RAW, "batch-*.json"))):
    try:
        with open(path, encoding="utf-8") as fh:
            batch = json.load(fh)
    except json.JSONDecodeError as e:
        print(f"WARN: {path}: bad JSON ({e}), skipping")
        continue
    for p in batch:
        urn = (p.get("urn") or "").strip()
        if not urn.startswith("urn:li:activity:"):
            continue
        if urn in posts:
            old = posts[urn]
            # prefer the record with the longer text (expanded)
            if len(p.get("text") or "") > len(old.get("text") or ""):
                posts[urn] = p
        else:
            posts[urn] = p

out = list(posts.values())
out.sort(key=lambda p: p.get("urn", ""), reverse=True)

with open(os.path.join(OUT, "all-posts.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

total_chars = sum(len(p.get("text") or "") for p in out)
empty = sum(1 for p in out if not (p.get("text") or "").strip())
print(f"merged: {len(out)} unique posts (from 67 batches)")
print(f"empty-text posts: {empty}")
print(f"total text chars: {total_chars}")
