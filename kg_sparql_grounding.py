"""
Knowledge Graph grounding via Wikidata SPARQL.

Demonstrates what independent quality evidence a KG-grounded shopping agent
would have access to for face serum ingredients — the structured data that
Z3 constraint analysis showed is absent from 84% of high-score recommendations
in the v14-serum dataset.

Queries Wikidata for each ingredient's:
  - CAS registry number (chemical identity verification)
  - Safety classification (GHS hazard statements)
  - Biological roles / use cases
  - LD50 / toxicity data where available
  - Regulatory status

Then shows how this structured KG evidence maps onto the Z3 quality-evidence
constraint: a recommendation is formally justified when the agent can retrieve
at least one verified quality signal from the KG.
"""

import time
import requests
import pandas as pd
from z3 import Bool, Implies, Solver, sat

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "DarkPatternResearch/1.0 (jasonshin711@gmail.com)"}

# Face serum ingredients with known Wikidata QIDs
SERUM_INGREDIENTS = {
    "Hyaluronic Acid": "Q3143635",
    "Niacinamide":     "Q192423",
    "Retinol":         "Q424976",
    "Glycerin":        "Q132501",
    "Vitamin C":       "Q199678",
    "Ceramide":        "Q424213",
}

SPARQL_TEMPLATE = """
SELECT DISTINCT
  ?casNumber
  ?ghsLabel
  ?bioRoleLabel
  ?medicalUseLabel
  ?safetyClass
WHERE {{
  BIND(wd:{qid} AS ?compound)

  OPTIONAL {{ ?compound wdt:P231 ?casNumber. }}
  OPTIONAL {{ ?compound wdt:P4952 ?ghs.
             ?ghs rdfs:label ?ghsLabel. FILTER(LANG(?ghsLabel)="en") }}
  OPTIONAL {{ ?compound wdt:P4954 ?bioRole.
             ?bioRole rdfs:label ?bioRoleLabel. FILTER(LANG(?bioRoleLabel)="en") }}
  OPTIONAL {{ ?compound wdt:P2175 ?medicalUse.
             ?medicalUse rdfs:label ?medicalUseLabel. FILTER(LANG(?medicalUseLabel)="en") }}
  OPTIONAL {{ ?compound wdt:P3071 ?safetyClass. }}
}}
LIMIT 10
"""


