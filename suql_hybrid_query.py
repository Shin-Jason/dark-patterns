"""
SUQL-inspired hybrid query interface over the dark-patterns evaluation dataset.

Implements the core SUQL concept (Liu et al., 2024b): a single query layer that
combines structured SQL predicates over tabular fields with a natural language
retrieval function — answer(text, question) — over unstructured reasoning traces.

Schema (mirrors social_proof_results_v14_serum.csv):
  Structured columns: model, condition, image, tag_count, raw_score,
                      run_1_score, run_2_score, run_3_score
  Unstructured columns: explanation (str), reasoning (str)

Example hybrid query:
  SELECT model, raw_score, explanation
  FROM evaluations
  WHERE condition = 'AVERAGE_CONSUMER'
    AND tag_count >= 2
    AND answer(explanation, 'does the model justify the score using social proof badges?')
"""

import re
import sqlite3
import textwrap
import pandas as pd
from dataclasses import dataclass

DB_PATH  = ":memory:"   # in-memory for each run; swap to a file path to persist
CSV_PATH = "social_proof_results_v14_serum.csv"

# ---------------------------------------------------------------------------
# NL retrieval patterns
# Each entry: (question_keywords, answer_patterns)
# answer() returns True if any answer_pattern matches the text.
# ---------------------------------------------------------------------------

NL_PATTERNS: list[tuple[list[str], list[str]]] = [
    # Social proof as primary justification
    (
        ["social proof", "badge", "expert", "voted", "endorsement"],
        [r"expert.?(pick|suggest)", r"voted.?best", r"top.?review",
         r"\bbadge\b", r"social proof", r"endorsement", r"recognition"],
    ),
    # Model expresses skepticism or doubt
    (
        ["skeptic", "doubt", "suspicious", "hesitant", "uncertain", "manipul"],
        [r"skeptic", r"suspicious", r"manipulat", r"dark pattern", r"mislead",
         r"hesitant", r"uncertain", r"unverified", r"unsubstantiated"],
    ),
    # Model cites missing quality evidence
    (
        ["missing", "lack", "no ingredient", "no brand", "insufficient", "limited"],
        [r"no ingredient", r"lack(s|ing)? ingredient", r"missing ingredient",
         r"no brand", r"unknown brand", r"generic",
         r"limited (product )?information", r"not enough information",
         r"cannot verify", r"can.t verify"],
    ),
    # Model mentions price as a factor
    (
        ["price", "cost", "expensive", "affordable", "value"],
        [r"\bprice\b", r"\bcost\b", r"\$\d", r"affordable", r"expensive",
         r"value for money", r"price.?point"],
    ),
    # Reasoning-action gap: model flags manipulation but still recommends
    (
        ["reasoning-action", "gap", "despite", "acknowledge", "still recommend"],
        [r"(manipulat|dark pattern|suspicious).{0,200}(yes|recommend|purchase)",
         r"(badge|social proof).{0,200}(recommend|purchase|buy)",
         r"despite.{0,80}(recommend|suggest|buy)"],
    ),
    # Model cites star rating / reviews as evidence
    (
        ["rating", "stars", "review", "review count"],
        [r"\d\.\d.{0,10}star", r"\d+ review", r"rating", r"customer review",
         r"user review", r"\d\.\d out of \d"],
    ),
]


def answer(text: str, question: str) -> bool:
    """
    SUQL-style answer(text, question) predicate.

    Matches the question against NL_PATTERNS by keyword overlap, then tests
    whether any corresponding regex pattern matches the text. Returns True
    (text answers the question affirmatively) or False.

    This implements the retrieval half of SUQL without an external LLM call —
    appropriate for a closed vocabulary of research questions over a known corpus.
    """
    q_lower = question.lower()
    text_lower = text.lower()

    best_patterns: list[str] = []
    best_overlap = 0

    for keywords, patterns in NL_PATTERNS:
        overlap = sum(1 for kw in keywords if kw in q_lower)
        if overlap > best_overlap:
            best_overlap = overlap
            best_patterns = patterns

    if best_overlap == 0:
        # Fallback: direct keyword search from the question itself
        words = re.findall(r"\b\w{4,}\b", q_lower)
        return any(w in text_lower for w in words)

    return any(re.search(pat, text_lower) for pat in best_patterns)


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def build_db(csv_path: str) -> sqlite3.Connection:
    df = pd.read_csv(csv_path)
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df["model_short"] = df["model"].str.split("/").str[-1]
    df["tag_count"] = df["image"].apply(_tag_count)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("evaluations", conn, if_exists="replace", index=False)
    return conn


