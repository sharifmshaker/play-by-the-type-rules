"""
costs.py — convert SemBench's raw token/latency logs into dollar costs.

WHY THIS EXISTS
---------------
The SemBench harness (eval_blendsql.py) logs only raw counts per query:
    input_tokens, output_tokens, num_generation_calls, latency (wall-clock s),
    gpu_usage.
It does NOT compute a dollar cost. This module adds that, for both regimes:

  * API models (Gemini)  -> token-based cost = tokens x per-token price.
  * Local models (Gemma) -> time-based cost = gpu_hours x hourly rental rate.

All prices are USD per 1,000,000 tokens, sync/standard tier, mid-2026.
Batch API halves both input and output (set batch=True).

CAVEATS (read before trusting a number):
  * Gemini 3.x Flash/Pro bill THINKING tokens at the output rate. The
    completion_tokens SemBench logs already include them IF the API returns
    them in usage; if you disable thinking (thinking_level=low / Flash-Lite),
    output counts and cost drop. Verify against your own billing dashboard.
  * SemBench logs a single input_tokens figure and does NOT separate audio
    input tokens (billed higher). For audio-heavy scenarios (cars, wildlife)
    pass audio_fraction>0 to approximate, or treat the number as a floor.
  * Gemini >200K-context tier pricing only applies to Pro; ignored for Flash*.
"""
from __future__ import annotations
from dataclasses import dataclass

# ---- Price table: USD per 1e6 tokens, sync standard tier -------------------
# Sources: ai.google.dev/gemini-api/docs/pricing (checked 2026-07). Audio-input
# rates flagged where uncertain. Update these as Google revises pricing.
PRICING = {
    "gemini-3.1-flash-lite":   {"in": 0.25, "in_audio": 0.50, "out": 1.50},
    "gemini-3-flash-preview":  {"in": 0.50, "in_audio": 1.00, "out": 3.00},   # audio rate approx
    "gemini-3.5-flash":        {"in": 1.50, "in_audio": 1.50, "out": 9.00},   # audio rate approx
    "gemini-3.1-pro-preview":  {"in": 2.00, "in_audio": 2.00, "out": 12.00},  # >200k: 4.00/18.00 (not modeled)
    # paper baseline, kept for apples-to-apples with the published result:
    "gemini-2.5-flash":        {"in": 0.30, "in_audio": 1.00, "out": 2.50},
    "gemini-2.5-flash-lite":   {"in": 0.10, "in_audio": 0.30, "out": 0.40},
}
BATCH_DISCOUNT = 0.5  # Batch API = 50% off input and output


@dataclass
class CostBreakdown:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total: float


def api_cost(model: str, input_tokens: int, output_tokens: int,
             batch: bool = False, audio_fraction: float = 0.0) -> CostBreakdown:
    """Dollar cost for an API (Gemini) run given total token counts.

    audio_fraction: share of INPUT tokens that are audio (billed at in_audio).
                    0.0 for text/image-only scenarios (movie, mmqa, ecomm).
    """
    if model not in PRICING:
        raise KeyError(f"No pricing for {model!r}. Known: {list(PRICING)}")
    p = PRICING[model]
    mult = BATCH_DISCOUNT if batch else 1.0
    in_rate = p["in"] * (1 - audio_fraction) + p["in_audio"] * audio_fraction
    in_cost = input_tokens / 1e6 * in_rate * mult
    out_cost = output_tokens / 1e6 * p["out"] * mult
    return CostBreakdown(model, input_tokens, output_tokens,
                         in_cost, out_cost, in_cost + out_cost)


def gemma_cost(total_latency_seconds: float, gpu_hourly_rate: float = 0.31) -> float:
    """Dollar cost for a local Gemma run = GPU-hours x hourly rental rate.

    Default $0.31/hr ~ a spot RTX 4090 (Vast). Use ~$1.0-1.5 for a rented
    A100 80GB. The paper used $0.18/hr for an RTX 5080. Because SemBench runs
    queries sequentially (each query internally parallelizes its own LM calls),
    summed per-query latency approximates wall-clock GPU time.
    """
    return total_latency_seconds / 3600.0 * gpu_hourly_rate


if __name__ == "__main__":
    # Illustrative: rescale the paper's measured 2.5-Flash workload to current
    # models, assuming the same token mix. (Rough — for a real number, feed the
    # actual input_tokens/output_tokens your run logs.)
    # Paper: avg SemBench system w/ 2.5 Flash = $226.64 over 5 runs, all scenarios.
    # Back out an approximate token volume from the 2.5-Flash price, then reprice.
    demo_in, demo_out = 400_000_000, 30_000_000  # placeholder token volumes
    for m in ("gemini-2.5-flash", "gemini-3.1-flash-lite",
              "gemini-3-flash-preview", "gemini-3.5-flash"):
        sync = api_cost(m, demo_in, demo_out).total
        batch = api_cost(m, demo_in, demo_out, batch=True).total
        print(f"{m:26s} sync=${sync:8.2f}  batch=${batch:8.2f}")
    print(f"{'gemma (local, 4090)':26s} 3h run  =${gemma_cost(3*3600):8.2f}")
