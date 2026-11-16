#!/usr/bin/env python3
"""Curate merged posts: classify interview vs non-interview, tag company + field + topics.

Outputs:
  data/posts.json        - interview questions site data (with tags)
  local/other-posts.md   - summary of non-interview posts (kept local, gitignored)
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tools/ — for extract_questions import

# ---------- company detection (ordered by specificity) ----------
COMPANIES = [
    ("Tredence", r"\bTredence\b"),
    ("Mastercard", r"\bMastercard\b"),
    ("HashedIn by Deloitte", r"HashedIn"),
    ("American Express", r"American Express|\bAmex\b"),
    ("Atlassian", r"\bAtlassian\b"),
    ("Goldman Sachs", r"Goldman Sachs"),
    ("Tiger Analytics", r"Tiger Analytics"),
    ("Deloitte", r"\bDeloitte\b"),
    ("PwC", r"\bPwC\b|PWC"),
    ("EY", r"\bEY\b|\bEY GDS\b"),
    ("KPMG", r"\bKPMG\b"),
    ("Genpact", r"\bGenpact\b"),
    ("JPMorgan", r"J\.?P\.? Morgan|JPMorgan"),
    ("Netflix", r"\bNetflix\b"),
    ("Walmart", r"\bWalmart\b"),
    ("Uber", r"\bUber\b"),
    ("PayPal", r"\bPayPal\b"),
    ("Amazon", r"\bAmazon\b"),
    ("Microsoft", r"\bMicrosoft\b"),
    ("Google", r"\bGoogle\b"),
    ("Meta", r"\bMeta\b"),
    ("Adobe", r"\bAdobe\b"),
    ("Apple", r"\bApple\b"),
    ("Salesforce", r"\bSalesforce\b"),
    ("Swiggy", r"\bSwiggy\b"),
    ("Zomato", r"\bZomato\b"),
    ("Flipkart", r"\bFlipkart\b"),
    ("Blinkit", r"\bBlinkit\b"),
    ("ZS Associates", r"\bZS\b (Associates)?|\bZSAssociates\b"),
    ("Fractal", r"\bFractal\b"),
    ("HDFC Bank", r"\bHDFC\b"),
    ("HSBC", r"\bHSBC\b"),
    ("Citi", r"\bCiti\b"),
    ("Barclays", r"\bBarclays\b"),
    ("NTT Data", r"\bNTT ?DATA\b"),
    ("Wells Fargo", r"Wells Fargo"),
    ("Accenture", r"\bAccenture\b"),
    ("TCS", r"\bTCS\b|Tata Consultancy"),
    ("Infosys", r"\bInfosys\b"),
    ("Wipro", r"\bWipro\b"),
    ("Cognizant", r"\bCognizant\b"),
    ("HCLTech", r"\bHCL(Tech)?\b"),
    ("Persistent Systems", r"Persistent Systems"),
    ("UST", r"\bUST\b"),
    ("Capgemini", r"\bCapgemini\b"),
    ("Optum", r"\bOptum\b"),
    ("PepsiCo", r"\bPepsiCo\b"),
    ("Oracle", r"\bOracle\b"),
    ("L&T", r"\bL&T\b"),
    ("Altimetrik", r"\bAltimetrik\b"),
    ("Bosscoder", r"\bBosscoder\b"),
]

FIELDS = [
    ("PySpark/Spark", r"\bPySpark\b|pyspark|\bSpark\b|SparkSQL"),
    ("Python", r"\bPython\b|\bPandas\b|\bNumPy\b"),
    ("SQL", r"\bSQL\b|sql query|sql interview"),
    ("Databricks", r"\bDatabricks\b"),
    ("Azure", r"\bAzure\b|\bADF\b|Azure Data Factory"),
    ("AWS", r"\bAWS\b|\bS3\b|\bGlue\b|\bRedshift\b"),
    ("Snowflake", r"\bSnowflake\b"),
    ("GCP", r"\bGCP\b|\bBigQuery\b|\bDataflow\b|\bPub/Sub\b"),
    ("Power BI", r"Power ?BI|\bDAX\b"),
    ("Machine Learning", r"machine learning|\bML\b|\bLLM\b|\bRAG\b|neural network"),
    ("Airflow", r"\bAirflow\b"),
    ("Kafka", r"\bKafka\b"),
    ("dbt", r"\bdbt\b"),
    ("Delta Lake", r"\bDelta Lake\b|\bDelta\b"),
    ("System Design", r"system design"),
    ("DSA", r"\bDSA\b|\bLeetcode\b|linked list|binary search|data structures"),
    ("Data Modeling", r"star schema|snowflake schema|\bSCD\b|slowly changing|dimension|fact table"),
    ("ETL", r"\bETL\b|\bELT\b|\bCDC\b"),
]

INTERVIEW_SIGNALS = re.compile(
    r"interview|asked in|question|Q\d|Q\d+\)|1️⃣|2️⃣|🔟|round|cheat ?sheet|case study|"
    r"crack|prep\b|prepare|practice|hiring|roadmap|tips|scenario|solve this|challenge|"
    r"top \d+ questions|\d+ questions|must-?know|from scratch|series",
    re.IGNORECASE,
)

JOB_SIGNALS = re.compile(
    r"hiring:|apply now|we are actively seeking|recruiter|looking for a |open position|"
    r"reach out to .*@.*\.com|resume review|ats score|job seekers|job hunt|open to work",
    re.IGNORECASE,
)

TOPIC_MAP = [
    ("window-functions", r"window function|ROW_NUMBER|RANK\(\)|DENSE_RANK|LAG\(|LEAD\(|OVER \(PARTITION"),
    ("joins", r"\bJOIN\b|INNER JOIN|LEFT JOIN|self join|anti join|broadcast join|shuffle join"),
    ("groupby", r"GROUP BY|aggregation|HAVING|conditional aggregat"),
    ("dedup", r"duplicate|deduplicat|dropDuplicates"),
    ("cte", r"\bCTE\b|WITH clause|common table expression|recursive cte"),
    ("second-highest", r"second highest|2nd highest|nth highest|top-n|top n per group"),
    ("nulls", r"\bNULL\b|null handling|COALESCE|ISNULL|fillna|dropna"),
    ("skew", r"skew|salting|data skew"),
    ("spark-optimization", r"repartition|coalesce|broadcast|cache|persist|shuffle|AQE|Catalyst|lazy evaluation"),
    ("delta-lake", r"Delta Lake|Delta table|MERGE INTO|time travel|Z-ORDER|OPTIMIZE|VACUUM"),
    ("scd", r"\bSCD\b|slowly changing|SCD Type"),
    ("streaming", r"streaming|Kafka|watermark|late-arriving|real-?time|exactly-once"),
    ("data-warehouse", r"star schema|snowflake schema|fact table|dimension|OLAP|OLTP|lakehouse|data lake"),
    ("pyspark-code", r"groupBy|withColumn|dropDuplicates|explode|Window\.partitionBy"),
    ("python-code", r"def |pandas|\.read_csv|decorator|generator|list comprehension"),
    ("optimization", r"optimi[sz]e|performance|slow query|query plan|index|EXPLAIN"),
    ("system-design", r"system design|design a pipeline|architecture|medallion|bronze.*silver.*gold"),
    ("career", r"roadmap|resume|interview prep|salary|job|career|LPA|placement|hiring"),
    ("cheatsheet", r"cheat ?sheet|one ?page|quick reference"),
]


def detect_company(text: str, headline: str) -> str:
    # text only — author headlines ("Senior DE @ ZS") describe employment, not the question source
    # strip hashtags: "#Microsoft" filler should not beat "Accenture Interview" in the body
    body = re.sub(r"#\w+", " ", text)
    # strip product names that collide with company names ("Microsoft Fabric" is a tech, not an interview)
    body = (body.replace("Microsoft Fabric", "Fabric")
                .replace("Amazon Web Services", "AWS")
                .replace("Google Cloud Platform", "GCP")
                .replace("Google Cloud", "GCP"))
    hits = []
    for name, pat in COMPANIES:
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            hits.append((m.start(), name))
    if hits:
        hits.sort()
        return hits[0][1]
    # fallback: company named only as a hashtag (e.g. "interview at #Oracle")
    tags = " ".join(re.findall(r"#(\w+)", text))
    for name, pat in COMPANIES:
        if re.search(pat, tags, re.IGNORECASE):
            return name
    return "General"


def detect_field(text: str, headline: str) -> str:
    blob = text
    hits = [name for name, pat in FIELDS if re.search(pat, blob, re.IGNORECASE)]
    if not hits:
        return "Other"
    # prefer the dominant specialty over generic matches
    priority = ["PySpark/Spark", "Databricks", "Snowflake", "dbt", "Delta Lake",
                "Azure", "AWS", "GCP", "Power BI", "Airflow", "Kafka",
                "Data Modeling", "System Design", "DSA", "ETL",
                "Machine Learning", "Python", "SQL"]
    for p in priority:
        if p in hits:
            return p
    return hits[0]


def detect_topics(text: str) -> list:
    hits = []
    for tag, pat in TOPIC_MAP:
        if re.search(pat, text, re.IGNORECASE):
            hits.append(tag)
    return hits[:8]


# Learning posts: concepts explained, how-to-answer guides, cheat sheets, roadmaps.
LEARN = re.compile(
    r"cheat ?sheet|road ?map|mind ?map|how (?:it|they|spark|sql|this|delta|kafka) works?|"
    r"how to (?:answer|explain|approach|structure|crack)|explain(?:s|ed)? (?:the|how|what|in simple|why)|"
    r"breakdown|step.by.step|terminolog|know the difference|understand(?:ing|ed)? (?:the|how|what|why)|"
    r"visual guide|one.pager|deep dive|mistakes? (?:to avoid|candidates|people|that (?:most|cost))|"
    r"pro tips?|patterns? (?:that|every|to)|day \d+\s*/\s*\d+|execution order|"
    r"architecture (?:explained|of|design)|in simple (?:terms|words)|"
    r"\d+\s*(?:advanced|real|interview|frequently asked)\s*(?:sql|pyspark|python|spark|data)?\s*questions|"
    r"must (?:know|try)|every (?:developer|engineer|analyst|data) (?:should|must)|"
    r"essential \S+ commands|learning (?:journey|path)|things (?:every|to know)|"
    r"how (?:i|you) (?:would )?(?:cracked?|approach|prepare|answer)|roadmap i|"
    r"concepts? (?:explained|you must)|translate business logic|think(?:ing)? (?:like an? )?(?:engineer|analyst|data)",
    re.I,
)


def classify(text: str) -> str:
    """three-way: interview (question source) | learnings | other"""
    from extract_questions import split_questions
    t = (text or "").strip()
    if not t:
        return "media"
    qs = split_questions(t)
    qn = len(qs)
    has_schema = "create table" in t.lower()
    if qn >= 2 or (qn >= 1 and has_schema):
        return "interview"
    if LEARN.search(t) and len(t) > 150:
        return "learnings"
    if qn >= 1:
        return "interview"
    return "other"


def main():
    with open(os.path.join(BASE, "data", "all-posts.json"), encoding="utf-8") as fh:
        posts = json.load(fh)

    curated = []
    learnings = []
    others = []
    for p in posts:
        urn = p.get("urn", "")
        post_url = f"https://www.linkedin.com/feed/update/{urn}/"
        entry = {
            "id": urn.replace("urn:li:activity:", ""),
            "author": p.get("author") or "Unknown",
            "author_url": p.get("authorUrl") or "",
            "post_url": post_url,
            "time": p.get("time") or "",
            "text": (p.get("text") or "").strip(),
        }
        entry["company"] = detect_company(entry["text"], p.get("headline") or "")
        entry["field"] = detect_field(entry["text"], p.get("headline") or "")
        entry["topics"] = detect_topics(entry["text"])
        bucket = classify(entry["text"])
        if bucket == "interview":
            curated.append(entry)
        elif bucket == "learnings":
            learnings.append(entry)
        else:
            note = "media-only post (image/carousel/document)" if not entry["text"] else ""
            others.append({**entry, "note": note})

    curated.sort(key=lambda x: x["id"], reverse=True)
    learnings.sort(key=lambda x: x["id"], reverse=True)
    with open(os.path.join(BASE, "data", "posts.json"), "w", encoding="utf-8") as fh:
        json.dump(curated, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, "data", "learnings.json"), "w", encoding="utf-8") as fh:
        json.dump(learnings, fh, ensure_ascii=False, indent=1)

    # non-interview summary (local only, gitignored)
    os.makedirs(os.path.join(BASE, "local"), exist_ok=True)
    lines = [
        "# Non-interview saved posts (local summary)",
        "",
        f"Extracted {len(posts)} saved posts total. {len(curated)} question posts and "
        f"{len(learnings)} learning posts are published. The remaining {len(others)} are summarized below.",
        "",
    ]
    for e in others:
        note = e.get("note", "")
        first = (e["text"][:220] + "…") if len(e["text"]) > 220 else e["text"]
        lines.append(f"## {e['author']} ({e['time']})" + (f" — {note}" if note else ""))
        lines.append("")
        if first.strip():
            lines.append(first.replace("\n", " ") if note else first)
            lines.append("")
        lines.append(f"[Original post]({e['post_url']})")
        lines.append("")
    with open(os.path.join(BASE, "local", "other-posts.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"question posts: {len(curated)}")
    print(f"learning posts: {len(learnings)}")
    print(f"other / media-only posts: {len(others)}")
    print(f"total: {len(posts)}")

    # quick field/company distribution
    from collections import Counter
    print("\nquestion fields:", Counter(e["field"] for e in curated).most_common(10))
    print("\nlearning fields:", Counter(e["field"] for e in learnings).most_common(10))
    print("\nlearning topics:", Counter(t for e in learnings for t in e["topics"]).most_common(12))


if __name__ == "__main__":
    main()
