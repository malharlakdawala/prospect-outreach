"""Prospect Outreach Tool - Streamlit UI.

Uses Claude Code CLI (included with Claude Max plan) instead of API keys.
"""

import os
import shutil
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd

from data.excel_handler import parse_upload, df_to_prospects, results_to_export_df, export_to_excel, export_to_csv
from orchestrator import Orchestrator
from config import AVAILABLE_MODELS, DEFAULT_MODEL
import config as config_default
import config_v2 as config_alt

CONFIG_PROFILES = {
    "Default": {
        "module": config_default,
        "description": "Original config (config.py)",
    },
    "Custom": {
        "module": config_alt,
        "description": "Custom config (config_v2.py)",
    },
}

# Page config
st.set_page_config(
    page_title="Prospect Outreach Tool",
    page_icon="📧",
    layout="wide",
)

st.title("Prospect Outreach Tool")
st.caption("AI-powered personalized email sequences for European business outreach")

# Initialize session state
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "prospects" not in st.session_state:
    st.session_state.prospects = None
if "results" not in st.session_state:
    st.session_state.results = None
if "processing" not in st.session_state:
    st.session_state.processing = False

# --- Check Claude Code CLI is available ---
claude_available = shutil.which("claude") is not None

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    if claude_available:
        st.success("Claude Code CLI detected (using your Max plan)")
    else:
        st.error("Claude Code CLI not found. Make sure 'claude' is installed and in your PATH.")

    config_profile = st.selectbox(
        "Config Profile",
        options=list(CONFIG_PROFILES.keys()),
        help="Switch between prompt configurations (scraping + email drafting instructions)",
    )
    st.caption(CONFIG_PROFILES[config_profile]["description"])

    model = st.selectbox(
        "AI Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.keys()).index(DEFAULT_MODEL),
        format_func=lambda x: AVAILABLE_MODELS[x]["name"],
    )

    st.divider()
    st.caption("Uses Claude Code CLI (included with Claude Max plan). No API key needed.")
    st.caption("Upload an Excel/CSV with columns: First Name, Last Name, Email, Website")

# --- Section 1: Upload ---
st.header("1. Upload Prospects")

uploaded_file = st.file_uploader(
    "Upload prospect list",
    type=["xlsx", "xls", "csv"],
    help="Required columns: First Name, Last Name, Email. Optional: Website, LinkedIn URL, Company, Role",
)

