#!/usr/bin/env python3
"""Fold OCR'd text (data/ocr/<id>.txt) into data/all-posts.json for posts with empty text."""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clean(t: str) -> str:
    t = re.sub(r"\n{3,}", "\n\n", t)
    lines = [ln.strip() for ln in t.splitlines()]
    return "\n".join(ln for ln in lines if ln).strip()

def main():
    ap = os.path.join(BASE, "data", "all-posts.json")
    posts = json.load(open(ap, encoding="utf-8"))
    ocr_dir = os.path.join(BASE, "data", "ocr")
    folded = 0
    for p in posts:
        if (p.get("text") or "").strip():
            continue
        pid = p["urn"].split(":")[3]
        ocr_path = os.path.join(ocr_dir, f"{pid}.txt")
        rescue_path = os.path.join(BASE, "data", "textrescue", f"{pid}.txt")
        txt_path = ocr_path if os.path.exists(ocr_path) and os.path.getsize(ocr_path) >= 50 else \
            (rescue_path if os.path.exists(rescue_path) and os.path.getsize(rescue_path) >= 50 else None)
        if not txt_path:
            continue
        body = clean(open(txt_path, encoding="utf-8", errors="ignore").read())
        if len(body) < 50:
            continue
        marker = "[OCR from post images]\n" if txt_path == ocr_path else "[Text rescued from permalink page]\n"
        p["text"] = marker + body
        folded += 1
    json.dump(posts, open(ap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"folded OCR text into {folded} posts (of {len(posts)})")

if __name__ == "__main__":
    main()
