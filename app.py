from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st

from config import EXPORTS_DIR, MAIN_COLUMNS, PROJECT_ROOT
from src.storage import load_display_data


st.set_page_config(
    page_title="Butler SAM.gov Opportunity Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DISPLAY_COLUMNS = [
    "Fit Score/Category",
    "Opportunity Title",
    "Agency",
    "Notice Type",
    "Notice ID",
    "Due Date",
    "Days Until Due",
    "NAICS",
    "PSC",
    "Set-Aside",
    "Location",
    "Contract Ceiling",
    "Why It Fits Butler",
    "Vehicle Required",
    "Subcontract/Teaming Path",
    "SAM.gov Link",
    "Contact Name/Email",
]

USER_OUTPUTS_DIR = PROJECT_ROOT.parent / "outputs"

st.html(
    """
    <style>
      .stApp {
        background: #fbfbf8;
        color: #1f2933 !important;
      }
      .block-container {
        padding-top: 3rem;
        max-width: 1720px;
      }
      h1 {
        font-size: 2.15rem !important;
        font-weight: 700 !important;
        letter-spacing: 0 !important;
        color: #1f2933 !important;
      }
      h2, h3, p, label, span, div {
        color: #1f2933;
      }
      code, pre {
        background: #ffffff !important;
        color: #1f2933 !important;
        border: 1px solid #d8ded4 !important;
        border-radius: 8px !important;
      }
      .stDownloadButton button,
      .stDownloadButton > button,
      div[data-testid="stDownloadButton"] button,
      div[data-testid="stDownloadButton"] > button,
      .stButton button,
      .stButton > button,
      div[data-testid="stButton"] button,
      button[kind],
      button[data-testid="baseButton-secondary"],
      button[data-testid="baseButton-primary"] {
        background: #ffffff !important;
        color: #1f2933 !important;
        border: 1px solid #cfd8cc !important;
        border-radius: 8px !important;
        box-shadow: none !important;
      }
      .stDownloadButton button *,
      .stDownloadButton > button *,
      div[data-testid="stDownloadButton"] button *,
      .stButton button *,
      .stButton > button *,
      div[data-testid="stButton"] button *,
      button[kind] *,
      button[data-testid="baseButton-secondary"] *,
      button[data-testid="baseButton-primary"] * {
        color: #1f2933 !important;
      }
      input,
      textarea,
      [data-baseweb="input"],
      [data-baseweb="select"],
      [data-baseweb="slider"],
      [data-testid="stTextInput"] input {
        background: #ffffff !important;
        color: #1f2933 !important;
        border-color: #cfd8cc !important;
      }
      [data-baseweb="select"] *,
      [data-baseweb="input"] *,
      [data-baseweb="slider"] * {
        color: #1f2933 !important;
      }
      [data-testid="stTextInput"] div {
        background: #ffffff !important;
      }
      [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e5df;
        border-radius: 8px;
        padding: 14px 16px;
      }
      div[data-testid="stMetricLabel"] p {
        font-size: 0.95rem;
      }
      div[data-testid="stMetricValue"] {
        font-size: 1.45rem;
      }
      [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border: 1px solid #d9dfd6;
        border-radius: 8px;
      }
      section[data-testid="stSidebar"] {
        display: none;
      }
      .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
      }
      .stTabs [data-baseweb="tab"] {
        background: #ffffff;
        border: 1px solid #dce2da;
        border-radius: 8px 8px 0 0;
        padding: 12px 16px;
        font-size: 1rem;
      }
      .stAlert {
        color: #1f2933;
      }
      .opp-card {
        background: #ffffff;
        border: 1px solid #d8ded4;
        border-radius: 8px;
        padding: 18px 20px;
        margin: 12px 0 18px;
        box-shadow: 0 1px 2px rgba(31, 41, 51, 0.05);
      }
      .opp-title {
        font-size: 1.18rem;
        font-weight: 700;
        color: #14202b;
        margin-bottom: 8px;
      }
      .opp-meta {
        display: grid;
        grid-template-columns: repeat(4, minmax(180px, 1fr));
        gap: 10px 18px;
        margin: 12px 0;
      }
      .opp-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #5b6670;
        text-transform: uppercase;
        letter-spacing: 0;
      }
      .opp-value {
        font-size: 0.96rem;
        color: #1f2933;
        line-height: 1.35;
        overflow-wrap: anywhere;
      }
      .opp-section {
        margin-top: 12px;
      }
      .opp-section p {
        font-size: 1rem;
        line-height: 1.45;
        margin: 4px 0 0;
      }
      .opp-link a {
        color: #1f6f68 !important;
        font-weight: 700;
      }
      .download-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(180px, 1fr));
        gap: 12px;
        margin: 12px 0 22px;
      }
      .light-download {
        display: block;
        background: #ffffff;
        color: #1f2933 !important;
        border: 1px solid #cfd8cc;
        border-radius: 8px;
        padding: 12px 14px;
        font-weight: 700;
        text-align: center;
        text-decoration: none !important;
      }
      .export-grid-spacer {
        margin-top: 8px;
      }
      .refresh-command {
        background: #f7f8f5;
        border: 1px solid #d8ded4;
        border-radius: 8px;
        padding: 12px 14px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.94rem;
        line-height: 1.45;
        color: #1f2933;
        white-space: pre-wrap;
      }
      .status-line {
        font-size: 1.03rem;
        color: #52606d;
        margin: 4px 0 20px;
      }
      @media (max-width: 1100px) {
        .opp-meta {
          grid-template-columns: repeat(2, minmax(180px, 1fr));
        }
      }
    </style>
    """
)


