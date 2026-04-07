"""Follow-up 1 Agent - writes first follow-up email with new angle."""

import time

from agents.base_agent import BaseAgent
from config import FOLLOWUP1_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import (
    Prospect, ResearchReport, OpportunityReport, GeneratedEmail, AgentTrace
)


class Followup1Agent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Follow-up 1 Writer", model, MAX_TOKENS["followup"])

    def compose(
        self,
        prospect: Prospect,
        research: ResearchReport,
        opportunities: OpportunityReport,
        initial_email: GeneratedEmail,
        case_study: dict,
        rewrite_feedback: str = "",
    ) -> tuple[GeneratedEmail, AgentTrace]:
        start = time.time()

        # Pick opportunities NOT highlighted in initial email
        opps_text = ""
        for opp in opportunities.opportunities[1:4]:
            opps_text += f"- {opp.name}: {opp.pitch_angle}\n"

        case_study_text = ""
        if case_study:
            case_study_text = f"""
Case Study to Reference:
Company: {case_study.get('company_description', '')}
Solution: {case_study.get('solution', '')}
Results: {case_study.get('results', '')}
One-liner: {case_study.get('one_liner', '')}"""

        user_msg = f"""Write a standalone value-driven email for this prospect. Do NOT reference any previous emails.

Prospect:
- Name: {prospect.first_name} {prospect.last_name}
- Company: {research.company_name}
- Industry: {research.industry}

About Their Business:
{research.description}

AI Automation Opportunities to Focus On (pick a different angle from "{initial_email.subject}"):
{opps_text}
{case_study_text}

IMPORTANT: This email must stand on its own. No "following up" or referencing prior contact. Lead with value."""

        if rewrite_feedback:
            user_msg += f"""

REWRITE REQUIRED. Fix these issues:
{rewrite_feedback}"""

        result = self.agent.run(FOLLOWUP1_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        if "error" in result and not result.get("subject"):
            email = GeneratedEmail(email_type="followup1", error=result.get("error"))
        else:
            email = GeneratedEmail(
                subject=result.get("subject", ""),
                body=result.get("body", ""),
                personalization_elements=[result.get("new_angle", "")],
                call_to_action=result.get("call_to_action", ""),
                email_type="followup1",
            )

        trace = AgentTrace(
            agent_name="Follow-up 1 Writer",
            input_summary=f"Follow-up for {prospect.first_name} at {research.company_name}",
            output_summary=f"Subject: {email.subject}" if email.subject else "Failed",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=email.error is None,
            error=email.error,
        )

        return email, trace
