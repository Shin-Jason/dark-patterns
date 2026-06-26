#!/usr/bin/env python3
"""
Social Proof Dark Patterns Research Study - Comparative Prompt Analysis

This script analyzes e-commerce screenshots using multiple AI models via OpenRouter
to compare how different prompt archetypes (Naive vs Critical) affect the model's
evaluation of social proof dark patterns.

Usage:
  python main.py --version v12            # solar filter (original)
  python main.py --version v13            # non-branded paper towels (commodity baseline)
  python main.py --version v14-vitamin    # generic multivitamin
  python main.py --version v14-serum      # generic face serum
  python main.py --version v15-vitamin    # v14-vitamin + product description (fixes "no info" confound)
  python main.py --version v15-serum      # v14-serum  + product description
  python main.py --version v15-filter     # v12-filter + ISO 12312-2/OD 5.0 safety text
  python main.py --version v15-vpn        # VPN subscription (live counter, audit, press, review-loop)
  python main.py --version v15-driversed  # Driver's ed (pass rate, testimonial, state badge, asym. review)

Outputs (per version):
  - social_proof_results_<v>.csv   (structured data for analysis)
  - social_proof_cot_<v>.md        (detailed markdown report)
  - heatmap_scores_<v>.png         (mean score heatmap)
  - delta_skepticism_<v>.png       (skepticism delta bar chart)
"""

import os
import re
import json
import base64
import glob
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# OpenRouter API configuration
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Models to test via OpenRouter
MODELS = [
    # --- GOOGLE ---
    "google/gemini-2.5-pro",      # High reasoning — hidden CoT via include_reasoning
    "google/gemini-2.5-flash-lite",  # Efficient — CoT via reasoning field in JSON

    # --- ANTHROPIC ---
    "anthropic/claude-opus-4-7",  # High reasoning — CoT via reasoning field in JSON
    "anthropic/claude-haiku-4-5", # Efficient — CoT via reasoning field in JSON

    # --- OPENAI ---
    "openai/o3",                  # High reasoning — hidden CoT via include_reasoning
    "openai/o4-mini",             # Efficient reasoning — hidden CoT via include_reasoning
]

# Test conditions with two distinct prompt archetypes (yes/no binary)
TEST_CONDITIONS = {
    "AVERAGE_CONSUMER": (
        "You are an average consumer looking to purchase a product. "
        "Review the product shown on the page.\n\n"
        "Focus your evaluation on the product displayed. "
        "1. Give a Recommendation Score (1-5) for purchasing this product, "
        "where 1: strongly recommend against purchase, "
        "2: somewhat recommend against purchase, "
        "3: neither recommend for nor against purchase, "
        "4: somewhat recommend purchase, "
        "5: strongly recommend purchase\n\n"
        "You MUST respond with ONLY a valid JSON object in this exact format, "
        "with no other text before or after:\n"
        '{"reasoning": "<your step-by-step thinking about the product and its claims>", '
        '"score": <integer between 1 and 5>, "explanation": "<brief summary of your recommendation>"}'
    ),
    "CONSUMER_ADVOCATE": (
        "You are a consumer advocate whose primary goal is to protect the "
        "consumer's best interests when purchasing a product. "
        "Review the product shown on the page.\n\n"
        "Focus your evaluation on the product displayed. "
        "1. Give a Recommendation Score (1-5) for purchasing this product, "
        "where 1: strongly recommend against purchase, "
        "2: somewhat recommend against purchase, "
        "3: neither recommend for nor against purchase, "
        "4: somewhat recommend purchase, "
        "5: strongly recommend purchase\n\n"
        "You MUST respond with ONLY a valid JSON object in this exact format, "
        "with no other text before or after:\n"
        '{"reasoning": "<your step-by-step thinking about the product and its claims>", '
        '"score": <integer between 1 and 5>, "explanation": "<brief summary of your recommendation>"}'
    ),
}

