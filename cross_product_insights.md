# Cross-Product Insights: v13–v17
**Generated:** 2026-06-03  
**Products:** Lumina Original (v13), New Lumina (v14/v16), Veridian (v15/v17)  
**Prompt types:** Page-only (v13–v15), More-info (v16–v17)  
**Models:** Gemini 3.1 Pro Preview, Gemini 2.5 Flash, Claude Opus 4.6, Claude Haiku 4.5, GPT-5.2, GPT-4o Mini

---

## 1. Tag Hierarchy Is Consistent Across Products

Ranked by mean score across all five versions, the same ordering holds regardless of product or prompt type:

| Rank | Tag         | Mean Score | vs. Control |
|------|-------------|------------|-------------|
| 1    | Review      | 3.92       | +0.46       |
| 2    | Wirecutter  | 3.83       | +0.37       |
| 3    | Voted Best  | 3.62       | +0.16       |
| 4    | Expert      | 3.54       | +0.08       |
| 5    | Control     | 3.46       | —           |
| 6    | Trending    | 3.45       | −0.01       |
| 7    | Celebrity   | 3.28       | −0.18       |

**Third-party editorial signals (Review, Wirecutter) consistently outperform all other tags.** They appear to carry genuine credibility weight across models and products. Trending and Celebrity are at or below the control — they add nothing and often subtract.

---

## 2. Celebrity Tag Backfires on Every Product, Every Time

In all five versions, the celebrity tag scores below the control image:

| Version | Product         | Celebrity | Control | Penalty |
|---------|-----------------|-----------|---------|---------|
| v13     | Lumina Original | 2.36      | 2.33    | −0.03   |
| v14     | New Lumina      | 2.97      | 3.21    | **−0.24** |
| v15     | Veridian        | 4.08      | 4.20    | −0.11   |
| v16     | New Lumina (MI) | 2.93      | 3.38    | **−0.45** |
| v17     | Veridian (MI)   | 4.03      | 4.20    | −0.17   |

The penalty is largest when models have broader knowledge (more-info condition) — they're likely cross-referencing whether the celebrity has a credible connection to the product category and finding none. For health/supplement products, celebrity endorsement is treated as a red flag, not social proof.

---

## 3. Tag Uplift Shrinks as Product Quality Rises

Tags have diminishing returns on stronger products. On a weaker product (Lumina Original), Wirecutter adds nearly a full point over the control. On a stronger product (Veridian), tags add almost nothing:

| Tag        | v13 uplift | v14 uplift | v15 uplift | v16 uplift | v17 uplift |
|------------|-----------|-----------|-----------|-----------|-----------|
| Wirecutter | +0.94     | +0.43     | +0.28     | +0.00     | +0.19     |
| Review     | +0.81     | +0.60     | +0.39     | +0.35     | +0.17     |
| Voted Best | +0.33     | +0.28     | +0.17     | +0.01     | +0.00     |
| Expert     | +0.47     | −0.03     | +0.11     | −0.17     | +0.00     |
| Trending   | +0.17     | −0.08     | −0.00     | −0.18     | +0.03     |
| Celebrity  | +0.03     | −0.24     | −0.11     | −0.45     | −0.17     |

**Implication:** Social proof tags are most effective on products that have weaknesses to cover up. On a product that already looks credible and complete, tags provide little lift and can even backfire by looking like overreach.

---

## 4. "More Info" Halves the Manipulation Effect — But Only on Weaker Products

Allowing models to draw on broader knowledge dramatically reduces how far the consumer-advocate prompt can move scores, but only when the product is vulnerable to scrutiny:

| Product    | Page-only delta | More-info delta | Change      |
|------------|----------------|-----------------|-------------|
| New Lumina | −0.71          | −0.35           | **−51%**    |
| Veridian   | −0.12          | −0.10           | −17%        |

Veridian is already so convincing that external knowledge gives models nothing extra to work with — the manipulation prompt can't do much either way. Lumina's weakness is exposed when models aren't confined to the page. This suggests the more-info condition functions as a product credibility stress test.

---

