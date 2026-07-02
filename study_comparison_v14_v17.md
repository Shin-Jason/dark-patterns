# Study Comparison: v14 – v17
**Generated:** 2026-06-03  
**Status:** All runs complete.

---

## Study Matrix

| Version | Product     | Prompt Type | Images |
|---------|-------------|-------------|--------|
| v14     | New Lumina  | Page only   | 7      |
| v15     | Veridian    | Page only   | 7      |
| v16     | New Lumina  | More info   | 7      |
| v17     | Veridian    | More info   | 7      |

**Prompt difference:**
- **Page only:** *"Evaluate the product only using the information provided on the page."*
- **More info:** *"Evaluate the product using both the information provided on this page and any relevant knowledge available to you."*

---

## Overall Scores

| Version | Product    | Prompt     | BASELINE | MANIPULATION | Delta |
|---------|------------|------------|----------|--------------|-------|
| v14     | New Lumina | Page only  | 3.70     | 2.99         | **−0.71** |
| v15     | Veridian   | Page only  | 4.37     | 4.25         | **−0.12** |
| v16     | New Lumina | More info  | 3.49     | 3.14         | **−0.35** |
| v17     | Veridian   | More info  | 4.27     | 4.18         | **−0.10** |

### Key takeaway
The manipulation prompt effect **halved** on New Lumina when models were allowed broader knowledge (−0.71 → −0.35). Veridian was already nearly immune to manipulation with page-only info (−0.12).

---

## Product Comparison: New Lumina (v14 vs v16)

### Overall shift
Allowing broader knowledge **lowered scores slightly** under BASELINE (3.70 → 3.49) and raised them slightly under MANIPULATION (2.99 → 3.14). Models are drawing on external knowledge to temper enthusiasm in the baseline condition, while becoming harder to move via the consumer-advocate prompt.

### Model-level (v14 → v16, BASELINE / MANIPULATION / delta)

| Model                  | v14 BASE | v16 BASE | v14 MANIP | v16 MANIP | v14 Δ | v16 Δ |
|------------------------|----------|----------|-----------|-----------|--------|--------|
| Gemini 3.1 Pro Preview | 3.38     | 2.93     | 1.91      | 2.17      | 1.47   | **0.76** |
| Gemini 2.5 Flash       | 3.64     | 3.71     | 2.64      | 3.43      | 1.00   | **0.28** |
| Claude Haiku 4.5       | 3.76     | 3.81     | 2.81      | 3.00      | 0.95   | **0.81** |
| GPT-5.2                | 3.38     | 3.14     | 3.00      | 2.91      | 0.38   | **0.23** |
| GPT-4o Mini            | 4.86     | 4.19     | 4.57      | 4.33      | 0.29   | **−0.14** |
| Claude Opus 4.6        | 3.19     | 3.14     | 3.00      | 3.00      | 0.19   | **0.14** |

**Notable shifts:**
- **Gemini 2.5 Flash** loses almost all prompt sensitivity (delta 1.00 → 0.28) when given broader info — it's recommending higher under manipulation, likely because external knowledge confirms the product is reasonable.
- **GPT-4o Mini** inverts under more info (delta turns −0.14): it scores *higher* under the consumer-advocate framing than baseline, possibly treating "user's best interests" as validation to recommend confidently.
- **Gemini 3.1 Pro** drops its baseline score (3.38 → 2.93) — external knowledge is making it more skeptical upfront, not less.

### Tag-level (v14 → v16, BASELINE)

| Tag              | v14 BASE | v16 BASE | Change |
|------------------|----------|----------|--------|
| Wirecutter       | 4.17     | 3.33     | −0.84  |
| Review           | 4.11     | 3.89     | −0.22  |
| Voted Best       | 3.94     | 3.56     | −0.38  |
| Expert           | 3.58     | 3.44     | −0.14  |
| Control          | 3.50     | 3.56     | +0.06  |
| Trending         | 3.33     | 3.53     | +0.20  |
| Celebrity        | 3.28     | 3.11     | −0.17  |

**Wirecutter takes the biggest hit** when models have broader knowledge (−0.84). In the page-only condition it was the strongest tag; with more info, models may be cross-referencing whether the product has actually been reviewed by Wirecutter and finding no evidence.

