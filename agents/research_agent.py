"""Research Agent - analyzes scraped website content to understand the business."""

import time

from agents.base_agent import BaseAgent
from config import RESEARCH_SYSTEM_PROMPT, DEFAULT_MODEL, MAX_TOKENS
from models import ScrapedWebsite, ResearchReport, AgentTrace, Prospect


class ResearchAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.agent = BaseAgent("Research Agent", model, MAX_TOKENS["research"])

    def analyze(self, scraped: ScrapedWebsite, prospect: Prospect) -> tuple[ResearchReport, AgentTrace]:
        start = time.time()

        # Build user message
        if scraped.success and scraped.main_text:
            user_msg = f"""Analyze this company's website for {prospect.first_name} {prospect.last_name}:

Website: {scraped.url}
Title: {scraped.title}
Meta Description: {scraped.meta_description}

Key Headings:
{chr(10).join('- ' + h for h in scraped.headings[:15])}

Technologies Detected: {', '.join(scraped.tech_hints) if scraped.tech_hints else 'None detected'}

Website Content:
{scraped.main_text}"""
        else:
            user_msg = f"""The website could not be scraped. Work with this limited information:

Prospect Name: {prospect.first_name} {prospect.last_name}
Company: {prospect.company or 'Unknown'}
Role: {prospect.role or 'Unknown'}
Website URL: {scraped.url}
LinkedIn: {prospect.linkedin_url or 'Not provided'}

Provide your best analysis based on what you can infer from the company name and URL."""

        result = self.agent.run(RESEARCH_SYSTEM_PROMPT, user_msg)
        duration = time.time() - start
        tokens = result.pop("_tokens_used", 0)

        # Build report
        if "error" in result and not result.get("company_name"):
            report = ResearchReport(error=result.get("error", "Unknown error"))
        else:
            report = ResearchReport(
                company_name=result.get("company_name", ""),
                industry=result.get("industry", ""),
                sub_industry=result.get("sub_industry", ""),
                description=result.get("description", ""),
                estimated_size=result.get("estimated_size", ""),
                tech_stack_hints=result.get("tech_stack_hints", []),
                digital_maturity=result.get("digital_maturity", ""),
                pain_points=result.get("pain_points", []),
                key_offerings=result.get("key_offerings", []),
                target_customers=result.get("target_customers", ""),
                confidence_score=result.get("confidence_score", 0),
            )

        trace = AgentTrace(
            agent_name="Research Agent",
            input_summary=f"Website: {scraped.url} ({scraped.pages_scraped} pages scraped)",
            output_summary=f"Industry: {report.industry}, Size: {report.estimated_size}, Pain points: {len(report.pain_points)}",
            tokens_used=tokens,
            duration_seconds=round(duration, 2),
            success=report.error is None,
            error=report.error,
        )

        return report, trace
