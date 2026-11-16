#!/usr/bin/env python3
"""Extract individual questions from curated posts, dedupe, and tag them.

Input:  data/posts.json  (curated interview posts)
Output: data/questions.json (unique questions, each with sources)
        data/posts.json     (unchanged, kept as source list)
"""
import json
import os
import re
import unicodedata
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- text cleanup ----------

def nfkc(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"[\uFE0E\uFE0F\u20E3]", "", text)  # keycap/variation-selector leftovers from emoji digits


NOISE = re.compile(
    r"(https?://|lnkd\.in|www\.|#[a-z]|"
    r"^\s*(?:follow|like and|liked|reshare|repost|save (?:this|for)|comment below|share (?:this|it|your)|"
    r"get (?:the|your|it)|download|join (?:the|our|my|us)|subscribe|book (?:a|1:1)|dm\b|topmate|youtube|whatsapp|telegram|"
    r"coupon|use (?:code|coupon)|apply now|apply for|reach out|register|enroll|limited (?:slots|seats|time)|offer valid|"
    r"checkout|check out|connect (?:with|me|1:1)|credits?:|image credit|post credits|contact|phone)\b)",
    re.I,
)

META = re.compile(r"^\s*(ctc|compensation|position|role|salary|package|exp(?:erience)?|application process|"
                  r"difficulty|location|experience)\b[^a-z]*", re.I)

SQLCODE = re.compile(r"^\s*(select|from|with|insert|update|delete|create|alter|drop|group by|order by|where|having|"
                     r"join|on\b|as\b|union|values|set\b|case when|sum\(|count\(|avg\(|min\(|max\(|rank\(\)|row_number|"
                     r"dense_rank|partition by|limit|offset|merge into|when matched|then)\b", re.I)

VERB = re.compile(r"^(write|create|design|explain|how|what|why|when|which|who|where|find|given|describe|tell|"
                  r"calculate|compute|compare|list|name|can|do|does|is|are|identify|detect|fetch|delete|remove|"
                  r"merge|sort|count|extract|return|select|generate|parse|process|implement|optimize|optimise|"
                  r"debug|handle|convert|build|rank|retrieve|differentiate|difference|discuss|walk|share|suggest|"
                  r"estimate|prepare|use|using|what.s)\b", re.I)

MARKER = re.compile(r"^\s*(?:(?:q|ques)\s*\d{0,2}\s*[\).:]?\s+|\d{1,2}\s*[\.\):]\s*|[•▪▸◦●○·*→➜➡↳✅✔☑🔹🔸⭕❓💬⁃‣\-–—]\s+)", re.I)

ENGAGEMENT = re.compile(
    r"^(?:which of (?:these|the)|which ones|which (?:one|topics?|questions?) (?:do|would|is)|"
    r"what(?:'s| is| are) your (?:favorite|go.?to|biggest)|"
    r"did i miss|let me know|drop your|comment below|have you (?:ever )?faced|how many (?:of )?(?:these|you)|"
    r"are you (?:ready|preparing|struggling)|what would you (?:do|say)|"
    r"what(?:'s| is) the (?:toughest|most (?:difficult|challenging))|"
    r"which (?:topic|concept|question) do|what (?:pyspark|sql) (?:command|function) do you use|"
    r"which (?:of these|stage|lesson|method))",
    re.I,
)

GENERIC = {"can you solve this", "can you solve", "how would you solve this", "how would you solve it",
           "can you crack this", "solve this", "your task", "the challenge", "try solving it"}

MIN_LEN = 14


def is_heading(line: str) -> bool:
    if "?" in line or len(line) > 30:
        return False
    if MARKER.match(line):
        # short numbered roadmap items like "1. SQL"
        body = MARKER.sub("", line).strip()
        if len(body) <= 28 and not VERB.match(body):
            return True
        return False
    return len(line) <= 30


def qualifies(body: str) -> bool:
    if len(body) < MIN_LEN or len(body) > 600:
        return False
    if NOISE.search(body) or SQLCODE.match(body) or ENGAGEMENT.match(body):
        return False
    norm = normalize_key(body)
    if norm in GENERIC or len(norm) < 8:
        return False
    if "?" in body:
        return True
    return bool(VERB.match(body))


