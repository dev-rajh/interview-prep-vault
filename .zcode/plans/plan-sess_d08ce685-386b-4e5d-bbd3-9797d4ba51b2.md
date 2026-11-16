# LinkedIn Saved Posts → Public Interview-Prep Site

## Context
You have under 100 saved LinkedIn posts, mostly interview questions across fields. Goal: extract all of them with their original links, organize by company / field / topic, and publish a readable, filterable static site as a public GitHub repo (GitHub Pages gives website + repo in one). Non-interview posts get summarized into a local markdown file, not published. Everything published carries an attribution line crediting LinkedIn authors with links back to the originals.

## Phase 1 — Extract (browser automation, ~20-30 min)
1. Open Chromium via the Playwright MCP tools (visible, not headless) at `linkedin.com`.
2. You log in manually (handles password/2FA) and tell me when done.
3. Navigate to My Items → Posts (`linkedin.com/feed/interests/`).
4. Loop: scroll to load more, expand every `…see more`, then run a JS extraction (via `playwright_evaluate`) pulling per post: author name, author headline, post text, relative date, and the activity permalink (`urn:li:activity:…` link).
5. Save each batch to `data/raw/batch-N.json` with the Write tool after every scroll pass — progress survives a dropped session. Merge + dedupe by activity URN at the end. Screenshots along the way to verify nothing is missed.

## Phase 2 — Curate and tag
I read every extracted post and build `data/posts.json`, each entry:
- `author`, `author_url`, `post_url` (original LinkedIn link, kept for reference)
- `company` — company the questions are tied to (e.g. Amazon, TCS), `General` when none
- `field` — DSA, SQL/Databases, System Design, Frontend, Backend, Data Engineering, ML/AI, DevOps/Cloud, QA, Behavioral, etc.
- `topics` — fine-grained tags (Arrays, Joins, React hooks, Python…)
- `difficulty` — Easy/Medium/Hard where inferable
- `text` — full post content

Non-interview posts: summarized into `local/other-saved-posts.md` (folder gitignored, stays on your machine).

## Phase 3 — Static site (zero build step, vanilla HTML/CSS/JS)
Structure:
```
site/
├── index.html      # app shell
├── assets/app.js   # reads data/posts.json, renders everything client-side
├── assets/style.css
└── data/posts.json
```
Features, built for both learner and interviewer:
- Filter chips for **company / field / topic** + full-text search, with live counts
- Each post card shows questions readably (collapsible long posts), author credit, and a **"View original on LinkedIn"** link
- **Done checkboxes** per post, saved in localStorage — progress tracking for prep
- **Mock interview generator**: pick a field/company and a count, get N random questions — interviewer mode
- Footer + README line: *"All questions and content on this site are gathered from LinkedIn posts. Credit goes to the original authors — every entry links back to the original post."*

## Phase 4 — Publish
1. Repo skeleton at workspace root: `README.md` (with attribution + how data was collected), `.gitignore` (`local/`).
2. Create new public repo (proposed name: `interview-prep-vault`, renameable) under your account, fresh git history (the existing remote points to an unrelated old repo and will be replaced), push.
3. Enable GitHub Pages from the repo and verify the live URL.

## Verification
- Local: serve `site/` with `python3 -m http.server`, load it in Playwright, screenshot, check filters/search/done-toggle/mock-generator and console for errors.
- Live: fetch the Pages URL after deploy to confirm it serves.
- Data check: count of published posts + count of summarized non-interview posts should equal total extracted; every published entry has a non-empty `post_url`.

## Notes
- LinkedIn's DOM changes often; selectors will be adapted live during extraction, that's expected.
- Scrolling is done slowly with pauses — staying gentle with LinkedIn's automation limits.