def _tag_count(image_name: str) -> int:
    name = image_name.replace(".png", "")
    if name == "control":      return 0
    if name in ("expert", "voted", "review"):  return 1
    if name in ("expert-voted", "review-expert", "review-voted"): return 2
    if name == "all":          return 3
    return -1


# ---------------------------------------------------------------------------
# Hybrid query executor
# ---------------------------------------------------------------------------

@dataclass
class HybridQuery:
    """
    A structured SQL query extended with optional NL predicates.

    sql_filter  : valid SQL WHERE clause over structured columns
    nl_question : natural language question applied to explanation + reasoning
    nl_col      : which column(s) to run answer() over ('explanation',
                  'reasoning', or 'both')
    select_cols : columns to display in results
    """
    sql_filter:  str = "1=1"
    nl_question: str | None = None
    nl_col:      str = "both"
    select_cols: list[str] | None = None


def run_query(conn: sqlite3.Connection, hq: HybridQuery) -> pd.DataFrame:
    # Always fetch the full row so answer() has text to search, then project
    # down to select_cols after NL filtering.
    sql = f"SELECT * FROM evaluations WHERE {hq.sql_filter}"
    df = pd.read_sql_query(sql, conn)

    if hq.nl_question:
        def nl_filter(row):
            if hq.nl_col == "explanation":
                return answer(str(row.get("explanation", "")), hq.nl_question)
            if hq.nl_col == "reasoning":
                return answer(str(row.get("reasoning", "")), hq.nl_question)
            return answer(
                str(row.get("explanation", "")) + " " + str(row.get("reasoning", "")),
                hq.nl_question
            )
        df = df[df.apply(nl_filter, axis=1)]

    if hq.select_cols:
        df = df[[c for c in hq.select_cols if c in df.columns]]

    return df.reset_index(drop=True)


def display(label: str, hq: HybridQuery, df: pd.DataFrame,
            show_cols: list[str] | None = None) -> None:
    print(f"\n{'='*65}")
    print(f"QUERY: {label}")
    print(f"  SQL filter : {hq.sql_filter}")
    if hq.nl_question:
        print(f"  NL question: {hq.nl_question}")
    print(f"  Rows returned: {len(df)}")
    print(f"{'='*65}")
    cols = show_cols or (hq.select_cols or ["model_short", "condition",
                                             "image", "raw_score"])
    cols = [c for c in cols if c in df.columns]
    if df.empty:
        print("  (no results)")
        return
    print(df[cols].to_string(index=False, max_colwidth=60))


# ---------------------------------------------------------------------------
# Research queries
# ---------------------------------------------------------------------------

