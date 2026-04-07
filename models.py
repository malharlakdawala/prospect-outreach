"""Pydantic models for data flowing between agents."""

from pydantic import BaseModel, Field
from typing import Optional


class Prospect(BaseModel):
    first_name: str
    last_name: str
    email: str
    website: str = ""
    linkedin_url: str = ""
    company: str = ""
    role: str = ""


class ScrapedWebsite(BaseModel):
    url: str
    title: str = ""
    meta_description: str = ""
    headings: list[str] = Field(default_factory=list)
    main_text: str = ""
    tech_hints: list[str] = Field(default_factory=list)
    pages_scraped: int = 0
    success: bool = True
    error: Optional[str] = None


class ResearchReport(BaseModel):
    company_name: str = ""
    industry: str = ""
    sub_industry: str = ""
    description: str = ""
    estimated_size: str = ""
    tech_stack_hints: list[str] = Field(default_factory=list)
    digital_maturity: str = ""
    pain_points: list[str] = Field(default_factory=list)
    key_offerings: list[str] = Field(default_factory=list)
    target_customers: str = ""
    confidence_score: int = 0
    error: Optional[str] = None


class AIOpportunity(BaseModel):
    name: str
    description: str
    impact: str = "medium"
    relevance_score: int = 5
    complexity: str = "moderate"
    pitch_angle: str = ""


class OpportunityReport(BaseModel):
    opportunities: list[AIOpportunity] = Field(default_factory=list)
    top_recommendation: str = ""
    industry_context: str = ""
    error: Optional[str] = None


class GeneratedEmail(BaseModel):
    subject: str = ""
    body: str = ""
    personalization_elements: list[str] = Field(default_factory=list)
    call_to_action: str = ""
    email_type: str = "initial"  # initial, followup1, followup2
    error: Optional[str] = None


class QualityReview(BaseModel):
    overall_score: float = 0
    human_score: float = 0
    personalization_score: float = 0
    spam_risk_score: float = 0
    gdpr_score: float = 0
    tone_score: float = 0
    persuasiveness_score: float = 0
    issues: list[str] = Field(default_factory=list)
    approved: bool = False
    rewrite_instructions: str = ""
    error: Optional[str] = None


class AgentTrace(BaseModel):
    agent_name: str
    input_summary: str = ""
    output_summary: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0
    attempt_number: int = 1
    success: bool = True
    error: Optional[str] = None


class ProspectResult(BaseModel):
    prospect: Prospect
    research: Optional[ResearchReport] = None
    opportunities: Optional[OpportunityReport] = None
    initial_email: Optional[GeneratedEmail] = None
    initial_quality: Optional[QualityReview] = None
    followup1_email: Optional[GeneratedEmail] = None
    followup1_quality: Optional[QualityReview] = None
    followup2_email: Optional[GeneratedEmail] = None
    followup2_quality: Optional[QualityReview] = None
    agent_traces: list[AgentTrace] = Field(default_factory=list)
    status: str = "pending"  # pending, processing, success, partial, failed
    error_message: Optional[str] = None
