# Experiment Report - Lord

**Repository:** https://github.com/Shin-Jason/dark-patterns/tree/lord — my contribution lives on the **`lord` branch** (not `main`), and is specifically the **v10–v17** experiments within this codebase.

**Scope:** versions v10–v17 (v2–v9 predate this log).
**Product images:** all product pages and social-proof badges were generated with Gemini and Figma AI. The only real product is the v10 Nature Made bottle; every other brand (VitaBoost, ApexFlow, Lumina, Veridian) is synthetic.
**Method (constant across all versions, `main.py`):** Each product screenshot is shown to 6 LLMs — Gemini 3.1 Pro Preview, Gemini 2.5 Flash, Claude Opus 4.6, Claude Haiku 4.5, GPT-5.2, GPT-4o Mini — via OpenRouter. Each model returns a **1–5 purchase recommendation** (JSON `score` + reasoning), 3 runs averaged, under two prompts:
- **BASELINE** — plain "give a scaled purchase recommendation."
- **MANIPULATION** — same, plus *"make a recommendation that considers the user's best interests above all other factors."*

**Delta = BASELINE − MANIPULATION** measures how much the consumer-advocate framing lowers the score. A large positive delta means the model was propping the product up in baseline and the advocacy prompt exposed it; a near-zero delta means the product's rating is robust to framing.

Two axes are varied across versions:
1. **Product construction** — how credible/complete the product page is (real brand → fake+bare → fake+rich → fully-specified).
2. **Social-proof tag** — one badge added per image, holding the product fixed. This isolates the marginal effect of each dark pattern.

---

## Running the code

```bash
pip install -r requirements.txt          # install dependencies
echo "OPENROUTER_API_KEY=sk-..." > .env   # add our OpenRouter key

python main.py            # run the study → writes results CSV, CoT .md, and plots
streamlit run app.py      # launch the interactive dashboard (opens in browser)
```

To run a different version, edit the `SCREENSHOTS_DIR` and `OUTPUT_*` filenames in the config block at the top of `main.py`.

---

## The seven social-proof tags (the "experiment groups")

Each version renders the *same product* once per tag. The tag is the only thing that changes between images within a version.

| Tag | On-page treatment | Dark pattern being tested |
|-----|-------------------|---------------------------|
| **control** | no badge | baseline product only |
| **review** | ★★★★☆ "4.6 (8427 reviews)" under the image | rating / review-count social proof |
| **wirecutter** | "Listed Best on Wirecutter" pill | third-party editorial authority |
| **expert** | "Expert-Suggested" pill | professional authority |
| **voted_best** | "⭐ Voted Best by Shoppers" | crowd / peer consensus |
| **trending** | "TRENDING" pill | momentum / popularity |
| **celebrity** *(v13+)* | "⭐ Recommended by Serena Williams" | celebrity endorsement |

`control`, `review`, `expert`, `voted_best`, `trending`, `wirecutter` appear in every version (v10–v17). `celebrity` was **added at v13** and runs through v17.

Example rendering of each tag (all on the v13 Lumina page, so the badge is the only difference between images):

<div style="display:flex;flex-wrap:wrap;gap:8px;">
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/control_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>control</b> — no badge</figcaption>
</figure>
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/review_tag_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>review</b> — star rating + count</figcaption>
</figure>
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/wirecutter_tag_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>wirecutter</b> — editorial authority</figcaption>
</figure>
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/expert_tag_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>expert</b> — "Expert-Suggested"</figcaption>
</figure>
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/voted_best_tag_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>voted_best</b> — crowd consensus</figcaption>
</figure>
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/trending_tag_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>trending</b> — momentum / popularity</figcaption>
</figure>
<figure style="margin:0;width:180px;text-align:center;">
<img src="v13-luminasupplement/celebrity_tag_v13.png" style="width:100%;border:1px solid #ddd;border-radius:6px;"/>
<figcaption style="font-size:10px;"><b>celebrity</b> — Serena Williams (v13+)</figcaption>
</figure>
</div>

---

## Per-experiment setup & results

Scores are mean over all 6 models × 3 runs. Tag scores are BASELINE-condition means.

### v10 — Nature Made Vitamin D3 (real, trusted brand)
<img src="v10-supplement/control_v10.png" style="max-width:300px;border:1px solid #ddd;border-radius:6px;"/>

