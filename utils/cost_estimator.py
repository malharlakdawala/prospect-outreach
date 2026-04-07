"""Cost estimation for processing prospects."""

from config import AVAILABLE_MODELS, DEFAULT_MODEL, MAX_REWRITES


def estimate_cost(num_prospects: int, model: str = DEFAULT_MODEL) -> dict:
    """Estimate API cost for processing prospects.

    Per prospect, we have:
    - Research Agent: ~2000 input + ~1000 output tokens
    - Opportunity Agent: ~1500 input + ~800 output tokens
    - Case Study Agent: ~1200 input + ~600 output tokens
    - Email Agent: ~1500 input + ~600 output tokens
    - Follow-up 1 Agent: ~1200 input + ~500 output tokens
    - Follow-up 2 Agent: ~1000 input + ~400 output tokens
    - Quality Agent (x3): ~800 input + ~500 output tokens each
    - Potential rewrites: up to MAX_REWRITES x 3 emails x 2 calls (write + review)
    """
    model_info = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL])

    # Base calls per prospect (7 agents: research + opportunity + case study + email + 2 followups + 3 quality)
    base_input = 2000 + 1500 + 1200 + 1500 + 1200 + 1000 + (800 * 3)  # 10800
    base_output = 1000 + 800 + 600 + 600 + 500 + 400 + (500 * 3)  # 5400

    # Worst-case rewrites (all 3 emails need MAX_REWRITES rewrites each)
    rewrite_input = MAX_REWRITES * 3 * (1500 + 800)  # write + review per rewrite
    rewrite_output = MAX_REWRITES * 3 * (600 + 500)

    # Average case: assume ~40% of emails need 1 rewrite
    avg_input = base_input + int(rewrite_input * 0.4)
    avg_output = base_output + int(rewrite_output * 0.4)

    total_input = avg_input * num_prospects
    total_output = avg_output * num_prospects

    cost = (
        (total_input / 1_000_000) * model_info["input_per_million"]
        + (total_output / 1_000_000) * model_info["output_per_million"]
    )

    return {
        "num_prospects": num_prospects,
        "model": model_info["name"],
        "estimated_input_tokens": total_input,
        "estimated_output_tokens": total_output,
        "estimated_cost_usd": round(cost, 4),
        "cost_per_prospect_usd": round(cost / max(num_prospects, 1), 4),
        "note": "Estimates assume ~40% of emails need one rewrite. Actual cost may vary.",
    }