def sort_main(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    order = {"A": 0, "B": 1, "C": 2}
    working = df.copy()
    working["_fit_order"] = working["Fit Category"].map(order).fillna(9)
    working["_due"] = pd.to_datetime(working["Due Date"], errors="coerce")
    working["_score"] = pd.to_numeric(working["Fit Score"], errors="coerce").fillna(0)
    return working.sort_values(["_fit_order", "_due", "_score"], ascending=[True, True, False]).drop(
        columns=["_fit_order", "_due", "_score"]
    )


def filter_main(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.reindex(columns=MAIN_COLUMNS)
    days = pd.to_numeric(df["Days Until Due"], errors="coerce")
    return df[(df["Fit Category"].isin(["A", "B", "C"])) & (days >= 0) & (days <= 90)]


def clean(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return html.escape(text)


def dataframe_to_tsv(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    clean_df = df.copy()
    for column in clean_df.columns:
        clean_df[column] = (
            clean_df[column]
            .fillna("")
            .astype(str)
            .str.replace("\r", " ", regex=False)
            .str.replace("\n", " ", regex=False)
            .str.replace("\t", " ", regex=False)
        )
    return clean_df.to_csv(index=False, sep="\t")


def next_refresh_text(timestamp: str) -> str:
    if not timestamp:
        return "Refresh when ready"
    parsed = pd.to_datetime(timestamp, errors="coerce")
    if pd.isna(parsed):
        return "Refresh when ready"
    return (parsed + pd.Timedelta(days=1)).strftime("%b %-d, %Y at %-I:%M %p")


def readable_notice_type(row: pd.Series) -> str:
    notice_type = str(row.get("Notice Type") or "").strip()
    stage = str(row.get("Opportunity Stage") or "").strip()
    if notice_type and notice_type.lower() not in {"unknown", "other", "nan"}:
        return notice_type
    if stage and stage.lower() not in {"unknown", "other", "nan"}:
        return stage
    return "See link for more details"


def contact_text(row: pd.Series) -> str:
    name = str(row.get("Contact Name") or "").strip()
    email = str(row.get("Contact Email") or "").strip()
    combined = " / ".join(part for part in [name, email] if part and part.lower() != "nan")
    emails = re.findall(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}", combined)
    if emails:
        return " / ".join(dict.fromkeys(emails))
    if len(combined) > 120:
        return "See SAM.gov notice for buyer contact details"
    if name and email and name.lower() != "nan" and email.lower() != "nan":
        return f"{name} / {email}"
    if name and name.lower() != "nan":
        return name
    if email and email.lower() != "nan":
        return email
    return ""


def make_readable(df: pd.DataFrame, include_rejection_reason: bool = False) -> pd.DataFrame:
    if df.empty:
        columns = DISPLAY_COLUMNS + (["Rejection Reason"] if include_rejection_reason else [])
        return pd.DataFrame(columns=columns)
    readable = pd.DataFrame()
    readable["Fit Score/Category"] = df["Fit Category"].fillna("") + " / " + df["Fit Score"].fillna("").astype(str)
    readable["Opportunity Title"] = df["Opportunity Title"].fillna("")
    readable["Agency"] = df["Agency"].fillna("")
    readable["Notice Type"] = df.apply(readable_notice_type, axis=1)
    readable["Notice ID"] = df["Notice ID"].fillna("")
    readable["Due Date"] = df["Due Date"].fillna("")
    readable["Days Until Due"] = df["Days Until Due"].fillna("")
    readable["NAICS"] = df["NAICS"].fillna("")
    readable["PSC"] = df["PSC"].fillna("")
    readable["Set-Aside"] = df["Set-Aside"].fillna("")
    readable["Location"] = df["Place of Performance"].fillna("")
    readable["Contract Ceiling"] = df["Contract Value / Ceiling"].fillna("Not stated")
    readable["Why It Fits Butler"] = df["Why It Fits Butler"].fillna("")
    readable["Vehicle Required"] = df["SeaPort / Vehicle Required"].fillna("")
    readable["Subcontract/Teaming Path"] = df["Subcontract / Teaming Path"].fillna("")
    readable["SAM.gov Link"] = df["SAM.gov Link"].fillna("")
    readable["Contact Name/Email"] = df.apply(contact_text, axis=1)
    if include_rejection_reason and "Rejection Reason" in df.columns:
        readable["Rejection Reason"] = df["Rejection Reason"].fillna("")
    return readable


def render_opportunity_card(row: pd.Series, allow_shortlist: bool = False, show_rejection: bool = False) -> None:
    if "shortlist_ids" not in st.session_state:
        st.session_state.shortlist_ids = set()
    notice_id = str(row.get("Notice ID", ""))
    link = str(row.get("SAM.gov Link", "") or "")
    link_html = (
        f'<span class="opp-link"><a href="{clean(link)}" target="_blank">Open SAM.gov notice</a></span>'
        if link
        else '<span class="opp-value">No link available</span>'
    )
    rejection_html = ""
    if show_rejection:
        rejection_html = f"""
        <div class="opp-section">
          <div class="opp-label">Rejection Reason</div>
          <p>{clean(row.get("Rejection Reason", ""))}</p>
        </div>
        """

    st.html(
        f"""<div class="opp-card">
          <div class="opp-title">{clean(row.get("Opportunity Title", ""))}</div>
          <div class="opp-meta">
            <div><div class="opp-label">Fit Score/Category</div><div class="opp-value">{clean(row.get("Fit Score/Category", ""))}</div></div>
            <div><div class="opp-label">Notice Type</div><div class="opp-value">{clean(row.get("Notice Type", ""))}</div></div>
            <div><div class="opp-label">Due Date</div><div class="opp-value">{clean(row.get("Due Date", ""))}</div></div>
            <div><div class="opp-label">Days Until Due</div><div class="opp-value">{clean(row.get("Days Until Due", ""))}</div></div>
            <div><div class="opp-label">Agency</div><div class="opp-value">{clean(row.get("Agency", ""))}</div></div>
            <div><div class="opp-label">Notice ID</div><div class="opp-value">{clean(row.get("Notice ID", ""))}</div></div>
            <div><div class="opp-label">NAICS / PSC</div><div class="opp-value">{clean(row.get("NAICS", ""))} / {clean(row.get("PSC", ""))}</div></div>
            <div><div class="opp-label">Set-Aside</div><div class="opp-value">{clean(row.get("Set-Aside", ""))}</div></div>
            <div><div class="opp-label">Location</div><div class="opp-value">{clean(row.get("Location", ""))}</div></div>
            <div><div class="opp-label">Contract Ceiling</div><div class="opp-value">{clean(row.get("Contract Ceiling", ""))}</div></div>
            <div><div class="opp-label">Vehicle Required</div><div class="opp-value">{clean(row.get("Vehicle Required", ""))}</div></div>
            <div><div class="opp-label">Contact</div><div class="opp-value">{clean(row.get("Contact Name/Email", ""))}</div></div>
          </div>
          <div class="opp-section">
            <div class="opp-label">Why It Fits Butler</div>
            <p>{clean(row.get("Why It Fits Butler", ""))}</p>
          </div>
          <div class="opp-section">
            <div class="opp-label">Subcontract/Teaming Path</div>
            <p>{clean(row.get("Subcontract/Teaming Path", ""))}</p>
          </div>
          {rejection_html}
          <div class="opp-section">{link_html}</div>
        </div>"""
    )
    if allow_shortlist:
        is_selected = notice_id in st.session_state.shortlist_ids
        label = "Remove from shortlist" if is_selected else "Add to shortlist"
        if st.button(label, key=f"shortlist_button_{notice_id}"):
            if is_selected:
                st.session_state.shortlist_ids.discard(notice_id)
            else:
                st.session_state.shortlist_ids.add(notice_id)
            st.rerun()


def render_opportunity_cards(df: pd.DataFrame, allow_shortlist: bool = False, show_rejection: bool = False) -> None:
    if df.empty:
        st.info("No opportunities to show.")
        return
    for _, row in df.iterrows():
        render_opportunity_card(row, allow_shortlist=allow_shortlist, show_rejection=show_rejection)


def render_failed_queries(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No failed queries.")
        return
    for _, row in df.iterrows():
        st.html(
            f"""<div class="opp-card">
              <div class="opp-title">{clean(row.get("error_type", "Failed query"))}</div>
              <div class="opp-meta">
                <div><div class="opp-label">HTTP Status</div><div class="opp-value">{clean(row.get("http_status_code", ""))}</div></div>
                <div><div class="opp-label">Retry Count</div><div class="opp-value">{clean(row.get("retry_count", ""))}</div></div>
                <div><div class="opp-label">Cached Data Used</div><div class="opp-value">{clean(row.get("cached_data_used", ""))}</div></div>
                <div><div class="opp-label">Partial Preserved</div><div class="opp-value">{clean(row.get("partial_results_preserved", ""))}</div></div>
              </div>
              <div class="opp-section">
                <div class="opp-label">Query Parameters</div>
                <p>{clean(row.get("query_parameters", ""))}</p>
              </div>
            </div>"""
        )


def render_refresh_log(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No refresh log yet.")
        return
    for _, row in df.tail(10).iloc[::-1].iterrows():
        st.html(
            f"""<div class="opp-card">
              <div class="opp-title">{clean(row.get("refresh_status", "Refresh"))}</div>
              <div class="opp-meta">
                <div><div class="opp-label">Timestamp</div><div class="opp-value">{clean(row.get("timestamp", ""))}</div></div>
                <div><div class="opp-label">Mode</div><div class="opp-value">{clean(row.get("mode", ""))}</div></div>
                <div><div class="opp-label">Accepted</div><div class="opp-value">{clean(row.get("accepted_results", ""))}</div></div>
                <div><div class="opp-label">Rejected</div><div class="opp-value">{clean(row.get("rejected_results", ""))}</div></div>
                <div><div class="opp-label">Raw Pulled</div><div class="opp-value">{clean(row.get("raw_results_pulled", ""))}</div></div>
                <div><div class="opp-label">Failed Queries</div><div class="opp-value">{clean(row.get("failed_queries", ""))}</div></div>
                <div><div class="opp-label">Skipped Queries</div><div class="opp-value">{clean(row.get("skipped_queries", ""))}</div></div>
                <div><div class="opp-label">API Calls</div><div class="opp-value">{clean(row.get("capacity_used", ""))}</div></div>
              </div>
            </div>"""
        )


def render_refresh_meta(meta: dict) -> None:
    st.html(
        f"""<div class="opp-card">
          <div class="opp-title">{clean(meta.get("refresh_status", "Refresh Status"))}</div>
          <div class="opp-meta">
            <div><div class="opp-label">Last Refresh</div><div class="opp-value">{clean(meta.get("last_refresh_timestamp", ""))}</div></div>
            <div><div class="opp-label">Accepted</div><div class="opp-value">{clean(meta.get("accepted_results", ""))}</div></div>
            <div><div class="opp-label">Rejected</div><div class="opp-value">{clean(meta.get("rejected_results", ""))}</div></div>
            <div><div class="opp-label">Raw Pulled</div><div class="opp-value">{clean(meta.get("raw_results_pulled", ""))}</div></div>
            <div><div class="opp-label">Failed Queries</div><div class="opp-value">{clean(meta.get("failed_queries", ""))}</div></div>
            <div><div class="opp-label">Skipped Queries</div><div class="opp-value">{clean(meta.get("skipped_queries", ""))}</div></div>
            <div><div class="opp-label">API Calls</div><div class="opp-value">{clean(meta.get("capacity_used", ""))}</div></div>
            <div><div class="opp-label">Mode</div><div class="opp-value">{clean(meta.get("mode", ""))}</div></div>
          </div>
        </div>"""
    )


main_df, rejected_df, failed_df, refresh_log_df, meta = load_display_data()
main_df = sort_main(filter_main(main_df))
status = meta.get("refresh_status", "No refresh yet")
timestamp = meta.get("last_refresh_timestamp", "")

st.title("Butler Aerospace & Defense SAM.gov Opportunity Tracker")
st.html(
    f"""<div class="status-line">
      {len(main_df)} opportunities available to view. Refreshes automatically every day (~6:00 AM ET). Next update: {clean(next_refresh_text(timestamp))}
    </div>"""
)

if status.startswith("Partial Refresh — Capacity Reached"):
    st.warning("SAM.gov query capacity was reached during refresh. Displaying partial results based on successfully retrieved opportunities.")
elif status.startswith("Partial"):
    st.warning(f"Refresh failed or incomplete. Showing last successful results from {timestamp}.")
elif "Using Cache" in status:
    st.warning(f"No new successful refresh. Showing cached results from {timestamp}.")
else:
    st.success(status)

metric_cols = st.columns(6)
metric_cols[0].metric("Accepted", int(meta.get("accepted_results", len(main_df)) or 0))
metric_cols[1].metric("Rejected", int(meta.get("rejected_results", len(rejected_df)) or 0))
metric_cols[2].metric("Raw Pulled", int(meta.get("raw_results_pulled", 0) or 0))
metric_cols[3].metric("API Calls", meta.get("capacity_used", "0/0"))
metric_cols[4].metric("Failed Queries", int(meta.get("failed_queries", len(failed_df)) or 0))
metric_cols[5].metric("Last Refresh", timestamp or "Never")

filtered = main_df.copy()

tabs = st.tabs(
    [
        "Main Butler Opportunity Dashboard",
        "Rejected / Debug View",
        "Export Center",
        "Refresh Info",
    ]
)

with tabs[0]:
    readable_filtered = make_readable(filtered)
    render_opportunity_cards(readable_filtered, allow_shortlist=True)

with tabs[1]:
    st.subheader("Rejected Opportunities")
    render_opportunity_cards(make_readable(rejected_df, include_rejection_reason=True), show_rejection=True)
    st.subheader("Failed Queries")
    render_failed_queries(failed_df)

with tabs[2]:
    st.subheader("Exports")
    readable_filtered = make_readable(filtered)
    shortlist_df = readable_filtered[readable_filtered["Notice ID"].astype(str).isin(st.session_state.get("shortlist_ids", set()))]
    st.subheader("Shortlist Copy/Paste for Excel")
    if shortlist_df.empty:
        st.info("No shortlisted opportunities yet. Add opportunities to the shortlist from the main dashboard.")
    else:
        st.caption("Click inside the box, select all, copy, and paste into Excel. Columns will separate automatically.")
        st.text_area(
            "Shortlisted opportunities",
            dataframe_to_tsv(shortlist_df),
            height=260,
            key="shortlist_copy_paste_tsv",
        )

with tabs[3]:
    st.subheader("How this dashboard refreshes")
    st.html(
        """<div class="opp-card">
          <div class="opp-title">Automatic daily refresh</div>
          <div class="opp-section">
            <p>This dashboard updates itself &mdash; there is nothing to run or paste here.
            An automated job pulls new opportunities from SAM.gov
            <strong>every day at about 6:00&nbsp;AM US Eastern (10:00&nbsp;UTC)</strong>,
            scores them for Butler fit, and saves the results. When it finishes, this page
            reloads with the fresh data on its own within a few minutes.</p>
            <p>The refresh runs on GitHub's servers rather than inside this dashboard, which
            is what lets it reach SAM.gov reliably. (Running the pull from the dashboard
            itself does not work &mdash; the shared hosting is throttled by SAM.gov, so an
            in-app refresh would fail no matter whose key was used.)</p>
            <p>If SAM.gov's daily request limit is reached mid-refresh, the job keeps the last
            good results in place instead of blanking the dashboard, and tries again the next
            day. So you may occasionally see a partial or slightly older set &mdash; but it
            will never go empty.</p>
          </div>
        </div>"""
    )

    st.subheader("Last refresh")
    render_refresh_meta(meta)
    render_refresh_log(refresh_log_df)
    st.caption("Refreshes run automatically once a day. The timestamp above shows when the data was last updated.")