def clean_body(line: str) -> str:
    line = MARKER.sub("", line).strip()
    line = re.sub(r"^\d{1,2}\s+(?=(write|explain|how|what|why|find|design|given|describe|tell|calculate|which|identify|fetch|list|compare))", "", line, flags=re.I)
    line = re.sub(r"\s*…\s*see more\s*$", "", line, flags=re.I)
    line = re.sub(r"\s+", " ", line).strip(" -:;·,")
    return line


def split_questions(text: str) -> list:
    lines = [l.strip() for l in nfkc(text).split("\n") if l.strip()]
    # emoji digits (1️⃣) become "1 Write..." after NFKC — strip leading numbering when followed by a verb
    lines = [re.sub(r"^\d{1,3}\s+(?=\S)", "", l) if VERB.match(re.sub(r"^\d{1,3}\s+", "", l)) else l for l in lines]
    out = []
    cur = None
    joins = 0
    for line in lines:
        if NOISE.search(line) or META.match(line) or SQLCODE.match(line):
            cur = None
            continue
        if is_heading(line):
            cur = None
            continue
        if MARKER.match(line) or VERB.match(line):
            if cur:
                out.append(cur)
            cur = clean_body(line)
            joins = 0
        elif cur is not None and joins < 2 and "?" not in cur:
            cur = (cur + " " + line).strip()
            joins += 1
        else:
            if cur:
                out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    seen = set()
    result = []
    for q in out:
        if not qualifies(q):
            continue
        k = normalize_key(q)
        if k in seen:
            continue
        seen.add(k)
        result.append(q)
    return result


# ---------- normalization + dedupe ----------

FILLER = [
    r"^(?:please\s+)?(?:can|could)\s+you\s+(?:please\s+)?",
    r"^how\s+(?:would|do|can|did|should)\s+(?:you|we|one|i)\s+",
    r"^(?:write|create|give|provide|develop|build)\s+(?:an?\s+)?(?:sql\s+|pyspark\s+|python\s+|spark\s+)?(?:query|program|code|script|function|solution)?\s*(?:to|for|that|which|and)?\s*",
    r"^tell\s+me\s+(?:about\s+)?(?:the\s+)?",
    r"^(?:explain|describe)\s+",
    r"^(?:the\s+)?(?:difference\s+between|diff\s+between|difference\s+in)\s+",
]


def normalize_key(text: str) -> str:
    t = nfkc(text).lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for _ in range(2):
        for pat in FILLER:
            t = re.sub(pat, "", t).strip()
    t = re.sub(r"^(in|on|for|of|the|a|an)\s+", "", t)
    return t.strip()


def tokens(key: str) -> set:
    stop = {"the", "a", "an", "of", "in", "on", "for", "to", "and", "is", "are", "it", "with", "using", "per",
            "s", "ll", "ve", "re", "don", "t", "you", "your", "we", "our", "how", "do", "would", "can", "please"}
    return set(key.split()) - stop


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedupe(items: list) -> list:
    """items: list of dicts with 'key','toks','text',... Greedy fuzzy clustering."""
    clusters = []  # each: {"rep_toks": set, "members": [items]}
    for it in items:
        placed = False
        for cl in clusters:
            rt = cl["rep_toks"]
            if not rt or not it["toks"]:
                continue
            ratio = len(rt) / len(it["toks"])
            if ratio < 0.45 or ratio > 2.2:
                continue
            j = jaccard(rt, it["toks"])
            inter = len(rt & it["toks"])
            diff = len(rt ^ it["toks"])
            if j >= 0.75 or (inter / min(len(rt), len(it["toks"])) >= 0.92 and diff <= 1 and min(len(rt), len(it["toks"])) >= 6):
                cl["members"].append(it)
                if len(it["toks"]) > len(rt):
                    cl["rep_toks"] = it["toks"]
                placed = True
                break
        if not placed:
            clusters.append({"rep_toks": set(it["toks"]), "members": [it]})
    return [cl["members"] for cl in clusters]


# ---------- tagging ----------