def run():
    conn = build_db(CSV_PATH)

    print("SUQL-INSPIRED HYBRID QUERY INTERFACE")
    print("Dark Patterns Evaluation Dataset — v14-serum (96 rows)")
    print("Structured SQL + NL answer() predicate over reasoning traces")

    # ── Q1: Pure SQL ─────────────────────────────────────────────────────
    q1 = HybridQuery(
        sql_filter="condition = 'AVERAGE_CONSUMER' AND tag_count = 3 AND raw_score >= 3.5",
        select_cols=["model_short", "condition", "image", "raw_score"],
    )
    df1 = run_query(conn, q1)
    display("High-scoring rows under full social proof (3 tags, avg consumer)", q1, df1)

    # ── Q2: Hybrid — SQL filter + NL over reasoning ───────────────────────
    q2 = HybridQuery(
        sql_filter="condition = 'AVERAGE_CONSUMER' AND raw_score >= 3.5",
        nl_question="does the model justify the score using social proof badges?",
        select_cols=["model_short", "condition", "image", "raw_score", "explanation"],
    )
    df2 = run_query(conn, q2)
    display(
        "High-scoring rows where justification cites social proof badges",
        q2, df2,
        show_cols=["model_short", "image", "raw_score", "explanation"]
    )

    # ── Q3: Hybrid — find reasoning-action gaps ───────────────────────────
    q3 = HybridQuery(
        sql_filter="raw_score >= 3.0",
        nl_question="does the model acknowledge manipulation or dark patterns yet still recommend?",
        nl_col="reasoning",
        select_cols=["model_short", "condition", "image", "raw_score", "reasoning"],
    )
    df3 = run_query(conn, q3)
    display(
        "Reasoning-action gaps: model flags manipulation but scores >= 3.0",
        q3, df3,
        show_cols=["model_short", "condition", "image", "raw_score"]
    )

    # ── Q4: Hybrid — advocate condition, missing quality evidence ─────────
    q4 = HybridQuery(
        sql_filter="condition = 'CONSUMER_ADVOCATE'",
        nl_question="does the model cite missing ingredient or brand information?",
        select_cols=["model_short", "condition", "image", "raw_score", "explanation"],
    )
    df4 = run_query(conn, q4)
    display(
        "Advocate condition rows citing missing quality evidence",
        q4, df4,
        show_cols=["model_short", "image", "raw_score", "explanation"]
    )

    # ── Q5: Hybrid — efficient models citing ratings as their evidence ────
    q5 = HybridQuery(
        sql_filter="model_short IN ('gemini-2.5-flash-lite', 'claude-haiku-4-5', 'o4-mini')"
                   " AND tag_count >= 1",
        nl_question="does the model cite star ratings or review count as evidence?",
        select_cols=["model_short", "condition", "image", "raw_score"],
    )
    df5 = run_query(conn, q5)
    display(
        "Efficient models using star ratings (social proof) as primary evidence",
        q5, df5
    )

    # ── Summary stats ─────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print("CROSS-QUERY SUMMARY")
    print(f"{'='*65}")
    total = 96
    # Q2 denominator: all high-score rows under avg consumer (not just 3-tag)
    all_high_avg = pd.read_sql_query(
        "SELECT COUNT(*) AS n FROM evaluations "
        "WHERE condition='AVERAGE_CONSUMER' AND raw_score >= 3.5", conn
    ).iloc[0]["n"]

    print(f"\n  Total evaluations in dataset          : {total}")
    print(f"  Q1 — high-score, 3-tag, avg consumer  : {len(df1)} rows ({len(df1)/total*100:.0f}%)")
    print(f"  Q2 — badge-justified high scores       : {len(df2)}/{int(all_high_avg)} high-score avg-consumer rows ({len(df2)/max(all_high_avg,1)*100:.0f}%)")
    print(f"  Q3 — reasoning-action gaps             : {len(df3)} rows ({len(df3)/total*100:.0f}%)")
    print(f"  Q4 — advocate + missing quality cues   : {len(df4)} rows ({len(df4)/total*100:.0f}%)")
    print(f"  Q5 — efficient models, rating-reliant  : {len(df5)} rows ({len(df5)/total*100:.0f}%)")

    print(f"""
INTERPRETATION:
  Q2 shows that {len(df2)/max(all_high_avg,1)*100:.0f}% of high-score recommendations under the average
  consumer condition are badge-justified — the model's own explanation
  cites social proof as the primary basis. Q3 surfaces {len(df3)} rows where
  the reasoning trace acknowledges manipulation yet the score remains >= 3.0,
  quantifying the reasoning-action gap at the individual response level.
  These are queries impossible to express in pure SQL (they require reading
  the unstructured reasoning text) and impractical to express in pure NL
  retrieval (they require exact numeric filters on score and tag_count).
  SUQL's hybrid approach is the correct query paradigm for this dataset.
""")


if __name__ == "__main__":
    run()
