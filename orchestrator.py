"""Orchestrator - coordinates the 2-call pipeline for each prospect."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.base_agent import BaseAgent
from scraper.website_scraper import scrape_website
from config import (
    RESEARCH_COMBINED_PROMPT as DEFAULT_RESEARCH_PROMPT,
    EMAILS_COMBINED_PROMPT as DEFAULT_EMAILS_PROMPT,
    DEFAULT_MODEL, SCRAPE_DELAY,
)
from models import (
    Prospect, ProspectResult, ResearchReport, OpportunityReport,
    AIOpportunity, GeneratedEmail, QualityReview, AgentTrace,
)


class Orchestrator:
    def __init__(self, model: str = DEFAULT_MODEL, research_prompt: str = None, emails_prompt: str = None):
        self.research_agent = BaseAgent("Research + Opportunities", model, 4096)
        self.email_agent = BaseAgent("Email Writer (x3)", model, 4096)
        self.research_prompt = research_prompt or DEFAULT_RESEARCH_PROMPT
        self.emails_prompt = emails_prompt or DEFAULT_EMAILS_PROMPT

    def process_prospect(self, prospect: Prospect, progress_callback=None) -> ProspectResult:
        """Process a single prospect with 2 CLI calls: research + emails."""
        result = ProspectResult(prospect=prospect, status="processing")

        try:
            # --- Phase 1: Scrape website ---
            if progress_callback:
                progress_callback(f"Scraping {prospect.website}...")

            scraped = scrape_website(prospect.website)

            # --- Phase 2: Research + Opportunities + Case Studies (1 call) ---
            if progress_callback:
                progress_callback("Analyzing company + identifying opportunities...")

            start = time.time()

            if scraped.success and scraped.main_text:
                research_msg = f"""Analyze this company:

Website: {scraped.url}
Title: {scraped.title}
Meta Description: {scraped.meta_description}
Headings: {', '.join(scraped.headings[:10])}
Technologies: {', '.join(scraped.tech_hints) if scraped.tech_hints else 'None detected'}

Content:
{scraped.main_text}"""
            else:
                research_msg = f"""Website could not be scraped. Work with limited info:

Name: {prospect.first_name} {prospect.last_name}
Company: {prospect.company or 'Unknown'}
Role: {prospect.role or 'Unknown'}
Website URL: {scraped.url}

Provide your best analysis from the company name and URL."""

            research_result = self.research_agent.run(self.research_prompt, research_msg)
            research_duration = time.time() - start

            # Parse research
            research_data = research_result.get("research", research_result)
            research = ResearchReport(
                company_name=research_data.get("company_name", prospect.company or ""),
                industry=research_data.get("industry", ""),
                sub_industry=research_data.get("sub_industry", ""),
                description=research_data.get("description", ""),
                estimated_size=research_data.get("estimated_size", ""),
                tech_stack_hints=research_data.get("tech_stack_hints", []),
                digital_maturity=research_data.get("digital_maturity", ""),
                pain_points=research_data.get("pain_points", []),
                key_offerings=research_data.get("key_offerings", []),
                target_customers=research_data.get("target_customers", ""),
                confidence_score=research_data.get("confidence_score", 0),
            )
            result.research = research

            # Parse opportunities
            opps_raw = research_result.get("opportunities", [])
            opportunities = OpportunityReport(
                opportunities=[
                    AIOpportunity(
                        name=o.get("name", ""),
                        description=o.get("description", ""),
                        impact=o.get("impact", "medium"),
                        relevance_score=o.get("relevance_score", 5),
                        pitch_angle=o.get("pitch_angle", ""),
                    )
                    for o in opps_raw
                ],
                top_recommendation=research_result.get("top_recommendation", ""),
                industry_context=research_result.get("industry_context", ""),
            )
            result.opportunities = opportunities

            # Parse case studies and highlights
            cs1 = research_result.get("case_study_1", {})
            cs2 = research_result.get("case_study_2", {})
            interesting_highlights = research_result.get("interesting_highlights", [])

            result.agent_traces.append(AgentTrace(
                agent_name="Research + Opportunities + Case Studies",
                input_summary=f"Website: {scraped.url} ({scraped.pages_scraped} pages)",
                output_summary=f"Industry: {research.industry}, {len(opportunities.opportunities)} opportunities found",
                tokens_used=0,
                duration_seconds=round(research_duration, 2),
                success=True,
            ))

            # --- Phase 3: All 3 Emails (1 call) ---
            if progress_callback:
                progress_callback("Writing all 3 emails...")

            start = time.time()

            opps_text = ""
            for opp in opportunities.opportunities[:3]:
                opps_text += f"- {opp.name}: {opp.pitch_angle}\n"

            highlights_text = ""
            if interesting_highlights:
                highlights_text = "\nInteresting Highlights (use for personalization):\n"
                for h in interesting_highlights:
                    highlights_text += f"- {h}\n"

            email_msg = f"""Write 3 emails for this prospect:

Prospect First Name: {prospect.first_name}
Prospect Last Name: {prospect.last_name}
Role: {prospect.role or 'Decision maker'}
Company: {research.company_name}
Industry: {research.industry}

About Their Business:
{research.description}
{highlights_text}
Industry Context: {opportunities.industry_context}

Case Study 1 (use as social proof for email 1):
{cs1.get('one_liner', cs1.get('results', ''))}

Case Study 2 (use as social proof for email 2):
{cs2.get('one_liner', cs2.get('results', ''))}

IMPORTANT: Do NOT suggest specific automation use cases for the prospect. Instead, ASK them where they spend the most hours. The case studies above are about OTHER companies, use those for social proof only.

IMPORTANT: Email 1 gets a SHORT personalization (6-8 words max). Emails 2 and 3 get NO personalization, NO filler openers like "Quick one" or "Short one". Jump straight into substance.

CRITICAL: Use the actual name "{prospect.first_name}" in each email greeting. Write "Hey {prospect.first_name}," not "Hey {{{{first_name}}}},". The name is {prospect.first_name}. Use it literally."""

            email_result = self.email_agent.run(self.emails_prompt, email_msg)
            email_duration = time.time() - start

            # Parse emails
            e1 = email_result.get("email_1", {})
            e2 = email_result.get("email_2", {})
            e3 = email_result.get("email_3", {})

            result.initial_email = GeneratedEmail(
                subject=e1.get("subject", ""),
                body=e1.get("body", ""),
                email_type="initial",
            )
            result.followup1_email = GeneratedEmail(
                subject=e2.get("subject", ""),
                body=e2.get("body", ""),
                email_type="followup1",
            )
            result.followup2_email = GeneratedEmail(
                subject=e3.get("subject", ""),
                body=e3.get("body", ""),
                email_type="followup2",
            )

            result.agent_traces.append(AgentTrace(
                agent_name="Email Writer (all 3 emails)",
                input_summary=f"Writing for {prospect.first_name} {prospect.last_name} at {research.company_name}",
                output_summary=f"Subjects: {e1.get('subject', '?')} | {e2.get('subject', '?')} | {e3.get('subject', '?')}",
                tokens_used=0,
                duration_seconds=round(email_duration, 2),
                success=True,
            ))

            # Determine status
            has_emails = (
                result.initial_email.subject
                and result.followup1_email.subject
                and result.followup2_email.subject
            )
            result.status = "success" if has_emails else "partial"

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)

        return result

    def process_batch(
        self,
        prospects: list[Prospect],
        progress_callback=None,
        max_workers: int = 3,
    ) -> list[ProspectResult]:
        """Process multiple prospects in parallel using threads."""
        results = [None] * len(prospects)

        def _run(i, prospect):
            result = self.process_prospect(prospect)
            return i, result

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_run, i, p): i
                for i, p in enumerate(prospects)
            }
            for future in as_completed(futures):
                i, result = future.result()
                results[i] = result

        return results