COMPANIES = [
    ("Tredence", r"\bTredence\b"), ("Mastercard", r"\bMastercard\b"), ("HashedIn", r"HashedIn"),
    ("American Express", r"American Express|\bAmex\b"), ("Atlassian", r"\bAtlassian\b"),
    ("Goldman Sachs", r"Goldman Sachs"), ("Tiger Analytics", r"Tiger Analytics"),
    ("Deloitte", r"\bDeloitte\b"), ("PwC", r"\bPwC\b|PWC"), ("EY", r"\bEY\b"), ("KPMG", r"\bKPMG\b"),
    ("Genpact", r"\bGenpact\b"), ("JPMorgan", r"J\.?P\.? Morgan|JPMorgan"), ("Netflix", r"\bNetflix\b"),
    ("Walmart", r"\bWalmart\b"), ("Uber", r"\bUber\b"), ("PayPal", r"\bPayPal\b"), ("Amazon", r"\bAmazon\b"),
    ("Microsoft", r"\bMicrosoft\b"), ("Google", r"\bGoogle\b"), ("Meta", r"\bMeta\b"), ("Adobe", r"\bAdobe\b"),
    ("Swiggy", r"\bSwiggy\b"), ("Zomato", r"\bZomato\b"), ("Flipkart", r"\bFlipkart\b"), ("Blinkit", r"\bBlinkit\b"),
    ("ZS Associates", r"\bZS\b|\bZSAssociates\b"), ("Fractal", r"\bFractal\b"), ("HDFC Bank", r"\bHDFC\b"),
    ("HSBC", r"\bHSBC\b"), ("Citi", r"\bCiti\b"), ("Barclays", r"\bBarclays\b"), ("NTT Data", r"\bNTT ?DATA\b"),
    ("Wells Fargo", r"Wells Fargo"), ("Accenture", r"\bAccenture\b"), ("TCS", r"\bTCS\b|Tata Consultancy"),
    ("Infosys", r"\bInfosys\b"), ("Wipro", r"\bWipro\b"), ("Cognizant", r"\bCognizant\b"),
    ("HCLTech", r"\bHCL\b"), ("Persistent", r"Persistent Systems"), ("UST", r"\bUST\b"),
    ("Capgemini", r"\bCapgemini\b"), ("Optum", r"\bOptum\b"), ("PepsiCo", r"\bPepsiCo\b"),
    ("Oracle", r"\bOracle\b"), ("L&T", r"\bL&T\b"), ("Altimetrik", r"\bAltimetrik\b"),
    ("Navya", r"Navya sri"), ("Koantek", r"\bKoantek\b"), ("Prodapt", r"\bProdapt\b"),
    ("Publicis Sapient", r"Publicis Sapient"), ("Tide", r"\bTide\b"), ("Emirates NBD", r"Emirates NBD"),
    ("Vanguard", r"\bVanguard\b"), ("Kyndryl", r"\bKyndryl\b"), ("Alinea", r"Alinea"),
    ("DAZN", r"\bDAZN\b"), ("Hexaware", r"Hexaware"), ("Coforge", r"\bCoforge\b"),
    ("Kimberly Clark", r"Kimberly Clark"), ("Atlas Copco", r"Atlas Copco"), ("Zscaler", r"\bZscaler\b"),
    ("BCG", r"\bBCG\b"), ("Namshi", r"\bNamshi\b"), ("PayU", r"\bPayU\b"), ("Huron", r"\bHuron\b"),
    ("GyanSys", r"\bGyanSys\b"), ("Apexon", r"\bApexon\b"), ("Mattel", r"\bMattel\b"),
    ("Celebal", r"Celebal"), ("NIKE", r"\bNIKE\b"),
]

