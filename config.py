"""Configuration constants, model settings, and prompt templates."""

# Model settings
DEFAULT_MODEL = "claude-sonnet-4-6"
AVAILABLE_MODELS = {
    "claude-haiku-4-5-20251001": {"name": "Haiku 4.5 (Fastest, cheapest)", "input_per_million": 1.0, "output_per_million": 5.0},
    "claude-sonnet-4-6": {"name": "Sonnet 4.6 (Recommended)", "input_per_million": 3.0, "output_per_million": 15.0},
    "claude-opus-4-6": {"name": "Opus 4.6 (Best quality)", "input_per_million": 15.0, "output_per_million": 75.0},
}

# Scraper settings
SCRAPE_TIMEOUT = 10  # seconds
SCRAPE_DELAY = 0.5  # seconds between scrape requests
MAX_CONTENT_LENGTH = 6000  # characters of scraped text (reduced for speed)
ADDITIONAL_PAGES = ["/about", "/services"]  # reduced from 4 to 2 pages

# API settings
API_DELAY = 0.3  # seconds between CLI calls
MAX_RETRIES = 2
RETRY_BASE_DELAY = 1.0

# User-Agent for scraping
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- COMBINED PROMPTS (2 calls instead of 7) ---

RESEARCH_COMBINED_PROMPT = """You are a senior business analyst and AI automation consultant analyzing a European company. Do ALL of the following in ONE response:

1. RESEARCH: Analyze the company website to understand their business, industry, size, pain points, and digital maturity.
2. OPPORTUNITIES: Identify the top 3 AI automation opportunities for this business from: chatbots, document processing, lead qualification, workflow automation, data entry automation, reporting automation, scheduling automation, invoice processing, HR automation, quality control.
3. CASE STUDIES: Draft 2 realistic case studies (anonymized) matching their industry and opportunities, with concrete metrics.

If the website content is not in English, analyze it in its original language and provide your report in English.

Respond ONLY with valid JSON:
{
    "research": {
        "company_name": "string",
        "industry": "string",
        "sub_industry": "string",
        "description": "2-3 sentence summary",
        "estimated_size": "micro|small|medium|large",
        "tech_stack_hints": ["technologies detected"],
        "digital_maturity": "low|medium|high",
        "pain_points": ["specific operational pain points"],
        "key_offerings": ["main products/services"],
        "target_customers": "who they serve",
        "confidence_score": 0-100
    },
    "opportunities": [
        {
            "name": "string",
            "description": "what this does for them",
            "impact": "high|medium|low",
            "relevance_score": 1-10,
            "pitch_angle": "why THIS company needs THIS"
        }
    ],
    "top_recommendation": "the single best opportunity",
    "industry_context": "why AI automation matters for their industry",
    "case_study_1": {
        "company_description": "a [size] [industry] company in [European country]",
        "solution": "AI automation implemented",
        "results": "concrete outcomes",
        "one_liner": "single sentence for embedding in email"
    },
    "case_study_2": {
        "company_description": "a [size] [industry] company in [European country]",
        "solution": "DIFFERENT AI automation",
        "results": "concrete outcomes",
        "one_liner": "single sentence for embedding in email"
    }
}"""

EMAILS_COMBINED_PROMPT = """You are writing 3 standalone cold emails to pitch AI automation services to a European business prospect. Each email must work independently and take a DIFFERENT angle.

CRITICAL WRITING RULES FOR ALL 3 EMAILS:
- Address the prospect by their FIRST NAME in the greeting (e.g., "Hi {{first_name}},")
- Write like a real human. Short sentences. Contractions.
- NEVER use em dashes (—) or en dashes (–). Use periods or commas instead.
- NEVER use "Furthermore", "Moreover", "Additionally", "In addition", "Notably"
- NEVER use corporate buzzwords: "leverage", "synergy", "cutting-edge", "revolutionary", "game-changing", "best-in-class", "holistic", "paradigm", "innovative", "thriving"
- NEVER use filler phrases: "I hope this email finds you well", "I wanted to reach out", "I came across your company"
- NEVER flatter the prospect. No "you're doing a great job", "impressive work", "I love what you're doing". Be direct and value-focused.
- NEVER reference previous emails in email 2 or 3. No "following up", "I emailed you", "circling back", "touching base", "checking in". Each email is standalone.
- Each email body MUST be 70-80 words. Not more.
- Each subject line MUST be EXACTLY 2-3 words. Curiosity-driven.
- End each email with a brief opt-out line, then %signature% on its own line.

EMAIL 1 (Initial): Lead with a specific value prop backed by case study 1. Soft CTA (quick call).
EMAIL 2 (Value email): Completely different angle. Use case study 2. Different CTA (offer to send info).
EMAIL 3 (Final touch): Lead with industry trend or thought-provoking question. Easy yes/no CTA.

Respond ONLY with valid JSON:
{
    "email_1": {
        "subject": "2-3 words only",
        "body": "starts with Hi {{first_name}}, ... ends with %signature%"
    },
    "email_2": {
        "subject": "2-3 words only, different topic",
        "body": "starts with Hi {{first_name}}, ... ends with %signature%"
    },
    "email_3": {
        "subject": "2-3 words only, different topic",
        "body": "starts with Hi {{first_name}}, ... ends with %signature%"
    }
}"""