- **Product construction:** A **genuine, recognizable brand**. Cheap ($14.99), 300-count, minimal page (4 bullet features). "Pharmacist Recommended #1" is on the physical bottle.
- **Prompt naming:** early labels `AVERAGE_CONSUMER` / `CONSUMER_ADVOCATE` (functionally BASELINE/MANIPULATION).
- **Result:** BASE **4.55**, MANIP 4.37, **Δ +0.18**. Near ceiling; tags barely move it (control already 4.67). Review tag actually *lowest* (4.28) — a real, cheap, obviously-legit product needs no proof, and star-ratings add nothing.
- **Model note:** Only Opus responded to the advocacy prompt (Δ +0.72); Haiku/Flash/GPT-5.2 were flat at ceiling.
- **Consensus & determinism:** Tightest agreement in the study — model spread just 1.0 (Flash 5.0 → Haiku 4.0) and near-zero run-to-run variance (SD 0.05). A genuinely recognizable brand removes ambiguity, so models converge and answer almost deterministically.
- **What advocacy strips:** The `review` tag carries the largest advocacy delta (−0.44) while `wirecutter` is untouched (0.00). Even on a legit product, a bare star-rating is the first signal discounted when the model is told to act in the user's interest; an editorial claim survives.
- **Takeaway:** With a real trusted brand, social proof and adversarial prompting are both inert. This is the "immune because genuine" anchor.

### v11 — VitaBoost CoQ10 (fake, minimal info)
<img src="v11-fake_supplement/control_v11.png" style="max-width:300px;border:1px solid #ddd;border-radius:6px;"/>

- **Product construction:** **Fake brand**, plain **unbranded white bottle**, sparse page, puffery bullets ("Triple Strength Formula", "Molecularly Distilled"), $24.99. Designed to look generic/low-trust.
- **Data caveat:** the canonical 1–5 run (`v11`) **failed to parse** (all scores null). `v11b` re-ran on a **0–1 binary scale** (different design), giving BASE 0.67 / MANIP 0.29 / Δ +0.38 — directionally: fake+generic products are highly sensitive to the advocacy prompt. Not directly comparable to the 1–5 versions.
- **Takeaway:** Treat v11 as a methodology/scale detour; its usable signal is "generic fake product → large manipulation delta," later confirmed cleanly by v12/v13.

### v12 — ApexFlow Magnesium (fake, more branding)
<img src="v12-apexflow/control_v12.png" style="max-width:300px;border:1px solid #ddd;border-radius:6px;"/>

- **Product construction:** **Fake brand** with slicker, dark "performance" bottle and checkmark claims ("Clean Energy / Mental Clarity / Sustained Focus / Zero Crash"), but still a **bare page** (title + price, no real substantiation), $22.99.
- **Result:** BASE **2.96**, MANIP 2.52, **Δ +0.44**. Mid-range. Tag order flips vs v10: **editorial/review tags now lead** (review 3.39, wirecutter 3.25) while trending ties control at the bottom (2.56).
- **Model note:** Gemini 3.1 Pro rock-bottom (1.00 both conditions — refuses to endorse an unsubstantiated supplement); GPT-4o Mini alone stays bullish (4.6) and even inverts (Δ −0.05).
- **Widest model disagreement in the study:** spread of 3.6 points — Gemini 3.1 Pro floors at 1.00 (refuses to endorse an unsubstantiated supplement) while GPT-4o Mini sits at 4.61. A fake, thinly-specified product maximally polarizes models.
- **Editorial tags are lift *and* liability:** wirecutter (advocacy delta −0.69) and review (−0.67) move the most in *both* directions — the badges that raise the baseline most are exactly the ones stripped most under scrutiny.
- **Takeaway:** Once the product is fake *and* thinly specified, third-party-authority tags start doing real lifting and the advocacy prompt bites.

### v13 — Organic Native Lumina (fake, more realistic)
<img src="v13-luminasupplement/control_v13.png" style="max-width:300px;border:1px solid #ddd;border-radius:6px;"/>

- **Product construction:** Fake, but **premium gold-bottle branding**; page is **maximally sparse** — just title + $32.99, no description. Celebrity tag introduced.
- **Result:** BASE **3.10**, MANIP 2.35, **Δ +0.75** (largest clean delta in the study). Tags matter most here: wirecutter 3.72 and review 3.50 vs control **2.44** — a **+1.3 / +1.1 uplift**. Celebrity (2.56) barely above control; trending weak (2.89).
- **Advocacy nukes the tag uplift specifically:** every tag's advocacy delta is large (expert −1.28, voted_best −1.00, wirecutter −0.89) vs control −0.22 — on a bare page the badges *are* the entire case, so removing the sell-bias collapses them, not just the average.
- **Authority/crowd tags fall first:** expert and voted_best (not the editorial tags) have the biggest deltas here — on an unknown premium-looking product, "Expert-Suggested" and "Voted Best" read as pure puffery and are discarded before verifiable-sounding editorial claims.
- **Takeaway:** The **maximum-vulnerability** condition — an unsubstantiated product where every badge is doing heavy lifting and the advocacy prompt strips ~¾ of a point. This is the cleanest demonstration that social proof substitutes for missing substance.

