#!/bin/bash
# OCR one LinkedIn media post. usage: ocr_one.sh <id>  (image URLs on stdin, page order)
id="$1"
ocr_dir="/Users/raj/Documents/Raj/Codes/LinkedIn/data/ocr"
mkdir -p "$ocr_dir/img"
i=0; rm -f "$ocr_dir/$id.txt"
while read -r url; do
  i=$((i+1))
  f="$ocr_dir/img/${id}-p${i}.png"
  curl -sL --max-time 25 -o "$f" "$url"
  if [ "$(file -b "$f" | grep -ci image)" = "0" ]; then rm -f "$f"; continue; fi
  sips --resampleWidth 1440 "$f" >/dev/null 2>&1
  /opt/homebrew/bin/tesseract "$f" "$ocr_dir/img/${id}-p${i}" --psm 4 2>/dev/null
  cat "$ocr_dir/img/${id}-p${i}.txt" >> "$ocr_dir/$id.txt" 2>/dev/null
done
bytes=$(wc -c < "$ocr_dir/$id.txt" 2>/dev/null | tr -d ' ')
echo "pages:$i bytes:${bytes:-0}"