if uploaded_file:
    try:
        df, warnings = parse_upload(uploaded_file)
        st.session_state.uploaded_df = df
        st.session_state.prospects = df_to_prospects(df)

        for w in warnings:
            st.warning(w)

        st.subheader(f"Preview ({len(df)} prospects)")
        st.dataframe(df.head(10), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Prospects", len(df))
        col2.metric("With Website", (df["website"] != "").sum() if "website" in df.columns else 0)
        col3.metric("With Email", (df["email"] != "").sum())

    except ValueError as e:
        st.error(str(e))
        st.session_state.uploaded_df = None
        st.session_state.prospects = None

# --- Section 2: Cost Estimate & Start ---
if st.session_state.prospects:
    st.header("2. Review & Start")

    num_prospects = len(st.session_state.prospects)
    model_name = AVAILABLE_MODELS[model]["name"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Prospects", num_prospects)
    col2.metric("Model", model_name)
    col3.metric("Agents per Prospect", "7 agents")

    st.caption("Uses your Claude Max plan via Claude Code CLI. No additional API costs.")

    if not claude_available:
        st.error("Claude Code CLI not found. Please install it first.")
    else:
        start_btn = st.button(
            "Start Processing",
            type="primary",
            disabled=st.session_state.processing,
        )

        if start_btn:
            st.session_state.processing = True
            st.session_state.results = None

            # --- Section 3: Processing ---
            st.header("3. Processing")

            selected_config = CONFIG_PROFILES[config_profile]["module"]
            orchestrator = Orchestrator(
                model=model,
                research_prompt=selected_config.RESEARCH_COMBINED_PROMPT,
                emails_prompt=selected_config.EMAILS_COMBINED_PROMPT,
            )
            prospects = st.session_state.prospects

            status_text = st.empty()
            status_text.markdown(f"**Processing {len(prospects)} prospects in parallel...**")

            with st.spinner(f"Running research + email generation for {len(prospects)} prospects..."):
                results = orchestrator.process_batch(prospects)

            st.session_state.results = results
            st.session_state.processing = False

            status_text.markdown("**Processing complete!**")

# --- Section 4: Results ---
if st.session_state.results:
    st.header("4. Results")

    results = st.session_state.results

    # Summary metrics
    success_count = sum(1 for r in results if r.status == "success")
    partial_count = sum(1 for r in results if r.status == "partial")
    failed_count = sum(1 for r in results if r.status == "failed")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Processed", len(results))
    col2.metric("Successful", success_count)
    col3.metric("Partial", partial_count)
    col4.metric("Failed", failed_count)

    # Results table
    summary_data = []
    for r in results:
        summary_data.append({
            "Name": f"{r.prospect.first_name} {r.prospect.last_name}",
            "Company": r.research.company_name if r.research else "",
            "Email 1 Subject": r.initial_email.subject if r.initial_email else "",
            "Email 2 Subject": r.followup1_email.subject if r.followup1_email else "",
            "Email 3 Subject": r.followup2_email.subject if r.followup2_email else "",
            "Status": r.status,
        })

    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

    # Detailed view per prospect
    st.subheader("Detailed View")

    for i, r in enumerate(results):
        name = f"{r.prospect.first_name} {r.prospect.last_name}"
        status_icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(r.status, "")

        with st.expander(f"{status_icon} {name} - {r.research.company_name if r.research else 'Unknown'}"):
            # Research tab
            if r.research and not r.research.error:
                st.markdown("**Research Summary**")
                col1, col2, col3 = st.columns(3)
                col1.write(f"Industry: {r.research.industry}")
                col2.write(f"Size: {r.research.estimated_size}")
                col3.write(f"Digital Maturity: {r.research.digital_maturity}")
                st.write(r.research.description)

                if r.research.pain_points:
                    st.markdown("**Pain Points:** " + ", ".join(r.research.pain_points))

            # Opportunities
            if r.opportunities and r.opportunities.opportunities:
                st.markdown("**AI Automation Opportunities**")
                for opp in r.opportunities.opportunities:
                    st.write(f"- **{opp.name}** ({opp.impact} impact): {opp.pitch_angle}")

            # Emails in tabs
            tab1, tab2, tab3, tab4 = st.tabs(["Initial Email", "Follow-up 1", "Follow-up 2", "Agent Traces"])

            with tab1:
                if r.initial_email and r.initial_email.subject:
                    st.markdown(f"**Subject:** {r.initial_email.subject}")
                    st.text_area("Email Body", r.initial_email.body, height=200, key=f"email1_{i}", disabled=True)
                else:
                    st.error("Initial email generation failed")

            with tab2:
                if r.followup1_email and r.followup1_email.subject:
                    st.markdown(f"**Subject:** {r.followup1_email.subject}")
                    st.text_area("Email Body", r.followup1_email.body, height=200, key=f"email2_{i}", disabled=True)
                else:
                    st.error("Follow-up 1 generation failed")

            with tab3:
                if r.followup2_email and r.followup2_email.subject:
                    st.markdown(f"**Subject:** {r.followup2_email.subject}")
                    st.text_area("Email Body", r.followup2_email.body, height=200, key=f"email3_{i}", disabled=True)
                else:
                    st.error("Follow-up 2 generation failed")

            with tab4:
                for trace in r.agent_traces:
                    icon = "✅" if trace.success else "❌"
                    st.write(f"{icon} **{trace.agent_name}** - {trace.duration_seconds}s")
                    st.caption(f"Input: {trace.input_summary}")
                    st.caption(f"Output: {trace.output_summary}")
                    if trace.error:
                        st.error(trace.error)

    # Export
    st.subheader("Export Results")

    export_df = results_to_export_df(results)

    col1, col2 = st.columns(2)
    with col1:
        excel_bytes = export_to_excel(export_df)
        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name="prospect_outreach_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        csv_bytes = export_to_csv(export_df)
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name="prospect_outreach_results.csv",
            mime="text/csv",
        )

# Footer
st.divider()
st.caption("GDPR Notice: This tool assists with email drafting. You are responsible for ensuring GDPR compliance, including having a legitimate interest basis for contacting each prospect and honoring opt-out requests.")
