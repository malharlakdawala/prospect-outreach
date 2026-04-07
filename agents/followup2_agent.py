"""Follow-up 2 Agent - writes breakup-style final follow-up."""

import time

from agents.base_agent import BaseAgent
from config import FOLLOWUP2_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import (
    Prospect, ResearchReport, OpportunityReport, GeneratedEmail, AgentTrace
)


class Followup2Agent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Follow-up 2 Writer", model, MAX_TOKENS["followup"])

    def compose(
        self,
        prospect: Prospect,
        research: ResearchReport,
        opportunities: OpportunityReport,
        initial_email: GeneratedEmail,
        followup1_email: GeneratedEmail,
        rewrite_feedback: str = "",
    ) -> tuple[GeneratedEmail, AgentTrace]:
        start = time.time()

        user_msg = f"""Write a standalone value-driven email for this prospect. Do NOT reference any previous emails.

Prospect:
- Name: {prospect.first_name} {prospect.last_name}
- Company: {research.company_name}
- Industry: {research.industry}

About Their Business:
{research.description}

Industry Context (use as the hook):
{opportunities.industry_context}

Pick a DIFFERENT angle from these previous subjects (avoid similar topics):
- "{initial_email.subject}"
- "{followup1_email.subject}"

Top Automation Opportunity: {opportunities.top_recommendation}

IMPORTANT: This email must stand completely on its own. No "following up", "circling back", or referencing prior emails. Lead with an industry insight or thought-provoking question."""

        if rewrite_feedback:
            user_msg += f"""

REWRITE REQUIRED. Fix these issues:
{rewrite_feedback}"""

        result = self.agent.run(FOLLOWUP2_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        if "error" in result and not result.get("subject"):
            email = GeneratedEmail(email_type="followup2", error=result.get("error"))
        else:
            email = GeneratedEmail(
                subject=result.get("subject", ""),
                body=result.get("body", ""),
                personalization_elements=[result.get("final_hook", "")],
                call_to_action=result.get("call_to_action", ""),
                email_type="followup2",
            )

        trace = AgentTrace(
            agent_name="Follow-up 2 Writer",
            input_summary=f"Breakup email for {prospect.first_name} at {research.company_name}",
            output_summary=f"Subject: {email.subject}" if email.subject else "Failed",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=email.error is None,
            error=email.error,
        )

        return email, trace