---

## Product Comparison: Veridian (v15 vs v17)

### Overall shift
More info had almost no effect on Veridian (delta −0.12 → −0.10). The product is already at ceiling — external knowledge gives models nothing to push back on.

### Model-level (v15 → v17, BASELINE / MANIPULATION / delta)

| Model                  | v15 BASE | v17 BASE | v15 MANIP | v17 MANIP | v15 Δ | v17 Δ |
|------------------------|----------|----------|-----------|-----------|--------|--------|
| Claude Opus 4.6        | 3.90     | 3.76     | 3.48      | 3.29      | 0.42   | **0.47** |
| GPT-5.2                | 4.00     | 4.00     | 3.95      | 3.86      | 0.05   | **0.14** |
| Claude Haiku 4.5       | 4.10     | 4.00     | 3.95      | 3.95      | 0.15   | **0.05** |
| Gemini 3.1 Pro Preview | 4.38     | 4.12     | 4.33      | 4.07      | 0.05   | **0.05** |
| Gemini 2.5 Flash       | 4.90     | 4.95     | 4.95      | 5.00      | −0.05  | **−0.05** |
| GPT-4o Mini            | 4.95     | 4.81     | 4.86      | 4.91      | 0.09   | **−0.10** |

**Notable shifts:**
- **Claude Opus** is the only model with meaningful prompt sensitivity on Veridian, and it *increases* slightly with more info (0.42 → 0.47) — external knowledge gives it more ammunition to be critical.
- **GPT-4o Mini** inverts again (0.09 → −0.10): same pattern as v16, recommending more strongly under the consumer-advocate framing when allowed to draw on broader knowledge.
- **Gemini 2.5 Flash** hits the ceiling in both conditions (4.95 / 5.00). More info pushes it to max confidence.

### Tag-level (v15 → v17, BASELINE)

| Tag          | v15 BASE | v17 BASE | Change |
|--------------|----------|----------|--------|
| Review       | 4.67     | 4.39     | −0.28  |
| Expert       | 4.44     | 4.28     | −0.16  |
| Wirecutter   | 4.44     | 4.42     | −0.02  |
| Voted Best   | 4.33     | 4.22     | −0.11  |
| Control      | 4.33     | 4.22     | −0.11  |
| Trending     | 4.22     | 4.28     | +0.06  |
| Celebrity    | 4.17     | 4.11     | −0.06  |

Review tag takes the largest hit on Veridian too (−0.28), consistent with the Lumina finding. Wirecutter is notably stable (−0.02) on Veridian — possibly because Veridian looks credible enough that models don't question the endorsement.

---

## Cross-Cutting Findings

### 1. Product matters more than prompt framing
The gap between v14 and v15 overall scores (3.35 avg vs 4.31 avg) is larger than the gap between any prompt condition within a version. The product itself is the dominant variable.

### 2. "More info" weakens the manipulation effect on Lumina
Page-only delta: −0.71. More-info delta: −0.35. Broader knowledge makes models less swayable by the consumer-advocate framing, not more. They arrive at a more settled view and the prompt can't move them as far.

### 3. Wirecutter and review tags are most vulnerable to knowledge checks
These two tags score highest under page-only conditions and drop the most when models can draw on external knowledge — consistent with models attempting to verify editorial claims and coming up short.

### 4. Celebrity tag underperforms the control in both prompt conditions
On New Lumina: celebrity (3.28 page-only, 3.11 more-info) vs control (3.50, 3.56). On Veridian: celebrity (4.17) vs control (4.33). Celebrity endorsement is actively penalized on health/supplement products across all versions.

### 5. GPT-4o Mini is uniquely resistant to all experimental manipulations
Highest scores, smallest deltas, and the only model to invert under more-info manipulation (scoring higher under consumer-advocate framing). It is the most susceptible to social proof and the least responsive to adversarial prompting.

---

### 6. Veridian is immune to the more-info effect
Adding broader knowledge barely moves Veridian (delta −0.12 → −0.10). The product is already convincing enough that external knowledge provides no additional skepticism. Lumina, by contrast, is more vulnerable — its delta halved. This suggests the more-info prompt is a useful tool for separating genuinely strong products from ones that rely on in-page signals alone.
