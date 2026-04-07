# Prospect Outreach Tool

An AI-powered Streamlit app that generates personalized email sequences for European business outreach. Uses a multi-agent pipeline to research prospects and draft tailored emails.

## How It Works

1. Upload a prospect list (Excel/CSV) with columns: First Name, Last Name, Email, Website
2. The system runs 7 specialized agents per prospect:
   - Research agent - scrapes and analyzes the prospect's company website
   - Opportunity agent - identifies AI automation opportunities
   - Email agent - drafts a personalized initial email
   - Follow-up agents - generates two follow-up emails
   - Quality agent - reviews and refines output
   - Case study agent - matches relevant case studies
3. Download results as Excel or CSV

## Prerequisites

- Python 3.8+
- Claude Code CLI (included with Claude Max plan)

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Project Structure

```
agents/          - AI agent implementations (research, email, follow-ups, etc.)
scraper/         - Website scraping utilities
data/            - Excel/CSV parsing and export
config.py        - Prompts and model configuration (default profile)
config_v2.py     - Alternative prompt configuration
orchestrator.py  - Parallel processing pipeline
models.py        - Pydantic data models
app.py           - Streamlit UI
```

## GDPR Note

You are responsible for ensuring GDPR compliance, including having a legitimate interest basis for contacting each prospect and honoring opt-out requests.
