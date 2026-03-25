"""Campaign analytics dashboard."""

import streamlit as st
import pandas as pd
from pathlib import Path
import json


def load_campaign_data() -> pd.DataFrame:
    data_dir = Path("data/campaigns")
    if not data_dir.exists():
        return pd.DataFrame()

    records = []
    for f in data_dir.glob("*.json"):
        with open(f) as fh:
            records.append(json.load(fh))

    return pd.DataFrame(records) if records else pd.DataFrame()


def show_analytics():
    st.title("Campaign Analytics")

    df = load_campaign_data()
    if df.empty:
        st.info("No campaign data yet. Run some outreach campaigns first.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sent", len(df))
    with col2:
        opened = df["opened"].sum() if "opened" in df.columns else 0
        st.metric("Opened", opened)
    with col3:
        replied = df["replied"].sum() if "replied" in df.columns else 0
        st.metric("Replied", replied)

    if "sent_date" in df.columns:
        st.subheader("Sends Over Time")
        daily = df.groupby("sent_date").size()
        st.line_chart(daily)


if __name__ == "__main__":
    show_analytics()
