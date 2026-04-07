"""Quality Agent - reviews emails for human tone, personalization, and compliance."""

import time

from agents.base_agent import BaseAgent
from config import QUALITY_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import GeneratedEmail, ResearchReport, QualityReview, AgentTrace


class QualityAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Quality Reviewer", model, MAX_TOKENS["quality"])

    def review(
        self,
        email: GeneratedEmail,
        research: ResearchReport,
    ) -> tuple[QualityReview, AgentTrace]:
        start = time.time()

        email_type_label = {
            "initial": "Initial Cold Email",
            "followup1": "First Follow-up Email",
            "followup2": "Second Follow-up / Breakup Email",
        }.get(email.email_type, "Email")

        user_msg = f"""Review this {email_type_label}:

Subject: {email.subject}

Body:
{email.body}

Context (what the email should reference):
- Company: {research.company_name}
- Industry: {research.industry}
- Description: {research.description}
- Pain Points: {', '.join(research.pain_points[:5])}

Personalization Elements Claimed: {', '.join(email.personalization_elements)}

Score this email on all dimensions and determine if it's approved."""

        result = self.agent.run(QUALITY_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        if "error" in result and "overall_score" not in result:
            review = QualityReview(error=result.get("error"))
        else:
            review = QualityReview(
                overall_score=result.get("overall_score", 0),
                human_score=result.get("human_score", 0),
                personalization_score=result.get("personalization_score", 0),
                spam_risk_score=result.get("spam_risk_score", 0),
                gdpr_score=result.get("gdpr_score", 0),
                tone_score=result.get("tone_score", 0),
                persuasiveness_score=result.get("persuasiveness_score", 0),
                issues=result.get("issues", []),
                approved=result.get("approved", False),
                rewrite_instructions=result.get("rewrite_instructions", ""),
            )

        trace = AgentTrace(
            agent_name="Quality Reviewer",
            input_summary=f"Reviewing {email_type_label} for {research.company_name}",
            output_summary=f"Score: {review.overall_score}/10, Approved: {review.approved}",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=review.error is None,
            error=review.error,
        )

        return review, trace