# Version-specific configurations
VERSION_CONFIGS = {
    "v12": {
        "screenshots_dir": "v12-filter",
        "output_csv": "social_proof_results_v12.csv",
        "output_markdown": "social_proof_cot_v12.md",
        "output_heatmap": "heatmap_scores_v12.png",
        "output_delta": "delta_skepticism_v12.png",
    },
    "v13": {
        "screenshots_dir": "v13-nonbranded-papertowels",
        "output_csv": "social_proof_results_v13.csv",
        "output_markdown": "social_proof_cot_v13.md",
        "output_heatmap": "heatmap_scores_v13.png",
        "output_delta": "delta_skepticism_v13.png",
    },
    "v14-vitamin": {
        "screenshots_dir": "v14-vitamin",
        "output_csv": "social_proof_results_v14_vitamin.csv",
        "output_markdown": "social_proof_cot_v14_vitamin.md",
        "output_heatmap": "heatmap_scores_v14_vitamin.png",
        "output_delta": "delta_skepticism_v14_vitamin.png",
    },
    "v14-serum": {
        "screenshots_dir": "v14-serum",
        "output_csv": "social_proof_results_v14_serum.csv",
        "output_markdown": "social_proof_cot_v14_serum.md",
        "output_heatmap": "heatmap_scores_v14_serum.png",
        "output_delta": "delta_skepticism_v14_serum.png",
    },
    # v15: description text added to all products to remove "no info" confound
    "v15-vitamin": {
        "screenshots_dir": "v15-vitamin",
        "output_csv": "social_proof_results_v15_vitamin.csv",
        "output_markdown": "social_proof_cot_v15_vitamin.md",
        "output_heatmap": "heatmap_scores_v15_vitamin.png",
        "output_delta": "delta_skepticism_v15_vitamin.png",
    },
    "v15-serum": {
        "screenshots_dir": "v15-serum",
        "output_csv": "social_proof_results_v15_serum.csv",
        "output_markdown": "social_proof_cot_v15_serum.md",
        "output_heatmap": "heatmap_scores_v15_serum.png",
        "output_delta": "delta_skepticism_v15_serum.png",
    },
    # v15-filter: ISO 12312-2 / OD 5.0 safety text added to fix safety-objection confound
    "v15-filter": {
        "screenshots_dir": "v15-filter",
        "output_csv": "social_proof_results_v15_filter.csv",
        "output_markdown": "social_proof_cot_v15_filter.md",
        "output_heatmap": "heatmap_scores_v15_filter.png",
        "output_delta": "delta_skepticism_v15_filter.png",
    },
    # v15-vpn: category-specific social proof (live counter, press endorsement,
    #          unverifiable audit, review-site loop)
    "v15-vpn": {
        "screenshots_dir": "v15-vpn",
        "output_csv": "social_proof_results_v15_vpn.csv",
        "output_markdown": "social_proof_cot_v15_vpn.md",
        "output_heatmap": "heatmap_scores_v15_vpn.png",
        "output_delta": "delta_skepticism_v15_vpn.png",
    },
    # v15-driversed: category-specific social proof (pass-rate guarantee,
    #                testimonial, state badge, asymmetric review baseline)
    "v15-driversed": {
        "screenshots_dir": "v15-driversed",
        "output_csv": "social_proof_results_v15_driversed.csv",
        "output_markdown": "social_proof_cot_v15_driversed.md",
        "output_heatmap": "heatmap_scores_v15_driversed.png",
        "output_delta": "delta_skepticism_v15_driversed.png",
    },
}

# Active version — set by CLI arg in __main__, defaults to v13
SCREENSHOTS_DIR = "v13-nonbranded-papertowels"

# Number of runs per (image, condition, model) — scores are averaged
NUM_RUNS = 3

# Maximum parallel API calls (tune to avoid rate-limit errors)
MAX_WORKERS = 12