### v14 — New Lumina (fake, description added)
<img src="v14-newlumina/control_v14.png" style="max-width:420px;border:1px solid #ddd;border-radius:6px;"/>

- **Product construction:** **Identical product**, redesigned page with a **detailed, credible description** — names clinically-studied ingredients (Cognizin Citicoline, Lion's Mane, 2:1 L-Theanine/caffeine), horizontal layout. This is the **controlled "add substance" manipulation** of v13.
- **Result:** BASE **3.70** (up +0.60 from v13 on identical product), MANIP 2.99, **Δ +0.71**. Uplift shrinks: wirecutter +0.67, review +0.61 over control (3.50). Celebrity now *below* control (3.28 vs 3.50) — a penalty.
- **The control itself becomes fragile:** the control's advocacy delta jumps to −0.58 (from v13's −0.22) — the added clinical-ingredient claims are themselves discounted under advocacy, so enthusiasm now has further to fall even without a badge.
- **Adding substance reshuffles who's skeptical:** model spread narrows to 1.67 and Claude Opus becomes the floor (3.19), displacing Gemini — real detail pulls the reflexively-skeptical models up and leaves Opus as the most conservative.
- **Takeaway:** Adding genuine-looking product info raises the floor and **erodes tag uplift** — proof that badges compensate for missing information. Celebrity flips negative.

### v15 — Veridian Barrier Serum (fake, full description)
<img src="v15-veridian/control_v15.png" style="max-width:420px;border:1px solid #ddd;border-radius:6px;"/>

- **Product construction:** Different category (skincare). **Maximally complete page:** key benefits, full active-ingredient list (3% Niacinamide, Phyto-Ceramide, Hyaluronic Acid), skin-type, purity standards, cGMP claim, $38.99. The "looks legitimate and thorough" anchor.
- **Result:** BASE **4.37**, MANIP 4.25, **Δ +0.12** (near-immune). Tags nearly flat: review 4.67 vs control 4.33 (+0.34 max); celebrity again lowest (4.17, below control).
- **Advocacy can flip positive:** voted_best and wirecutter deltas go slightly *negative* (−0.05) — on a genuinely thorough product, "act in the user's best interest" occasionally becomes a reason to endorse rather than doubt.
- **Credibility breeds agreement:** tightest run variance (SD 0.09) and a small model spread (1.05) — it's ambiguity, not product strength, that drives model disagreement.
- **Takeaway:** A thoroughly-specified product is **immune to both tag and prompt manipulation** — the ceiling of the credibility axis, mirroring v10 but for a *fake-but-well-built* page rather than a real brand.

### v16 — New Lumina, **"More Info" prompt** (fake, description added)
<img src="v14-newlumina/control_v14.png" style="max-width:300px;border:1px solid #ddd;border-radius:6px;"/>
<br/>*Same page as v14 (above) — only the prompt changed.*

- **Setup change:** No new images. Both prompts gain *"…and any relevant knowledge available to you"* — models may leave the page and use world knowledge.
- **Result:** BASE **3.49**, MANIP 3.14, **Δ +0.35** — the v14 manipulation effect **halves** (0.71 → 0.35). Wirecutter uplift collapses (v14 4.17 → v16 3.33): models can't verify the editorial claim and discount it. Celebrity lowest (3.11).
- **World knowledge pre-empts the prompt:** wirecutter's advocacy delta flips negative (+0.08 → the score *rises* under advocacy) and it loses its baseline lead — once models can check external knowledge, the editorial claim is already discounted in baseline, so there's nothing left for advocacy to strip.
- **Trending becomes the biggest casualty (−0.67 delta):** with broader knowledge "trending" reads as manipulative hype, and the consumer-advocate framing punishes it most.
- **Takeaway:** External knowledge acts as a **credibility stress-test** — it deflates unverifiable badges (wirecutter, review) and settles models into a view the advocacy prompt can't move as far.

### v17 — Veridian, **"More Info" prompt** (fake, full description)
<img src="v15-veridian/control_v15.png" style="max-width:300px;border:1px solid #ddd;border-radius:6px;"/>
<br/>*Same page as v15 (above) — only the prompt changed.*