FIELD_RULES = [
    ("Behavioral", r"tell me about|why do you want|describe a (time|situation|challenging)|how do you (handle|prioriti|manage|communicate)|stakeholder|conflict|deadline|take ownership|production failure you|mistake you"),
    ("System Design", r"system design|design a|design an|architecture|medallion|bronze|scalable|fault.tolerant|end.to.end|lakehouse|multi.tenant|real.time pipeline|data platform"),
    ("DSA", r"\bdsa\b|linked list|binary search|sliding window|two.pointer|lru|anagram|palindrome|heap|time complexit|\bo\(.+\)|merge k sorted|cycle in"),
    ("PySpark", r"pyspark|dataframe|rdd|withcolumn|explode|spark session|spark udf|catalyst|spark (job|ui|shuffle)"),
    ("Spark", r"\bspark\b|sparksql|narrow vs wide|lazy evaluation"),
    ("Databricks", r"databricks|unity catalog|autoloader|auto loader"),
    ("Delta Lake", r"delta lake|delta table|delta live|\bmerge\b.*delta|time travel|z-order"),
    ("Snowflake", r"snowflake|snowpark|qualify"),
    ("Azure", r"\bazure\b|\badf\b|data factory|adls|synapse|event hub|integration runtime"),
    ("AWS", r"\baws\b|\bs3\b|\bglue\b|redshift|lambda|kinesis|emr"),
    ("GCP", r"\bgcp\b|bigquery|dataflow|pub/sub"),
    ("Power BI", r"power ?bi|\bdax\b|\bpibix\b|rls\b"),
    ("Data Modeling", r"star schema|snowflake schema|fact (table|and dimension)|dimension table|olap|oltp|normali[sz]|denormali|data model|grain\b"),
    ("ETL", r"\betl\b|\belt\b|\bcdc\b|incremental (load|data)|watermark|idempotent|data quality"),
    ("Kafka", r"\bkafka\b|kinesis|pub/sub"),
    ("Airflow", r"\bairflow\b|\bdag\b"),
    ("dbt", r"\bdbt\b"),
    ("Machine Learning", r"machine learning|\bml\b|\bllm\b|\brag\b|neural|regression|classif|clustering|overfitting"),
    ("Python", r"\bpython\b|pandas|numpy|decorator|generator|list comprehension|mutable|immutable|\bgil\b"),
    ("SQL", r"\bsql\b|query|table\b|\bselect\b|\bjoin\b|salary"),
]


def detect_field(q: str, post_field: str) -> str:
    for name, pat in FIELD_RULES:
        if re.search(pat, q, re.I):
            return name
    if re.search(r"\bquery\b|\btable\b|salary|\bselect\b", q, re.I):
        return "SQL"
    return post_field or "General"


TOPICS_Q = [
    ("window-functions", r"window function|row_number|dense_rank|\brank\b|lag\b|lead\b|partition by|ntile"),
    ("joins", r"\bjoin\b|inner join|left join|full outer|self join|anti join|cross join|broadcast join|shuffle join"),
    ("aggregations", r"group by|having|aggregat|count\(|sum\(|avg\(|conditional aggregation|pivot"),
    ("cte", r"\bcte\b|common table expression|recursive"),
    ("nulls", r"\bnull\b|coalesce|nvl|isnull|fillna|dropna|missing (values|data|records)"),
    ("dedup", r"duplicat|dedup|dropduplicates"),
    ("topn-ranking", r"second (highest|largest|most)|2nd highest|nth highest|nth (record|salary)|top[- ]?\d|top n\b|highest (salary|paid)|kth"),
    ("consecutive", r"consecutive"),
    ("running-total", r"running total|cumulative|moving average|rolling"),
    ("pyspark", r"pyspark|dataframe|rdd|withcolumn|explode"),
    ("delta-lake", r"delta lake|delta table|time travel|z-order|\boptimize\b|vacuum|merge\b"),
    ("scd", r"\bscd\b|slowly changing"),
    ("streaming", r"streaming|kafka|watermark|exactly-once|real.?time|late.?arriving"),
    ("data-modeling", r"star schema|snowflake schema|fact (table|and)|dimension|olap|oltp|lakehouse|data (warehouse|lake)|schema (evolution|drift)|normali"),
    ("optimization", r"optimi[sz]|performance|slow|query plan|explain|index|shuffle|skew|salting|broadcast|cach|repartition|coalesce|partition|small file"),
    ("etl-cdc", r"\betl\b|\belt\b|\bcdc\b|incremental|idempotent|data quality|audit"),
    ("python", r"python|pandas|numpy|decorator|generator|list comprehension|mutable|immutable"),
    ("dsa", r"linked list|binary search|sliding window|two.pointer|lru|anagram|palindrome|time complexit|heap|\bdsa\b"),
    ("power-bi", r"power ?bi|\bdax\b"),
    ("cloud", r"\bazure\b|\badf\b|data factory|adls|synapse|event hub|\baws\b|\bs3\b|\bglue\b|redshift|lambda|kinesis|\bgcp\b|bigquery|dataflow|pub/sub|snowflake|fabric"),
    ("sql-basics", r"\bwhere\b|\bhaving\b|union|truncate|delete\b|drop\b|primary key|unique|constraint|execution order|isnull"),
]


