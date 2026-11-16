#!/usr/bin/env python3
"""Download + OCR a batch of LinkedIn media posts.

usage: ocr_batch.py <batch.json>   # {post_id: [image_urls in page order]}
writes data/ocr/<id>.txt for each post
"""
import json
import subprocess
import sys
import os

OCR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ocr")
os.makedirs(os.path.join(OCR_DIR, "img"), exist_ok=True)


def run(cmd, timeout=40):
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def main():
    with open(sys.argv[1]) as fh:
        batch = json.load(fh)
    for pid, urls in batch.items():
        out = os.path.join(OCR_DIR, f"{pid}.txt")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            print(f"{pid}: already done ({os.path.getsize(out)}b)")
            continue
        pages = 0
        chunks = []
        for i, url in enumerate(urls, 1):
            img = os.path.join(OCR_DIR, "img", f"{pid}-p{i}.png")
            r = run(["curl", "-sL", "--max-time", "25", "-o", img, url])
            if r.returncode != 0 or not os.path.exists(img):
                continue
            with open(img, "rb") as fh:
                magic = fh.read(8)
            if not (magic.startswith(b"\x89PNG") or magic.startswith(b"\xff\xd8")):
                os.remove(img)
                continue
            run(["sips", "--resampleWidth", "1440", img])
            txt = img[:-4] + ".txt"
            r = run(["/opt/homebrew/bin/tesseract", img, txt[:-4], "--psm", "4"], timeout=60)
            if os.path.exists(txt):
                with open(txt, encoding="utf-8", errors="ignore") as fh:
                    chunks.append(fh.read())
            pages += 1
        body = "\n".join(chunks)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"{pid}: pages:{pages} bytes:{len(body)}")


if __name__ == "__main__":
    main()
