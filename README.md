# 🎯 Interview Prep Vault

A searchable, filterable collection of **real interview questions** gathered from LinkedIn posts — organized **company-wise**, **field-wise**, and **topic-wise**.

> **Everything on this site is gathered from LinkedIn posts.** All credit belongs to the original authors. Every entry links back to the original LinkedIn post — open the card and click *"View original on LinkedIn"* for full context, answers, and discussion.

**Live site:** https://dev-rajh.github.io/interview-prep-vault/ (after GitHub Pages is enabled)

## What's inside

- **408 interview-prep posts** from authors like Rakesh D L, Rabi Sankar Mahata, Shilpa Das, Kasi V, Shubham D., and many more
- Coverage: **PySpark, SQL, Spark, Databricks, Azure, Snowflake, Power BI, Data Modeling, Machine Learning, System Design, DSA** and more
- Company-tagged questions from **Deloitte, Microsoft, EY, Google, PwC, Amazon, KPMG, Walmart, Uber, PayPal, American Express, HDFC Bank, Mastercard** and others

## Features

- 🔍 Full-text search across questions, topics, companies, and authors
- 🏷️ Filter by **field / company / topic / difficulty**
- ✅ "Done" checkboxes with localStorage — track your prep progress
- 🎲 **Mock interview generator** — pick a field or company, get N random questions
- 🌗 Light/dark mode (follows system preference)
- 📱 Mobile-friendly, zero build step — plain HTML/CSS/JS

## For learners

- Filter by field and topic to drill specific skills (window functions, SCD, data skew…)
- Use the "Not done" view to keep a running revision list
- Every question links to the original post, where authors often share solutions and discussion

## For interviewers

- Use the mock interview generator to pull a random question set for a given field or company
- Filter by company to see what its interview loops actually ask
- Sort mentally by difficulty signal from the original posts

## How this was built

1. Saved LinkedIn posts were extracted via browser automation (post text, author, and permalink).
2. Posts were classified by heuristics into interview-prep vs. other content, and tagged by company, field, and topic.
3. The site is a static page that reads `data/posts.json` — no framework, no build step.

## Contributing

PRs welcome. To add posts: extend `data/raw/batch-*.json`, then run:

```bash
python3 tools/merge_raw.py   # merge + dedupe -> data/all-posts.json
python3 tools/curate.py      # classify + tag  -> data/posts.json, local/other-posts.md
```

## Credits

All content belongs to its original LinkedIn authors. This repo is an index/aggregator for personal study — each card links to the source post. Non-interview posts were not published; they are summarized in a local-only file (`local/`, gitignored).