def detect_topics(q: str) -> list:
    hits = []
    for tag, pat in TOPICS_Q:
        if re.search(pat, q, re.I):
            hits.append(tag)
    if not hits and re.search(r"\bquery\b|\btable\b|salary", q, re.I):
        hits.append("sql-coding")
    return hits[:6]


# ---------- experience ----------

EXP_RE = re.compile(
    r"(?:exp(?:erience)?|yoe)\s*[:=\-–]?\s*(\d{1,2}(?:\.\d)?)(?:\s*(?:[–+\-]|to)\s*(\d{1,2}(?:\.\d)?))?\s*\+?\s*(?:years?|yrs?)",
    re.I,
)
EXP_RE2 = re.compile(r"(\d{1,2})\s*(?:[–+\-]|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)


def exp_bucket(text: str) -> str:
    t = nfkc(text)
    m = EXP_RE.search(t) or EXP_RE2.search(t)
    if not m:
        return "Not specified"
    lo = float(m.group(1))
    if lo < 2:
        return "0–2 yrs"
    if lo < 4:
        return "2–4 yrs"
    if lo < 7:
        return "4–7 yrs"
    return "7+ yrs"


# ---------- main ----------

def main():
    with open(os.path.join(BASE, "data", "posts.json"), encoding="utf-8") as fh:
        posts = json.load(fh)

    raw_items = []
    for p in posts:
        text = p.get("text") or ""
        exp = exp_bucket(text)
        post_company = p.get("company") or "General"
        for q in split_questions(text):
            raw_items.append({
                "key": normalize_key(q),
                "toks": tokens(normalize_key(q)),
                "text": q,
                "post_id": p["id"],
                "post_url": p["post_url"],
                "author": p.get("author") or "Unknown",
                "post_company": post_company,
                "post_field": p.get("field") or "General",
                "exp": exp,
            })

    clusters = dedupe(raw_items)

    questions = []
    for members in clusters:
        members.sort(key=lambda m: -len(m["text"]))
        rep = members[0]
        companies = Counter(m["post_company"] for m in members if m["post_company"] != "General")
        company = companies.most_common(1)[0][0] if companies else "General"
        exps = Counter(m["exp"] for m in members if m["exp"] != "Not specified")
        exp = exps.most_common(1)[0][0] if exps else rep["exp"]
        authors = list(dict.fromkeys(m["author"] for m in members))
        questions.append({
            "id": "q" + rep["post_id"],
            "text": rep["text"],
            "company": company,
            "field": detect_field(rep["text"], rep["post_field"]),
            "topics": detect_topics(rep["text"]),
            "exp": exp,
            "sources": sorted({m["post_id"] for m in members}),
            "authors": authors,
        })

    questions.sort(key=lambda x: x["sources"][0], reverse=True)
    # ensure unique ids (a question may repeat if two clusters share the first source)
    seen = set()
    for i, q in enumerate(questions):
        if q["id"] in seen:
            q["id"] = q["id"] + "x" + str(i)
        seen.add(q["id"])

    with open(os.path.join(BASE, "data", "questions.json"), "w", encoding="utf-8") as fh:
        json.dump(questions, fh, ensure_ascii=False, indent=1)

    print(f"posts: {len(posts)}")
    print(f"raw questions extracted: {len(raw_items)}")
    print(f"unique questions after dedupe: {len(questions)}")
    print("\nfields:", Counter(q['field'] for q in questions).most_common(12))
    print("\ncompanies:", Counter(q['company'] for q in questions).most_common(12))
    print("\nexp:", Counter(q['exp'] for q in questions).most_common())
    print("\ntop topics:", Counter(t for q in questions for t in q['topics']).most_common(15))


if __name__ == "__main__":
    main()
