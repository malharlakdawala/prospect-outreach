"""Excel/CSV parsing and export."""

from io import BytesIO

import pandas as pd

from models import Prospect, ProspectResult


# Expected column names (case-insensitive matching)
REQUIRED_COLUMNS = ["first name", "last name", "email"]
OPTIONAL_COLUMNS = ["website", "linkedin url", "linkedin", "company", "role"]

COLUMN_ALIASES = {
    "first name": ["first_name", "firstname", "first", "fname"],
    "last name": ["last_name", "lastname", "last", "lname", "surname"],
    "email": ["email", "email id", "email_id", "emailid", "e-mail", "email address"],
    "website": ["website", "url", "web", "site", "company website", "company_website"],
    "linkedin url": ["linkedin url", "linkedin_url", "linkedin", "linkedin link"],
    "company": ["company", "company name", "company_name", "organization"],
    "role": ["role", "title", "job title", "job_title", "position", "designation"],
}


def _normalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Normalize column names and return warnings."""
    warnings = []
    col_map = {}

    for col in df.columns:
        col_lower = col.strip().lower()
        matched = False
        for standard_name, aliases in COLUMN_ALIASES.items():
            if col_lower in aliases or col_lower == standard_name:
                col_map[col] = standard_name
                matched = True
                break
        if not matched:
            warnings.append(f"Unknown column '{col}' will be ignored")

    df = df.rename(columns=col_map)
    return df, warnings


def parse_upload(uploaded_file) -> tuple[pd.DataFrame, list[str]]:
    """Parse uploaded Excel/CSV file into a DataFrame."""
    warnings = []

    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    df, norm_warnings = _normalize_columns(df)
    warnings.extend(norm_warnings)

    # Check required columns
    for req in REQUIRED_COLUMNS:
        if req not in df.columns:
            raise ValueError(f"Missing required column: '{req}'. Found columns: {list(df.columns)}")

    # Check optional columns
    if "website" not in df.columns:
        warnings.append("No 'Website' column found. Emails will be less personalized without website data.")

    # Count issues
    missing_website = df["website"].isna().sum() if "website" in df.columns else len(df)
    missing_email = df["email"].isna().sum()

    if missing_email > 0:
        warnings.append(f"{missing_email} rows have no email address")
    if "website" in df.columns and missing_website > 0:
        warnings.append(f"{missing_website} rows have no website URL")

    # Fill NaN with empty strings
    df = df.fillna("")

    return df, warnings


def df_to_prospects(df: pd.DataFrame) -> list[Prospect]:
    """Convert DataFrame rows to Prospect objects."""
    prospects = []
    for _, row in df.iterrows():
        prospects.append(Prospect(
            first_name=str(row.get("first name", "")).strip(),
            last_name=str(row.get("last name", "")).strip(),
            email=str(row.get("email", "")).strip(),
            website=str(row.get("website", "")).strip(),
            linkedin_url=str(row.get("linkedin url", "")).strip(),
            company=str(row.get("company", "")).strip(),
            role=str(row.get("role", "")).strip(),
        ))
    return prospects


def results_to_export_df(results: list[ProspectResult]) -> pd.DataFrame:
    """Convert results to export DataFrame with all 3 emails in separate columns."""
    rows = []
    for r in results:
        row = {
            "First Name": r.prospect.first_name,
            "Last Name": r.prospect.last_name,
            "Email": r.prospect.email,
            "Website": r.prospect.website,
            "Industry": r.research.industry if r.research else "",
            "Company Summary": r.research.description if r.research else "",
            "Opportunities": ", ".join(
                opp.name for opp in r.opportunities.opportunities
            ) if r.opportunities else "",
            "Email 1 Subject": r.initial_email.subject if r.initial_email else "",
            "Email 1 Body": r.initial_email.body if r.initial_email else "",
            "Email 2 Subject (Follow-up 1)": r.followup1_email.subject if r.followup1_email else "",
            "Email 2 Body": r.followup1_email.body if r.followup1_email else "",
            "Email 3 Subject (Follow-up 2)": r.followup2_email.subject if r.followup2_email else "",
            "Email 3 Body": r.followup2_email.body if r.followup2_email else "",
            "Status": r.status,
        }
        rows.append(row)

    return pd.DataFrame(rows)


def export_to_excel(df: pd.DataFrame) -> bytes:
    """Export DataFrame to Excel bytes."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Prospects")
        worksheet = writer.sheets["Prospects"]
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            max_len = min(max_len, 60)
            worksheet.set_column(i, i, max_len)
    return buffer.getvalue()


def export_to_csv(df: pd.DataFrame) -> bytes:
    """Export DataFrame to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")
