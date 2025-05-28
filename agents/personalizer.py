"""Email personalization agent using Claude."""

import anthropic
import os


class PersonalizationAgent:
    SYSTEM_PROMPT = """You are an expert B2B email copywriter. Given prospect research data,
personalize an email template by:
1. Adding a relevant opening hook based on the prospect's recent activity
2. Connecting their pain points to our solution
3. Including a specific, compelling CTA

Keep the email under 150 words. Sound human, not salesy."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def personalize(self, template: str, prospect_data: dict) -> str:
        context = f"""Prospect: {prospect_data.get('name', 'Unknown')}
Company: {prospect_data.get('company', 'Unknown')}
Title: {prospect_data.get('title', 'Unknown')}
Industry: {prospect_data.get('industry', 'Unknown')}
Recent Activity: {prospect_data.get('recent_activity', 'N/A')}
Pain Points: {prospect_data.get('pain_points', 'N/A')}

Template to personalize:
{template}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": context}],
        )
        return response.content[0].text