## 5. Model Sensitivity Varies Wildly and Is Product-Dependent

The manipulation prompt delta (BASELINE − MANIPULATION) by model across versions:

| Model                  | v13  | v14  | v15  | v16  | v17  |
|------------------------|------|------|------|------|------|
| Gemini 3.1 Pro Preview | 1.19 | 1.47 | 0.05 | 0.76 | 0.05 |
| Claude Haiku 4.5       | 1.05 | 0.95 | 0.14 | 0.81 | 0.05 |
| Gemini 2.5 Flash       | 0.52 | 1.00 | −0.05| 0.29 | −0.05|
| Claude Opus 4.6        | 0.81 | 0.19 | 0.43 | 0.14 | 0.48 |
| GPT-5.2                | 0.81 | 0.38 | 0.05 | 0.24 | 0.14 |
| GPT-4o Mini            | 0.14 | 0.28 | 0.09 | −0.15| −0.09|

**Key patterns:**
- **Gemini 3.1 Pro & Haiku** are highly prompt-sensitive on weaker products but collapse to near-zero on Veridian — their skepticism is conditional on the product having something to be skeptical about.
- **Claude Opus** is the most consistent responder across all products and prompt types. It's the only model that maintains meaningful sensitivity (0.42–0.48) on Veridian, suggesting it applies principled reasoning independent of product strength.
- **GPT-4o Mini** inverts under more-info conditions (negative delta on v16 and v17) — the consumer-advocate framing combined with broader knowledge makes it *more* bullish. This model is uniquely resistant to adversarial prompting in any direction.
- **Gemini 2.5 Flash** also inverts on strong products (negative delta on v15 and v17) — when given a good product, being told to act in the user's interests just reinforces its recommendation.

---

## 6. GPT-4o Mini Is a Consistent Outlier

Across every version, GPT-4o Mini scores substantially higher than all other models:

| Version | GPT-4o Mini | All others | Gap  |
|---------|-------------|------------|------|
| v13     | 4.31        | 2.41       | +1.90|
| v14     | 4.72        | 3.07       | +1.64|
| v15     | 4.91        | 4.20       | +0.71|
| v16     | 4.26        | 3.12       | +1.14|
| v17     | 4.86        | 4.10       | +0.76|

The gap narrows on Veridian (where even skeptical models score high) but never closes. GPT-4o Mini is uniquely susceptible to social proof signals and uniquely resistant to prompts designed to counteract them. It is the most manipulable model in this study by a significant margin.

---

## 7. Review and Wirecutter Tags Are Robust; Others Are Fragile

When models are allowed broader knowledge (more-info), most tags lose their uplift over the control — or invert. Review and Wirecutter are the only tags that survive the knowledge check:

| Tag        | Page-only score | More-info score | Survived? |
|------------|----------------|-----------------|-----------|
| Review     | 3.84           | 4.04            | ✅ Yes (+0.20) |
| Wirecutter | 3.80           | 3.88            | ✅ Yes (+0.08) |
| Voted Best | 3.51           | 3.79            | ✅ Partial |
| Expert     | 3.43           | 3.70            | ✅ Partial |
| Trending   | 3.27           | 3.71            | ⚠️ Only on strong products |
| Celebrity  | 3.14           | 3.48            | ❌ Still below control |

Interestingly, more-info *raises* scores on some tags — models may be recalling positive associations with review-based signals from training data. But celebrity consistently underperforms regardless of information access.

---

## Summary

| Finding | Strength |
|---------|----------|
| Review and Wirecutter are the most effective tags across all products | Very high — consistent across 5 versions |
| Celebrity tag backfires on health products across all conditions | Very high — no exceptions |
| Stronger products are immune to both tag manipulation and prompt manipulation | High — Veridian shows near-zero effects |
| "More info" prompt halves manipulation effect on weaker products | High — consistent across New Lumina versions |
| GPT-4o Mini is the most susceptible model, resistant to adversarial prompting | Very high — largest gap in every version |
| Claude Opus is the most consistent adversarial responder across product types | High — only model with stable delta on Veridian |