def sparql_query(qid: str) -> list[dict]:
    query = SPARQL_TEMPLATE.format(qid=qid)
    r = requests.get(
        WIKIDATA_SPARQL,
        params={"query": query, "format": "json"},
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


def extract_kg_evidence(bindings: list[dict]) -> dict:
    """Flatten SPARQL bindings into a structured evidence dict."""
    evidence = {
        "cas_number": None,
        "ghs_classifications": [],
        "biological_roles": [],
        "medical_uses": [],
        "safety_class": None,
    }
    for row in bindings:
        if "casNumber" in row and not evidence["cas_number"]:
            evidence["cas_number"] = row["casNumber"]["value"]
        if "ghsLabel" in row:
            val = row["ghsLabel"]["value"]
            if val not in evidence["ghs_classifications"]:
                evidence["ghs_classifications"].append(val)
        if "bioRoleLabel" in row:
            val = row["bioRoleLabel"]["value"]
            if val not in evidence["biological_roles"]:
                evidence["biological_roles"].append(val)
        if "medicalUseLabel" in row:
            val = row["medicalUseLabel"]["value"]
            if val not in evidence["medical_uses"]:
                evidence["medical_uses"].append(val)
        if "safetyClass" in row and not evidence["safety_class"]:
            evidence["safety_class"] = row["safetyClass"]["value"]
    return evidence


def check_kg_constraint(evidence: dict) -> bool:
    """
    Z3 constraint: a high recommendation is formally justified when the KG
    provides at least one of: verified chemical identity (CAS), biological
    role, or medical use — independent of any social proof signal.

    This mirrors the constraint in z3_constraint_analysis.py but now the
    quality evidence comes from a structured KG rather than the model's
    unverified reasoning.
    """
    has_cas      = Bool("has_cas_number")
    has_bio_role = Bool("has_biological_role")
    has_med_use  = Bool("has_medical_use")
    justified    = Bool("recommendation_justified")

    s = Solver()
    # Justified iff at least one KG quality signal is present
    s.add(justified == (has_cas | has_bio_role | has_med_use))
    s.add(has_cas      == bool(evidence["cas_number"]))
    s.add(has_bio_role == bool(evidence["biological_roles"]))
    s.add(has_med_use  == bool(evidence["medical_uses"]))

    s.check()
    m = s.model()
    return bool(m[justified])


def run():
    print("=" * 65)
    print("KG GROUNDING: Wikidata SPARQL for Face Serum Ingredients")
    print("=" * 65)
    print(f"\nQuerying {len(SERUM_INGREDIENTS)} ingredients from Wikidata...\n")

    rows = []
    for name, qid in SERUM_INGREDIENTS.items():
        bindings = sparql_query(qid)
        evidence = extract_kg_evidence(bindings)
        justified = check_kg_constraint(evidence)
        rows.append({"ingredient": name, "qid": qid, **evidence,
                     "kg_justified": justified})
        print(f"  {name} ({qid})")
        print(f"    CAS number:        {evidence['cas_number'] or '—'}")
        print(f"    Biological roles:  {', '.join(evidence['biological_roles'][:3]) or '—'}")
        print(f"    Medical uses:      {', '.join(evidence['medical_uses'][:3]) or '—'}")
        print(f"    GHS safety:        {', '.join(evidence['ghs_classifications'][:2]) or '—'}")
        print(f"    KG constraint satisfied: {justified}")
        print()
        time.sleep(0.5)  # be polite to Wikidata

    df = pd.DataFrame(rows)

    print("=" * 65)
    print("CONSTRAINT SUMMARY")
    print("=" * 65)
    n_justified = df["kg_justified"].sum()
    print(f"\nIngredients with KG-verified quality evidence: {n_justified}/{len(df)}")
    print(f"({n_justified/len(df)*100:.0f}% of common serum ingredients are formally "
          f"justifiable via Wikidata KG)\n")

    print("CONTRAST WITH UNGROUNDED LLM RECOMMENDATIONS (v14-serum):")
    print("  - 84% of high-score recommendations under AVERAGE_CONSUMER")
    print("    violated the quality-evidence constraint (Z3 analysis).")
    print("  - Those models cited star ratings and social proof badges,")
    print("    not verified ingredient data like the above.")
    print("  - A KG-grounded agent querying Wikidata before recommending")
    print("    would have structured chemical identity, biological role,")
    print("    and safety classification data available — the exact")
    print("    independent quality evidence the constraint requires.\n")

    has_cas  = df["cas_number"].notna().sum()
    has_role = df["biological_roles"].apply(bool).sum()
    has_use  = df["medical_uses"].apply(bool).sum()
    print(f"KG evidence retrieved:")
    print(f"  CAS registry numbers:   {has_cas}/{len(df)} ingredients")
    print(f"  Biological roles:       {has_role}/{len(df)} ingredients")
    print(f"  Medical uses:           {has_use}/{len(df)} ingredients")

    df_out = df.copy()
    df_out["biological_roles"] = df_out["biological_roles"].apply(lambda x: "; ".join(x))
    df_out["medical_uses"]     = df_out["medical_uses"].apply(lambda x: "; ".join(x))
    df_out["ghs_classifications"] = df_out["ghs_classifications"].apply(lambda x: "; ".join(x))
    df_out.to_csv("kg_ingredient_evidence.csv", index=False)
    print("\nFull KG evidence saved to kg_ingredient_evidence.csv")


if __name__ == "__main__":
    run()
