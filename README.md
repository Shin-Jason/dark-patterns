# Dark Patterns in AI Shopping Agents

**Social Proof Susceptibility, Constraint Verification, and Knowledge Grounding**

Author: Jason Shin · Stanford (CS224V) · Advised in the Stanford HAI ecosystem

As frontier models are embedded in e-commerce workflows, are they susceptible to the
same *dark patterns* that manipulate human consumers? This project measures whether
**social-proof tags** — labels like *Expert-Suggested*, *Voted Best by Shoppers*, and
*Review Highlights* — inflate an AI shopping agent's recommendation score **independent
of objective product quality**, and builds a verification layer to tell evidence-grounded
recommendations apart from badge-driven ones.

## Research questions
1. Do social-proof tags raise recommendation scores independently of product quality?
2. Does a consumer-advocate framing reduce susceptibility?
3. Can formal constraint checking flag *unjustified* recommendations that cite badges instead of evidence?
4. Does the effect generalize across product categories?

## Method
- **Controlled dose-response design:** 8 screenshots per product, varying only the number
  of social-proof overlays (0–3 tags), holding the product constant.
- **6 frontier vision-language models across 3 providers**, temperature 0, multiple runs per cell.
- **288+ structured evaluations**, iterated across versions v10–v15 (face serum, multivitamin,
  solar filter, paper towels, VPN, driver's-ed) to test generalization.

## Key finding
Social-proof badges measurably inflate recommendation scores beyond objective merit, and
**ungrounded models cited no objective evidence in 84% of high-confidence recommendations** —
quantifying a concrete consumer-harm / market-distortion risk as AI mediates commerce. More
capable models respond *more* strongly to the corrective consumer-advocate framing.

## Verification layer
| Component | File | What it does |
|---|---|---|
| SMT constraint checker | `z3_constraint_analysis.py` | Z3-based quality–evidence constraints that flag recommendations unsupported by independent signals |
| Hybrid query interface | `suql_hybrid_query.py` | SUQL-style queries over reasoning traces (SQL predicates + an `answer()` NL predicate) to surface reasoning–action gaps |
| Knowledge grounding | `kg_sparql_grounding.py` | SPARQL/Wikidata retrieval of ingredient evidence (CAS numbers, biological roles) the model *should* have cited |

## Repo structure
- `main.py` — evaluation runner (queries models via the OpenRouter API)
- `app.py` — Streamlit viewer for results
- `generate_plots.py` — dose-response, heatmap, and skepticism-delta figures
- `social_proof_results_v*.csv`, `social_proof_cot_v*.md` — raw scores and chain-of-thought per version
- `v*-*/` — screenshot image sets per experimental version
- `final_report.pdf` — full technical report (intro, lit review, methods, results)

## Running it
```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY="your-key-here"   # or put it in a .env file (git-ignored)
python main.py            # run evaluations
streamlit run app.py      # browse results
```

## Report
See **`final_report.pdf`** for the full writeup. A peer-reviewed paper is in preparation.