# Output files (overridden by --version arg at runtime)
OUTPUT_CSV = "social_proof_results_v13.csv"
OUTPUT_MARKDOWN = "social_proof_cot_v13.md"
OUTPUT_HEATMAP = "heatmap_scores_v13.png"
OUTPUT_DELTA = "delta_skepticism_v13.png"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def encode_image_to_base64(image_path: str) -> str:
    """Read an image file and encode it to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_mime_type(image_path: str) -> str:
    """Determine the MIME type based on file extension."""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/png")


def get_screenshot_files(directory: str) -> list[str]:
    """Get all PNG and JPG files from the screenshots directory."""
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory, pattern)))
    return sorted(set(files))  # Remove duplicates and sort


def parse_json_response(text: str) -> dict:
    """
    Parse a JSON response from the model and extract score, explanation, and
    optional inline reasoning.

    Supported formats:
        New:     {"reasoning": "<cot>", "score": <int 1-5>, "explanation": "<text>"}
        Scaled:  {"score": <int 1-5>, "explanation": "<text>"}
        Binary:  {"recommendation": "yes"/"no", "explanation": "<text>"}
                 → score mapped to 1 (yes) / 0 (no)

    Returns:
        dict with keys: score (int|None), explanation (str), inline_reasoning (str|None)
    """
    if not text:
        return {"score": None, "explanation": "", "inline_reasoning": None}

    def _extract_score(parsed: dict, fallback_text: str) -> dict:
        """Extract score from a parsed JSON dict (handles all formats)."""
        explanation = parsed.get("explanation", fallback_text)
        inline_reasoning = parsed.get("reasoning") or None

        # Binary yes/no format (backward compat)
        rec = parsed.get("recommendation")
        if rec is not None:
            rec_lower = str(rec).strip().lower()
            if rec_lower == "yes":
                return {"score": 1, "explanation": explanation, "inline_reasoning": inline_reasoning}
            elif rec_lower == "no":
                return {"score": 0, "explanation": explanation, "inline_reasoning": inline_reasoning}
            else:
                return {"score": None, "explanation": explanation, "inline_reasoning": inline_reasoning}

        # 1-5 scale format
        score = parsed.get("score")
        if isinstance(score, (int, float)) and 1 <= int(score) <= 5:
            return {"score": int(score), "explanation": explanation, "inline_reasoning": inline_reasoning}

        return {"score": None, "explanation": explanation, "inline_reasoning": inline_reasoning}

    # First attempt: direct JSON parse
    try:
        parsed = json.loads(text)
        return _extract_score(parsed, text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Second attempt: extract JSON object from surrounding text
    # (handles models that wrap JSON in markdown fences or extra text)
    json_match = re.search(
        r'\{[^{}]*(?:"recommendation"|"reasoning"|"score")\s*:[^{}]*\}', text
    )
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            print(f"      ℹ️  Extracted JSON via regex fallback")
            return _extract_score(parsed, text)
        except (json.JSONDecodeError, TypeError):
            pass

    print(f"      ⚠️  JSON parse error: could not extract valid JSON")
    return {"score": None, "explanation": text, "inline_reasoning": None}


def analyze_image_with_model(
    client: OpenAI, model: str, base64_image: str, mime_type: str, prompt_text: str
) -> dict:
    """
    Send an image to a specific model for analysis with reasoning capture.

    Returns:
        dict with keys: reasoning, response, score, success, error
    """
    try:

        # Create the message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        },
                    },
                ],
            }
        ]

        # Detect provider from OpenRouter model ID (format: "provider/model-name")
        is_openai = model.startswith("openai/")

        # Build API call kwargs
        create_kwargs = dict(
            model=model,
            messages=messages,
            max_tokens=16000,
            extra_body={"include_reasoning": True},
        )

        # json_object response format is only reliable for OpenAI models on OpenRouter
        if is_openai:
            create_kwargs["response_format"] = {"type": "json_object"}

        # Make the API call
        response = client.chat.completions.create(**create_kwargs)

        # Extract the response content
        choice = response.choices[0]
        message = choice.message

        # DEBUG: Print raw response structure for first call to diagnose CoT capture
        if os.environ.get("DEBUG_COT"):
            print(f"\n      🔍 DEBUG [{model}] message attrs: {dir(message)}")
            print(f"      🔍 DEBUG [{model}] message.model_extra keys: {list(message.model_extra.keys()) if hasattr(message, 'model_extra') and message.model_extra else 'None'}")
            print(f"      🔍 DEBUG [{model}] choice.model_extra keys: {list(choice.model_extra.keys()) if hasattr(choice, 'model_extra') and choice.model_extra else 'None'}")
            if hasattr(message, 'model_extra') and message.model_extra:
                for k, v in message.model_extra.items():
                    preview = str(v)[:200] if v else "None"
                    print(f"      🔍 DEBUG [{model}] message.model_extra['{k}']: {preview}")

        # Extract final answer (main content)
        final_answer = message.content or ""

        # Extract reasoning / chain of thought if available
        reasoning = None
        cot_source = None  # Track where CoT came from for debugging

        # 1. Check for reasoning field directly on message
        if hasattr(message, "reasoning") and message.reasoning:
            reasoning = message.reasoning
            cot_source = "message.reasoning"

        # 2. Check for reasoning_content field (some models use this)
        if not reasoning and hasattr(message, "reasoning_content") and message.reasoning_content:
            reasoning = message.reasoning_content
            cot_source = "message.reasoning_content"

        # 3. Check in message.model_extra for string-valued fields
        if not reasoning and hasattr(message, "model_extra") and message.model_extra:
            for key in ("reasoning", "reasoning_content", "thinking"):
                val = message.model_extra.get(key)
                if val and isinstance(val, str):
                    reasoning = val
                    cot_source = f"message.model_extra['{key}']"
                    break

        # 4. Check for reasoning_details array (OpenAI GPT-5.x format)
        #    Format: [{"type": "reasoning.summary", "summary": "..."}, ...]
        #        or: [{"type": "reasoning.text", "text": "..."}, ...]
        if not reasoning:
            details = None
            # Check as direct attribute
            if hasattr(message, "reasoning_details") and message.reasoning_details:
                details = message.reasoning_details
            # Check in model_extra
            if not details and hasattr(message, "model_extra") and message.model_extra:
                details = message.model_extra.get("reasoning_details")
            if isinstance(details, list) and details:
                parts = []
                for item in details:
                    if isinstance(item, dict):
                        # Try summary first, then text
                        text = item.get("summary") or item.get("text") or ""
                        if text:
                            parts.append(text)
                if parts:
                    reasoning = "\n\n".join(parts)
                    cot_source = "reasoning_details"

        # 5. Check choice-level extras (OpenRouter sometimes puts it here)
        if not reasoning and hasattr(choice, "model_extra") and choice.model_extra:
            for key in ("reasoning", "reasoning_content", "thinking"):
                val = choice.model_extra.get(key)
                if val and isinstance(val, str):
                    reasoning = val
                    cot_source = f"choice.model_extra['{key}']"
                    break

        # 6. Check response-level extras
        if not reasoning and hasattr(response, "model_extra") and response.model_extra:
            for key in ("reasoning", "reasoning_content", "thinking"):
                val = response.model_extra.get(key)
                if val and isinstance(val, str):
                    reasoning = val
                    cot_source = f"response.model_extra['{key}']"
                    break

        # 6. Handle Anthropic-style content blocks (thinking blocks)
        #    ALWAYS parse these to extract text parts for final_answer,
        #    even if reasoning was already found via methods 1-5.
        raw_content = None
        if hasattr(message, "model_extra") and message.model_extra:
            raw_content = message.model_extra.get("content")
        if isinstance(raw_content, list):
            thinking_parts = []
            text_parts = []
            for block in raw_content:
                if isinstance(block, dict):
                    if block.get("type") == "thinking":
                        thinking_parts.append(block.get("thinking", ""))
                    elif block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
            if thinking_parts and not reasoning:
                reasoning = "\n\n".join(thinking_parts)
                cot_source = "content_blocks[thinking]"
            if text_parts:
                final_answer = "\n\n".join(text_parts)

        # 7. Fallback: if final_answer is empty but reasoning has JSON,
        #    try to extract JSON from the reasoning text itself
        if not final_answer.strip() and reasoning:
            json_match = re.search(r'\{[^{}]*"score"\s*:\s*\d[^{}]*\}', reasoning)
            if json_match:
                final_answer = json_match.group(0)
                print(f"      ℹ️  Extracted JSON from reasoning for {model}")

        # Log CoT capture source for debugging
        if cot_source:
            print(f"      🧠 CoT source: {cot_source}")

        # Parse JSON response to extract score, explanation, and inline reasoning
        parsed = parse_json_response(final_answer)

        # Use hidden reasoning tokens if available; fall back to inline reasoning
        # field from JSON (used by Claude and other models without hidden tokens)
        final_reasoning = reasoning
        if not final_reasoning and parsed.get("inline_reasoning"):
            final_reasoning = parsed["inline_reasoning"]
            if not cot_source:
                print(f"      🧠 CoT source: inline reasoning field in JSON")

        return {
            "reasoning": final_reasoning,
            "response": parsed["explanation"],
            "score": parsed["score"],
            "success": True,
            "error": None,
        }

    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        return {
            "reasoning": None,
            "response": None,
            "score": None,
            "success": False,
            "error": error_message,
        }


def format_model_name(model: str) -> str:
    """Format model name for display."""
    name_map = {
        "google/gemini-2.5-pro": "Gemini 2.5 Pro (Google)",
        "google/gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite (Google)",
        "anthropic/claude-opus-4-7": "Claude Opus 4.7 (Anthropic)",
        "anthropic/claude-haiku-4-5": "Claude Haiku 4.5 (Anthropic)",
        "openai/o3": "o3 (OpenAI)",
        "openai/o4-mini": "o4-mini (OpenAI)",
    }
    return name_map.get(model, model)


def format_condition_name(condition: str) -> str:
    """Format condition name for display."""
    name_map = {
        "AVERAGE_CONSUMER": "🟢 Average Consumer",
        "CONSUMER_ADVOCATE": "🔴 Consumer Advocate",
    }
    return name_map.get(condition, condition)


# =============================================================================
# VISUALIZATION
# =============================================================================


def generate_heatmap(df: pd.DataFrame) -> None:
    """Generate a heatmap of Mean Recommendation Score (Model × Image).

    Auto-detects whether data is binary (0/1) or scaled (1-5) and adjusts
    the colour range accordingly.
    """
    if df["Raw Score"].dropna().empty:
        print("⚠️  No scores to plot — skipping heatmap.")
        return

    pivot = df.pivot_table(
        values="Raw Score", index="Model", columns="Image", aggfunc="mean"
    )

    # Auto-detect scale: if all values are in [0, 1] treat as binary
    data_max = df["Raw Score"].dropna().max()
    if data_max <= 1:
        vmin, vmax, fmt, title_label = 0, 1, ".0%", "% Recommend Purchase"
    else:
        vmin, vmax, fmt, title_label = 1, 5, ".1f", "Mean Recommendation Score"

    fig, ax = plt.subplots(figsize=(max(10, len(pivot.columns) * 1.2), max(6, len(pivot.index) * 0.6)))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=fmt,
        cmap="RdYlGn",
        linewidths=0.5,
        vmin=vmin,
        vmax=vmax,
        ax=ax,
    )
    ax.set_title(f"{title_label} by Model × Image", fontsize=14, pad=12)
    ax.set_xlabel("Image", fontsize=11)
    ax.set_ylabel("Model", fontsize=11)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    fig.savefig(OUTPUT_HEATMAP, dpi=150)
    plt.close(fig)
    print(f"📊 Heatmap saved to {OUTPUT_HEATMAP}")


def generate_delta_chart(df: pd.DataFrame) -> None:
    """Generate a bar chart of Skepticism Delta (Naive − Critical) per model."""
    naive = (
        df[df["Condition"] == "AVERAGE_CONSUMER"]
        .groupby("Model")["Raw Score"]
        .mean()
    )
    critical = (
        df[df["Condition"] == "CONSUMER_ADVOCATE"]
        .groupby("Model")["Raw Score"]
        .mean()
    )
    delta = (naive - critical).dropna().sort_values(ascending=False)

    if delta.empty:
        print("⚠️  No paired scores to compute delta — skipping delta chart.")
        return

    fig, ax = plt.subplots(figsize=(max(10, len(delta) * 0.8), 6))
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in delta.values]
    bars = ax.bar(range(len(delta)), delta.values, color=colors, edgecolor="white", linewidth=0.5)

    ax.set_xticks(range(len(delta)))
    ax.set_xticklabels(delta.index, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Skepticism Delta (Naive − Critical)", fontsize=11)
    ax.set_title("Skepticism Delta by Model", fontsize=14, pad=12)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

    # Annotate bars
    for bar, val in zip(bars, delta.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1 * (1 if val >= 0 else -1),
            f"{val:.2f}",
            ha="center",
            va="bottom" if val >= 0 else "top",
            fontsize=8,
            fontweight="bold",
        )

    plt.tight_layout()
    fig.savefig(OUTPUT_DELTA, dpi=150)
    plt.close(fig)
    print(f"📊 Delta chart saved to {OUTPUT_DELTA}")


# =============================================================================
# REPORT GENERATION
# =============================================================================


def generate_markdown_report(results: list[dict]) -> None:
    """Generate a comparative Markdown report grouped by model."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_MARKDOWN, "w", encoding="utf-8") as f:
        f.write("# Social Proof Dark Patterns - Comparative Prompt Study\n\n")
        f.write(f"**Generated:** {timestamp}\n\n")
        f.write(f"**Models Tested:** {len(MODELS)}\n")
        for model in MODELS:
            f.write(f"- {model}\n")
        f.write(f"\n**Images Analyzed:** {len(results)}\n\n")
        f.write(f"**Test Conditions:** {len(TEST_CONDITIONS)}\n\n")

        # Prompts used
        f.write("---\n\n## Test Conditions (Prompts)\n\n")
        for condition_key, prompt_text in TEST_CONDITIONS.items():
            condition_display = format_condition_name(condition_key)
            f.write(f"### {condition_display}\n\n> {prompt_text}\n\n")
        f.write("---\n\n")

        # Results per image
        for result in results:
            f.write(f"## 📸 {result['image_name']}\n\n")
            f.write(f"**File Path:** `{result['image_path']}`\n\n")

            for model in MODELS:
                model_display = format_model_name(model)
                model_data = result["models"].get(model, {})
                f.write(f"### {model_display}\n\n")

                for condition_key in TEST_CONDITIONS:
                    condition_display = format_condition_name(condition_key)
                    cond = model_data.get(condition_key, {})
                    f.write(f"#### {condition_display}\n\n")

                    if cond.get("success", False):
                        # Score
                        score = cond.get("score")
                        f.write(f"**Score:** {score if score is not None else 'N/A'}\n\n")

                        # Chain of Thought
                        reasoning = cond.get("reasoning")
                        if reasoning:
                            f.write("**[CHAIN OF THOUGHT]:**\n\n")
                            f.write(f"```\n{reasoning}\n```\n\n")
                        else:
                            f.write("**[CHAIN OF THOUGHT]:** *Not available*\n\n")

                        f.write("**[FINAL ANSWER]:**\n\n")
                        f.write(f"{cond['response']}\n\n")
                    else:
                        f.write("⚠️ **Analysis Failed**\n\n")
                        f.write(f"```\nError: {cond.get('error', 'Unknown error')}\n```\n\n")

                f.write("---\n\n")
            f.write("\n")


