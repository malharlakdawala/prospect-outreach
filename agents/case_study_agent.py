"""Case Study Agent - dynamically generates relevant case studies for each prospect."""

import time

from agents.base_agent import BaseAgent
from config import CASE_STUDY_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import ResearchReport, OpportunityReport, AgentTrace


class CaseStudyAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Case Study Writer", model, MAX_TOKENS["case_study"])

    def generate(
        self,
        research: ResearchReport,
        opportunities: OpportunityReport,
    ) -> tuple[dict, dict, AgentTrace]:
        """Generate two tailored case studies. Returns (case_study_1, case_study_2, trace)."""
        start = time.time()

        opps_text = ""
        for opp in opportunities.opportunities[:4]:
            opps_text += f"- {opp.name} ({opp.impact} impact): {opp.description}\n"

        user_msg = f"""Generate two case studies for this prospect:

Company: {research.company_name}
Industry: {research.industry} / {research.sub_industry}
Estimated Size: {research.estimated_size}
Description: {research.description}
Pain Points: {', '.join(research.pain_points) if research.pain_points else 'Unknown'}
Digital Maturity: {research.digital_maturity}

AI Automation Opportunities Identified:
{opps_text}

Top Recommendation: {opportunities.top_recommendation}

Generate two DIFFERENT case studies that would resonate with this specific company.
Case study 1 should relate to the top recommendation.
Case study 2 should relate to a different opportunity from the list."""

        result = self.agent.run(CASE_STUDY_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        cs1 = result.get("case_study_1", {})
        cs2 = result.get("case_study_2", {})

        # Ensure both have the expected keys with defaults
        for cs in [cs1, cs2]:
            cs.setdefault("company_description", "")
            cs.setdefault("solution", "")
            cs.setdefault("results", "")
            cs.setdefault("one_liner", "")

        error = result.get("error") if not cs1.get("company_description") else None

        trace = AgentTrace(
            agent_name="Case Study Writer",
            input_summary=f"Generating case studies for {research.company_name} ({research.industry})",
            output_summary=f"CS1: {cs1.get('solution', 'N/A')[:50]}... | CS2: {cs2.get('solution', 'N/A')[:50]}...",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=error is None,
            error=error,
        )

        return cs1, cs2, trace
