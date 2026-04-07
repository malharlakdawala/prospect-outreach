"""Email Writer Agent - crafts personalized cold emails with human tone."""

import time

from agents.base_agent import BaseAgent
from config import EMAIL_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import (
    Prospect, ResearchReport, OpportunityReport, GeneratedEmail, AgentTrace
)


class EmailAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Email Writer", model, MAX_TOKENS["email"])

    def compose(
        self,
        prospect: Prospect,
        research: ResearchReport,
        opportunities: OpportunityReport,
        case_study: dict,
        rewrite_feedback: str = "",
    ) -> tuple[GeneratedEmail, AgentTrace]:
        start = time.time()

        opps_text = ""
        for opp in opportunities.opportunities[:3]:
            opps_text += f"- {opp.name}: {opp.pitch_angle}\n"

        case_study_text = ""
        if case_study:
            case_study_text = f"""
Case Study to Reference:
Industry: {case_study.get('industry', '')}
Solution: {case_study.get('solution', '')}
Results: {case_study.get('results', '')}
Company Description: {case_study.get('company_description', '')}"""

        user_msg = f"""Write a cold email to pitch AI automation services.

Prospect:
- Name: {prospect.first_name} {prospect.last_name}
- Role: {prospect.role or 'Decision maker'}
- Company: {research.company_name}
- Industry: {research.industry}

About Their Business:
{research.description}

Top AI Automation Opportunities:
{opps_text}

Top Recommendation: {opportunities.top_recommendation}
{case_study_text}"""

        if rewrite_feedback:
            user_msg += f"""

IMPORTANT - REWRITE REQUIRED. Previous version had issues:
{rewrite_feedback}

Fix these issues while keeping the email natural and human-sounding."""

        result = self.agent.run(EMAIL_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        if "error" in result and not result.get("subject"):
            email = GeneratedEmail(email_type="initial", error=result.get("error"))
        else:
            email = GeneratedEmail(
                subject=result.get("subject", ""),
                body=result.get("body", ""),
                personalization_elements=result.get("personalization_elements", []),
                call_to_action=result.get("call_to_action", ""),
                email_type="initial",
            )

        trace = AgentTrace(
            agent_name="Email Writer",
            input_summary=f"Prospect: {prospect.first_name} {prospect.last_name} at {research.company_name}",
            output_summary=f"Subject: {email.subject}" if email.subject else "Failed",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=email.error is None,
            error=email.error,
        )

        return email, trace