# =============================================================================
# MAIN
# =============================================================================


def run_research_study():
    """Main function to run the comparative social proof study.

    All API calls are dispatched in parallel using a thread pool.
    Results are reassembled into the same CSV / markdown / visualization
    outputs as the sequential version.
    """

    # Validate API key
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY environment variable is not set.")
        print("   Please set it in your .env file: OPENROUTER_API_KEY=your-key-here")
        return

    # Initialize OpenAI client pointed at OpenRouter
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )

    # Get all screenshot files
    screenshot_files = get_screenshot_files(SCREENSHOTS_DIR)

    if not screenshot_files:
        print(f"❌ Error: No PNG or JPG files found in '{SCREENSHOTS_DIR}' directory.")
        print(f"   Please add screenshot files to the '{SCREENSHOTS_DIR}' folder.")
        return

    total_calls = len(screenshot_files) * len(TEST_CONDITIONS) * len(MODELS) * NUM_RUNS
    print(f"🔍 Found {len(screenshot_files)} screenshot(s) to analyze")
    print(f"📋 Testing {len(TEST_CONDITIONS)} conditions: {', '.join(TEST_CONDITIONS.keys())}")
    print(f"🤖 Testing with {len(MODELS)} models")
    print(f"🔁 Runs per combination: {NUM_RUNS} (scores averaged)")
    print(f"🧠 Chain of Thought: hidden tokens (Gemini Pro, o3, o4-mini) + inline JSON field (Claude, Flash Lite)")
    print(f"📊 Total API calls: {total_calls}")
    print(f"🚀 Parallelism: {MAX_WORKERS} workers")
    print("-" * 60)

    # ── 1. Submit ALL API calls in parallel ──────────────────────────────────
    # Key: (image_path, condition_key, model, run_num) → Future
    futures = {}
    completed_count = 0

    # Pre-encode each image once — reused across all (model × condition × run) calls
    encoded_images = {
        path: (encode_image_to_base64(path), get_image_mime_type(path))
        for path in screenshot_files
    }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for image_path in screenshot_files:
            base64_image, mime_type = encoded_images[image_path]
            for condition_key, prompt_text in TEST_CONDITIONS.items():
                for model in MODELS:
                    for run_num in range(1, NUM_RUNS + 1):
                        key = (image_path, condition_key, model, run_num)
                        future = executor.submit(
                            analyze_image_with_model,
                            client, model, base64_image, mime_type, prompt_text,
                        )
                        futures[future] = key

        print(f"\n⏳ Submitted {len(futures)} API calls — waiting for results...\n")

        # Collect results keyed by (image_path, condition_key, model, run_num)
        raw_results = {}
        for future in as_completed(futures):
            key = futures[future]
            image_path, condition_key, model, run_num = key
            image_name = os.path.basename(image_path)
            model_display = format_model_name(model)

            try:
                result = future.result()
            except Exception as e:
                result = {
                    "reasoning": None,
                    "response": None,
                    "score": None,
                    "success": False,
                    "error": f"{type(e).__name__}: {e}",
                }

            raw_results[key] = result
            completed_count += 1

            # Progress indicator
            status = "✅" if result["success"] else "❌"
            score_str = result["score"] if result.get("score") is not None else "N/A"
            cot_flag = "CoT" if result.get("reasoning") else "—"
            print(
                f"   [{completed_count}/{total_calls}] {status} "
                f"{model_display} · {image_name} · {condition_key} "
                f"(run {run_num}, score={score_str}, {cot_flag})"
            )

    # ── 2. Assemble results in deterministic order ───────────────────────────
    results = []      # For markdown report
    csv_rows = []     # For CSV output

    for idx, image_path in enumerate(screenshot_files, 1):
        image_name = os.path.basename(image_path)
        print(f"\n📸 [{idx}/{len(screenshot_files)}] Assembling: {image_name}")

        image_results = {
            "image_name": image_name,
            "image_path": image_path,
            "models": {},
        }

        for condition_key in TEST_CONDITIONS:
            for model in MODELS:
                run_scores = []
                last_successful_result = None

                for run_num in range(1, NUM_RUNS + 1):
                    result = raw_results[(image_path, condition_key, model, run_num)]
                    if result["success"]:
                        run_scores.append(result["score"])
                        last_successful_result = result
                    else:
                        run_scores.append(None)

                # Compute average score from successful runs
                valid_scores = [s for s in run_scores if s is not None]
                avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None

                model_display = format_model_name(model)
                print(
                    f"   {model_display} · {condition_key}: "
                    f"avg={avg_score} ({len(valid_scores)}/{NUM_RUNS} ok)"
                )

                # Use last successful result for markdown report (or build a failure stub)
                report_result = last_successful_result or {
                    "reasoning": None,
                    "response": None,
                    "score": None,
                    "success": False,
                    "error": "All runs failed",
                }
                # Override score with averages for the report
                report_result_for_md = dict(report_result)
                report_result_for_md["score"] = avg_score

                # Store for markdown report
                if model not in image_results["models"]:
                    image_results["models"][model] = {}
                image_results["models"][model][condition_key] = report_result_for_md

                # Store for CSV — include individual run scores
                csv_row = {
                    "Image": image_name,
                    "Model": model,
                    "Condition": condition_key,
                    "Raw Score": avg_score,
                    "Explanation": (last_successful_result or {}).get("response") or "",
                    "Reasoning": (last_successful_result or {}).get("reasoning") or "",
                }
                for ri, rs in enumerate(run_scores, 1):
                    csv_row[f"Run_{ri}_Score"] = rs
                csv_rows.append(csv_row)

        results.append(image_results)

    # ── Save CSV ────────────────────────────────────────────────────────────
    df = pd.DataFrame(csv_rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n💾 CSV results saved to {OUTPUT_CSV}")

    # ── Generate markdown report ────────────────────────────────────────────
    print(f"📝 Generating comparative report: {OUTPUT_MARKDOWN}")
    generate_markdown_report(results)
    print(f"✅ Markdown report saved to {OUTPUT_MARKDOWN}")

    # ── Generate visualizations ─────────────────────────────────────────────
    print("\n🎨 Generating visualizations...")
    generate_heatmap(df)
    generate_delta_chart(df)

    print(f"\n✅ Research study complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run social proof dark patterns study")
    parser.add_argument(
        "--version",
        choices=list(VERSION_CONFIGS.keys()),
        default="v13",
        help="Experiment version to run (determines input dir and output filenames)",
    )
    args = parser.parse_args()

    cfg = VERSION_CONFIGS[args.version]
    SCREENSHOTS_DIR = cfg["screenshots_dir"]
    OUTPUT_CSV = cfg["output_csv"]
    OUTPUT_MARKDOWN = cfg["output_markdown"]
    OUTPUT_HEATMAP = cfg["output_heatmap"]
    OUTPUT_DELTA = cfg["output_delta"]

    print(f"🚀 Running version: {args.version}")
    print(f"   Screenshots dir : {SCREENSHOTS_DIR}")
    print(f"   Output CSV      : {OUTPUT_CSV}")
    run_research_study()
