"""Opportunity Agent - identifies AI automation opportunities for the business."""

import json
import time

from agents.base_agent import BaseAgent
from config import OPPORTUNITY_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import ResearchReport, OpportunityReport, AIOpportunity, AgentTrace


class OpportunityAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Opportunity Agent", model, MAX_TOKENS["opportunity"])

    def identify(self, research: ResearchReport) -> tuple[OpportunityReport, AgentTrace]:
        start = time.time()

        user_msg = f"""Identify AI automation opportunities for this company:

Company: {research.company_name}
Industry: {research.industry} / {research.sub_industry}
Description: {research.description}
Estimated Size: {research.estimated_size}
Digital Maturity: {research.digital_maturity}
Current Tech: {', '.join(research.tech_stack_hints) if research.tech_stack_hints else 'Unknown'}
Key Offerings: {', '.join(research.key_offerings) if research.key_offerings else 'Unknown'}
Target Customers: {research.target_customers}
Pain Points: {json.dumps(research.pain_points)}

Identify the top 3-5 most relevant AI automation opportunities for this specific business."""

        result = self.agent.run(OPPORTUNITY_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        if "error" in result and not result.get("opportunities"):
            report = OpportunityReport(error=result.get("error", "Unknown error"))
        else:
            opportunities = []
            for opp in result.get("opportunities", []):
                opportunities.append(AIOpportunity(
                    name=opp.get("name", ""),
                    description=opp.get("description", ""),
                    impact=opp.get("impact", "medium"),
                    relevance_score=opp.get("relevance_score", 5),
                    complexity=opp.get("complexity", "moderate"),
                    pitch_angle=opp.get("pitch_angle", ""),
                ))
            report = OpportunityReport(
                opportunities=opportunities,
                top_recommendation=result.get("top_recommendation", ""),
                industry_context=result.get("industry_context", ""),
            )

        trace = AgentTrace(
            agent_name="Opportunity Agent",
            input_summary=f"Company: {research.company_name} ({research.industry})",
            output_summary=f"Found {len(report.opportunities)} opportunities. Top: {report.top_recommendation}",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=report.error is None,
            error=report.error,
        )

        return report, trace