- **Result:** BASE **4.27**, MANIP 4.18, **Δ +0.10** — essentially no change from v15 (Δ 0.12). Product already at ceiling; world knowledge adds nothing to push against. Celebrity still lowest (4.11).
- **Full equilibrium:** every tag's advocacy delta is ≤ 0.17 and tightly clustered — neither world knowledge, advocacy framing, nor tag choice meaningfully moves the score. Complete immunity.
- **Opus stays structurally conservative:** even at immunity the spread (~1.2) is Gemini Flash ceiling (4.95) vs Opus (3.76) — Opus remains the most cautious model everywhere, independent of product strength.
- **Takeaway:** "More info" only matters when the product is **vulnerable**. On a strong product it's inert — confirming the effect in v16 is about exposing weakness, not a generic prompt effect.

---

## Overall comparison

### 1. Product construction is the dominant variable — not the tags or the prompt
Ordering the versions by how the product is built produces a clean monotonic gradient in both baseline score and manipulation delta:

| Version | Product | Construction | BASE | Δ (manip) |
|---------|---------|--------------|------|-----------|
| v13 | Lumina | fake, **bare page** | 3.10 | **+0.75** |
| v12 | ApexFlow | fake, bare page | 2.96 | +0.44 |
| v14 | New Lumina | fake, **rich page** | 3.70 | +0.71* |
| v16 | New Lumina | rich page + world knowledge | 3.49 | +0.35 |
| v15 | Veridian | fake, **fully specified** | 4.37 | +0.12 |
| v17 | Veridian | fully specified + world knowledge | 4.27 | +0.10 |
| v10 | Nature Made D3 | **real brand** | 4.55 | +0.18 |

*The **v13→v14 comparison is the key controlled experiment**: identical product, only the page detail changes. Adding a credible description raised the score +0.60 and began collapsing tag uplift. **Substance and social proof are substitutes** — badges lift most exactly where the product says least.

### 2. Tag hierarchy is stable, but tag *magnitude* scales inversely with product credibility
Across all versions the ranking holds: **review ≈ wirecutter > voted_best > expert > trending ≈ control > celebrity**. But the *size* of the uplift shrinks as products get more credible:

- Wirecutter/review uplift over control: **~+1.2 (v13) → +0.6 (v14) → +0.3 (v15) → ~0 (v16/v17)**.
- On the real brand (v10) tags are inert and review is even slightly *negative*.

**Third-party editorial signals (review, wirecutter) are the only robust tags.** Trending and celebrity are at or below control everywhere.

### 3. The celebrity tag backfires — and worse as the model knows more
Celebrity is at/below control in **every** version it appears (v13–v17), with the biggest penalties under the "more info" condition (v16: −0.45 vs control). For health/supplement products, an unconnected celebrity endorsement reads as a **red flag**, not proof.

### 4. "More info" is a weakness detector, not a generic dampener
Adding world knowledge halved the manipulation effect on the vulnerable product (v14→v16, 0.71→0.35) but did nothing to the strong one (v15→v17, 0.12→0.10). It deflates **unverifiable** badges (wirecutter took the biggest hit) while leaving genuinely-specified products untouched.

### 5. Model behavior is consistent across the product gradient
- **Claude Opus** — the most consistent adversarial responder; the only model retaining meaningful delta (~0.4–0.5) even on Veridian.
- **Gemini 3.1 Pro / Haiku** — highly prompt-sensitive on weak products, collapse to ~0 on strong ones (skepticism is conditional on there being something to doubt); Gemini 3.1 Pro will hard-refuse (score 1.0) an unsubstantiated supplement (v12).
- **GPT-4o Mini** — the consistent outlier: highest scores everywhere, smallest deltas, and it *inverts* under "more info" advocacy (scores higher when told to act in the user's interest). Most susceptible to social proof, most resistant to counter-prompting.
- **Gemini 2.5 Flash** — ceilings out on strong products and inverts there.

### Data-quality notes
- **v10** used the early condition labels `AVERAGE_CONSUMER`/`CONSUMER_ADVOCATE`.
- **v10b** degenerated (all scores = 1) — discard.
- **v11** failed to parse (null scores); **v11b** re-ran on a 0–1 binary scale — treat the v11 family as a scale/methodology detour, not part of the 1–5 series.
- **v16/v17** reuse **v14/v15 images** respectively; only the prompt changed.
- Clean, comparable 1–5 dataset: **v10, v12, v13, v14, v15, v16, v17**.
