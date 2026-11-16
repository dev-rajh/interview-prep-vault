# 🎯 Interview Prep Vault

A searchable, filterable bank of **1,300+ unique interview questions** extracted and deduplicated from LinkedIn posts — organized **company-wise**, **field-wise**, **topic-wise**, and by **years of experience**.

> **Everything on this site is gathered from LinkedIn posts.** All credit belongs to the original authors. Every question links back to the original LinkedIn post — open the card and click *"View original on LinkedIn"* for full context, answers, and discussion.

**Live site:** https://dev-rajh.github.io/interview-prep-vault/

## What's inside

- **1,327 unique questions** (extracted from 408 source posts, deduplicated)
- Fields: **SQL, PySpark, Spark, System Design, Azure, Databricks, Power BI, ETL, Snowflake, Data Modeling, Machine Learning, Behavioral** and more
- Company-tagged questions from **Deloitte, Microsoft, Amazon, PwC, EY, KPMG, Netflix, JPMorgan, Google, Walmart, Uber, PayPal** and others
- Topics derived from **question content** (window functions, joins, deduplication, SCD, data skew, Delta Lake, streaming…), not from hashtags
- **Experience buckets** (0–2 / 2–4 / 4–7 / 7+ yrs) extracted from each source post

## Features

- 🔍 Full-text search across questions, topics, and companies
- 🏷️ Filters: **field / company / topic / experience** — every dropdown shows counts
- ✅ "Done" checkboxes with localStorage — track your prep progress
- 🎲 **Mock interview generator** — pick a field, company, and experience level, get N random questions
- 📚 **Sources tab** — the original 408 LinkedIn posts, with per-post question counts
- 🌗 Light/dark mode · 📱 mobile-friendly · zero build step (plain HTML/CSS/JS)

## For learners

- Filter by field + topic to drill specific skills (window functions, top-N ranking, SCD…)
- Use the "Not done" view as a running revision list
- Every question links to the original post, where authors often share solutions and discussion

## For interviewers

- Use the mock interview generator to pull a random question set for a field/company/experience combo
- Filter by company to see what its interview loops actually ask
- The Sources tab shows which posts contributed each question

## How this was built

1. Saved LinkedIn posts were extracted via browser automation (post text, author, permalink).
2. Posts were classified into interview-prep vs. other content (`tools/curate.py`).
3. Individual questions were split out of post text, normalized, and deduplicated (`tools/extract_questions.py`) — 1,704 raw questions → 1,327 unique.
4. Topics are tagged from question content; experience buckets come from the source post's stated experience range.
5. The site is a static page reading `data/questions.json` + `data/posts.json` — no framework, no build step.

## Contributing

PRs welcome. Pipeline:

```bash
python3 tools/merge_raw.py          # merge raw batches -> data/all-posts.json
python3 tools/curate.py             # classify posts -> data/posts.json, local/other-posts.md
python3 tools/extract_questions.py  # split + dedupe questions -> data/questions.json
```

## Credits

All content belongs to its original LinkedIn authors. This repo is an index/aggregator for personal study — every entry links to the source post. Non-interview posts were not published; they are summarized in a local-only file (`local/`, gitignored).
