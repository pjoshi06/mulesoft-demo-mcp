"""
SAGE — Streamlit UI
====================
Claude Desktop–style interface for the SAGE diagnostic agent.
Connects to your deployed AWS Bedrock AgentCore Runtime via boto3.

Two-phase flow:
  Phase 1 (diagnose) → shows diagnostic report + recommendations
  Phase 2 (approve)  → human approves/rejects → finalised runbook

Run locally:
    streamlit run streamlit_app.py

Required env vars (or set in the sidebar):
    AWS_REGION              e.g. us-east-1
    AGENTCORE_RUNTIME_ARN   arn:aws:bedrock-agentcore:...
    AWS credentials via ~/.aws/credentials or env vars
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAGE · CDP Diagnostic Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — Claude Desktop aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1rem; padding-bottom: 0; max-width: 900px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
        border-right: 1px solid #2d2d4e;
    }
    [data-testid="stSidebar"] * { color: #c9c9e0 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: #2d2d4e;
        border: 1px solid #3d3d6e;
        color: #c9c9e0 !important;
        border-radius: 8px;
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #3d3d6e;
        border-color: #6366f1;
    }

    /* ── Chat bubbles ── */
    .sage-bubble-user {
        background: #f0f0ff;
        border: 1px solid #ddddf0;
        border-radius: 12px 12px 2px 12px;
        padding: 14px 18px;
        margin: 8px 0;
        max-width: 85%;
        margin-left: auto;
        font-size: 0.93rem;
        line-height: 1.6;
    }
    .sage-bubble-agent {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 2px 12px 12px 12px;
        padding: 14px 18px;
        margin: 8px 0;
        max-width: 90%;
        font-size: 0.93rem;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .sage-bubble-system {
        background: #fefce8;
        border: 1px solid #fde68a;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 0.85rem;
        color: #92400e;
        margin: 6px 0;
    }

    /* ── Risk badges ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-right: 6px;
    }
    .badge-low      { background:#d1fae5; color:#065f46; }
    .badge-medium   { background:#fef3c7; color:#92400e; }
    .badge-high     { background:#fee2e2; color:#991b1b; }
    .badge-critical { background:#7f1d1d; color:#ffffff; }
    .badge-sev1     { background:#7f1d1d; color:#fff; }
    .badge-sev2     { background:#c2410c; color:#fff; }
    .badge-sev3     { background:#d97706; color:#fff; }
    .badge-sev4     { background:#4b5563; color:#fff; }

    /* ── Rec card ── */
    .rec-card {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 8px 0;
        background: #fafafa;
    }
    .rec-card h4 { margin: 0 0 6px 0; font-size: 0.95rem; color: #111827; }
    .rec-card p  { margin: 4px 0; font-size: 0.88rem; color: #374151; }

    /* ── Submit button ── */
    div[data-testid="stForm"] .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 0.95rem;
        width: 100%;
        transition: opacity 0.15s;
    }
    div[data-testid="stForm"] .stButton > button:hover { opacity: 0.88; }

    /* ── Approve / Reject buttons ── */
    .approve-btn > div > button {
        background: #059669 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 600;
    }
    .reject-btn > div > button {
        background: #dc2626 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 600;
    }

    /* ── Divider ── */
    hr { border-color: #e5e7eb; margin: 8px 0; }

    /* ── Input fields ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
        font-size: 0.92rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "session_id":      str(uuid.uuid4()),
        "messages":        [],          # list[dict] – chat history rendered
        "pending_report":  None,        # RecommendationReport dict awaiting approval
        "pending_inc_id":  None,        # incident_id of the pending report
        "agentcore_arn":   os.getenv("AGENTCORE_RUNTIME_ARN", ""),
        "aws_region":      os.getenv("AWS_REGION", "us-east-1"),
        "running":         False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─────────────────────────────────────────────────────────────────────────────
# AgentCore helpers
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _agentcore_client(region: str):
    return boto3.client("bedrock-agentcore-runtime", region_name=region)


def _invoke_agentcore(payload: dict[str, Any]) -> dict[str, Any]:
    """Send a payload to AgentCore and return the parsed body dict."""
    client = _agentcore_client(st.session_state.aws_region)
    raw = client.invoke_agent_runtime(
        agentRuntimeArn=st.session_state.agentcore_arn,
        sessionId=st.session_state.session_id,
        payload=json.dumps(payload),
    )
    response: dict[str, Any] = json.loads(raw["output"])
    # SAGE returns {"statusCode": N, "body": "<json string>"}
    status = response.get("statusCode", 200)
    body   = json.loads(response.get("body", "{}"))
    if status >= 400:
        raise RuntimeError(body.get("error", "Unknown AgentCore error"))
    return body


def _phase1(incident: dict[str, Any]) -> dict[str, Any]:
    return _invoke_agentcore({"phase": "diagnose", "incident": incident})


def _phase2(report: dict[str, Any], decision: str, notes: str, approved_by: str) -> dict[str, Any]:
    return _invoke_agentcore({
        "phase": "approve",
        "report": report,
        "approval": {
            "decision":    decision,
            "notes":       notes,
            "approved_by": approved_by,
        },
    })

# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────
_RISK_CLASS = {
    "LOW":      "badge-low",
    "MEDIUM":   "badge-medium",
    "HIGH":     "badge-high",
    "CRITICAL": "badge-critical",
}

_SEV_CLASS = {
    "SEV1": "badge-sev1",
    "SEV2": "badge-sev2",
    "SEV3": "badge-sev3",
    "SEV4": "badge-sev4",
}


def _badge(label: str, css_class: str) -> str:
    return f'<span class="badge {css_class}">{label}</span>'


def _render_report_html(body: dict[str, Any]) -> str:
    """Convert a Phase 1 APPROVAL_REQUIRED body into styled HTML."""
    report     = body.get("report", body)           # handle both shapes
    inc_id     = report.get("incident_id", "—")
    severity   = report.get("severity", "—")
    cluster    = report.get("affected_cluster", "—")
    summary    = report.get("diagnostic_summary", "No summary available.")
    recs       = report.get("recommendations", [])
    disclaimer = report.get("disclaimer", "")

    sev_badge = _badge(severity, _SEV_CLASS.get(severity, "badge-medium"))

    html = f"""
    <div>
        <p style="margin:0 0 8px 0; font-size:0.82rem; color:#6b7280;">
            {sev_badge}
            <strong style="color:#111827;">{inc_id}</strong>
            &nbsp;·&nbsp; Cluster: <code style="background:#f3f4f6;padding:1px 6px;border-radius:4px;">{cluster}</code>
            &nbsp;·&nbsp; {datetime.now(timezone.utc).strftime("%H:%M UTC")}
        </p>
        <hr/>
        <p style="font-size:0.88rem;color:#374151;margin:8px 0 14px 0;">{summary}</p>
        <p style="font-weight:600;font-size:0.9rem;color:#111827;margin:0 0 8px 0;">
            📋 Recommendations ({len(recs)})
        </p>
    """

    for rec in recs:
        risk      = rec.get("risk_level", "LOW")
        risk_cls  = _RISK_CLASS.get(risk, "badge-medium")
        prereqs   = rec.get("prerequisites", [])
        prereq_html = ""
        if prereqs:
            items = "".join(f"<li style='margin:2px 0'>{p}</li>" for p in prereqs)
            prereq_html = f"""
            <p style="font-size:0.83rem;color:#6b7280;margin:6px 0 2px 0;font-weight:600;">Prerequisites</p>
            <ul style="margin:0;padding-left:18px;font-size:0.83rem;color:#374151">{items}</ul>
            """

        html += f"""
        <div class="rec-card">
            <h4>#{rec.get("rank","?")} &nbsp; {rec.get("title","—")} &nbsp;
                {_badge(risk, risk_cls)}
            </h4>
            <p>{rec.get("description","")}</p>
            <p style="font-size:0.83rem;color:#6b7280;">
                <strong>Impact:</strong> {rec.get("estimated_impact","—")}
            </p>
            {prereq_html}
            <p style="font-size:0.8rem;color:#6b7280;margin-top:6px;">
                <em>Risk reasoning: {rec.get("risk_reasoning","—")}</em>
            </p>
        </div>
        """

    if disclaimer:
        html += f"""
        <p style="font-size:0.78rem;color:#9ca3af;border-top:1px solid #e5e7eb;
                   padding-top:8px;margin-top:12px;">⚠️ {disclaimer}</p>
        """

    html += "</div>"
    return html


def _render_approved_html(body: dict[str, Any]) -> str:
    runbook = body.get("runbook", {})
    recs    = runbook.get("recommendations", [])
    html = f"""
    <div>
        <p style="color:#065f46;font-weight:600;font-size:0.95rem;">
            ✅ Approved by {body.get("approved_by","—")}
        </p>
        <p style="font-size:0.85rem;color:#374151;">
            Notes: {body.get("notes") or "—"}
        </p>
        <p style="font-weight:600;font-size:0.9rem;margin:10px 0 6px 0;">Finalised Runbook</p>
    """
    for rec in recs:
        risk     = rec.get("risk_level","LOW")
        risk_cls = _RISK_CLASS.get(risk,"badge-medium")
        html += f"""
        <div class="rec-card">
            <h4>#{rec.get("rank","?")} &nbsp; {rec.get("title","—")} &nbsp;
                {_badge(risk, risk_cls)}
            </h4>
            <p>{rec.get("description","")}</p>
        </div>
        """
    html += f"""
        <p style="font-size:0.78rem;color:#9ca3af;border-top:1px solid #e5e7eb;
                   padding-top:8px;margin-top:12px;">
            ⚠️ {body.get("disclaimer","")}
        </p>
    </div>"""
    return html


def _render_rejected_html(body: dict[str, Any]) -> str:
    return f"""
    <div style="color:#991b1b;">
        <p style="font-weight:600;">❌ Recommendations rejected</p>
        <p style="font-size:0.88rem;">Notes: {body.get("notes") or "—"}</p>
        <p style="font-size:0.85rem;color:#374151;">{body.get("message","")}</p>
    </div>"""


def _add_message(role: str, html: str, raw: dict | None = None) -> None:
    st.session_state.messages.append({"role": role, "html": html, "raw": raw})


def _render_messages() -> None:
    for msg in st.session_state.messages:
        role = msg["role"]
        if role == "user":
            st.markdown(
                f'<div class="sage-bubble-user">{msg["html"]}</div>',
                unsafe_allow_html=True,
            )
        elif role == "system":
            st.markdown(
                f'<div class="sage-bubble-system">{msg["html"]}</div>',
                unsafe_allow_html=True,
            )
        else:  # agent
            st.markdown(
                f'<div class="sage-bubble-agent">{msg["html"]}</div>',
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:20px 0 12px 0;">
            <div style="font-size:2.2rem;">🛡️</div>
            <div style="font-size:1.15rem;font-weight:700;color:#e0e0ff;letter-spacing:0.05em;">
                SAGE
            </div>
            <div style="font-size:0.72rem;color:#8080b0;margin-top:2px;">
                Specialist Agent for Guided Expertise
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Connection settings ──
    st.markdown(
        '<p style="font-size:0.78rem;font-weight:600;color:#8080b0;'
        'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px 0">'
        'AgentCore Connection</p>',
        unsafe_allow_html=True,
    )

    arn_input = st.text_input(
        "Runtime ARN",
        value=st.session_state.agentcore_arn,
        placeholder="arn:aws:bedrock-agentcore:...",
        label_visibility="collapsed",
        key="_arn",
    )
    if arn_input != st.session_state.agentcore_arn:
        st.session_state.agentcore_arn = arn_input

    region_input = st.text_input(
        "AWS Region",
        value=st.session_state.aws_region,
        placeholder="us-east-1",
        label_visibility="collapsed",
        key="_region",
    )
    if region_input != st.session_state.aws_region:
        st.session_state.aws_region = region_input
        st.cache_resource.clear()

    st.divider()

    # ── Session ──
    st.markdown(
        '<p style="font-size:0.78rem;font-weight:600;color:#8080b0;'
        'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px 0">'
        'Session</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-size:0.75rem;font-family:monospace;color:#6060a0;">'
        f'{st.session_state.session_id[:18]}…</p>',
        unsafe_allow_html=True,
    )
    if st.button("＋  New Session"):
        st.session_state.session_id     = str(uuid.uuid4())
        st.session_state.messages       = []
        st.session_state.pending_report = None
        st.session_state.pending_inc_id = None
        st.rerun()

    st.divider()

    # ── Severity legend ──
    st.markdown(
        '<p style="font-size:0.78rem;font-weight:600;color:#8080b0;'
        'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px 0">'
        'Severity Guide</p>',
        unsafe_allow_html=True,
    )
    for sev, desc in [
        ("SEV1", "Production down / full outage"),
        ("SEV2", "Significant degradation"),
        ("SEV3", "Partial / limited impact"),
        ("SEV4", "Minor / cosmetic"),
    ]:
        css = _SEV_CLASS[sev]
        st.markdown(
            f'<span class="badge {css}">{sev}</span>'
            f'<span style="font-size:0.78rem;"> {desc}</span><br/>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# Main area header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <span style="font-size:1.35rem;font-weight:700;color:#111827;">SAGE Diagnostic Console</span>
        <span style="background:#d1fae5;color:#065f46;font-size:0.72rem;font-weight:600;
                     padding:2px 10px;border-radius:9999px;">read-only</span>
    </div>
    <p style="font-size:0.85rem;color:#6b7280;margin:0 0 16px 0;">
        Submit an incident for AI-driven CDP diagnostics and risk-rated remediation recommendations.
        All actions require explicit human approval.
    </p>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Chat history
# ─────────────────────────────────────────────────────────────────────────────
chat_area = st.container()
with chat_area:
    if not st.session_state.messages:
        st.markdown(
            """
            <div style="text-align:center;padding:48px 0;color:#9ca3af;">
                <div style="font-size:2.5rem;margin-bottom:8px;">🛡️</div>
                <p style="font-size:1rem;font-weight:500;">Ready to diagnose</p>
                <p style="font-size:0.85rem;">
                    Fill in the incident details below and click <strong>Run Diagnostics</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        _render_messages()

# ─────────────────────────────────────────────────────────────────────────────
# Approval gate (shown only when Phase 1 has returned a pending report)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.pending_report is not None:
    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.92rem;font-weight:600;color:#92400e;">'
        '⏳ Awaiting your approval for <code style="background:#fef3c7;padding:1px 6px;'
        'border-radius:4px;">'
        f'{st.session_state.pending_inc_id}</code></p>',
        unsafe_allow_html=True,
    )

    col_notes, col_by = st.columns([3, 2])
    with col_notes:
        approval_notes = st.text_area(
            "Reviewer notes (optional)",
            placeholder="e.g. Reviewed by on-call SRE — all steps verified against runbook v3.2",
            height=68,
            key="approval_notes",
            label_visibility="visible",
        )
    with col_by:
        approved_by = st.text_input(
            "Your name / email",
            placeholder="alice@example.com",
            key="approved_by",
        )

    col_approve, col_reject, col_spacer = st.columns([2, 2, 4])
    with col_approve:
        st.markdown('<div class="approve-btn">', unsafe_allow_html=True)
        approve_clicked = st.button("✅  Approve", key="btn_approve", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_reject:
        st.markdown('<div class="reject-btn">', unsafe_allow_html=True)
        reject_clicked  = st.button("❌  Reject",  key="btn_reject",  use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if approve_clicked or reject_clicked:
        decision = "APPROVE" if approve_clicked else "REJECT"
        with st.spinner(f"Processing {decision.lower()}al…"):
            try:
                result = _phase2(
                    report     = st.session_state.pending_report,
                    decision   = decision,
                    notes      = approval_notes or "",
                    approved_by= approved_by or "anonymous",
                )
                # Add user action to chat
                _add_message(
                    "user",
                    f"<strong>{decision}</strong> — {approved_by or 'anonymous'}"
                    + (f"<br/><em>{approval_notes}</em>" if approval_notes else ""),
                )
                # Add agent response
                if decision == "APPROVE":
                    _add_message("agent", _render_approved_html(result), raw=result)
                else:
                    _add_message("agent", _render_rejected_html(result), raw=result)

                st.session_state.pending_report  = None
                st.session_state.pending_inc_id  = None
                st.rerun()
            except Exception as exc:
                st.error(f"Approval error: {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# Incident submission form
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")

if st.session_state.pending_report is not None:
    st.caption("Resolve the pending approval above before submitting a new incident.")
else:
    with st.form("incident_form", clear_on_submit=True):
        st.markdown(
            '<p style="font-size:0.88rem;font-weight:600;color:#374151;margin:0 0 10px 0;">'
            '📥 New Incident</p>',
            unsafe_allow_html=True,
        )

        # ── Row 1: Incident ID + Severity ──────────────────────────────────
        col1, col2 = st.columns([2, 1])
        with col1:
            incident_id = st.text_input(
                "Incident ID *",
                placeholder="INC-12345",
            )
        with col2:
            severity = st.selectbox(
                "Severity *",
                ["SEV1", "SEV2", "SEV3", "SEV4"],
                index=1,
            )

        # ── Row 2: Title + Cluster ──────────────────────────────────────────
        col3, col4 = st.columns([3, 2])
        with col3:
            title = st.text_input(
                "Incident Title *",
                placeholder="e.g. HDFS NameNode not responding",
            )
        with col4:
            affected_cluster = st.text_input(
                "Affected Cluster *",
                placeholder="e.g. prod-datahub-01",
            )

        # ── Row 3: Incident Details (the main textarea) ─────────────────────
        incident_details = st.text_area(
            "Incident Details *",
            placeholder=(
                "Describe the incident in full:\n"
                "• What symptoms are observed?\n"
                "• When did it start?\n"
                "• What has been tried so far?\n"
                "• Any error messages or relevant logs?"
            ),
            height=130,
        )

        # ── Row 4: Optional fields (collapsed) ─────────────────────────────
        with st.expander("Optional fields"):
            col5, col6 = st.columns(2)
            with col5:
                affected_env = st.text_input(
                    "CDP Environment",
                    placeholder="e.g. prod-aws-01",
                )
                reporter = st.text_input(
                    "Reporter",
                    placeholder="name or email",
                )
            with col6:
                tags_raw = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="hdfs, namenode, replication",
                )

        submitted = st.form_submit_button(
            "🔍  Run Diagnostics",
            use_container_width=True,
        )

    # ── Validation & submission ─────────────────────────────────────────────
    if submitted:
        errors = []
        if not incident_id.strip():
            errors.append("Incident ID is required")
        if not title.strip():
            errors.append("Incident Title is required")
        if not incident_details.strip():
            errors.append("Incident Details are required")
        if not affected_cluster.strip():
            errors.append("Affected Cluster is required")
        if not st.session_state.agentcore_arn.strip():
            errors.append("AgentCore Runtime ARN is not set (configure in sidebar)")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Build the user message for chat display
            sev_badge_html = _badge(severity, _SEV_CLASS.get(severity, "badge-medium"))
            user_html = (
                f"{sev_badge_html} <strong>{incident_id.strip()}</strong> · "
                f"<code style='background:#f3f4f6;padding:1px 6px;border-radius:4px;'>"
                f"{affected_cluster.strip()}</code><br/>"
                f"<strong>{title.strip()}</strong><br/>"
                f"<span style='color:#374151'>{incident_details.strip()}</span>"
            )
            _add_message("user", user_html)

            # Build the incident payload exactly matching IncidentPayload model
            incident_payload: dict[str, Any] = {
                "incident_id":      incident_id.strip(),
                "title":            title.strip(),
                "description":      incident_details.strip(),
                "severity":         severity,
                "affected_cluster": affected_cluster.strip(),
            }
            if affected_env.strip():
                incident_payload["affected_environment"] = affected_env.strip()
            if reporter.strip():
                incident_payload["reporter"] = reporter.strip()
            if tags_raw.strip():
                incident_payload["tags"] = [
                    t.strip() for t in tags_raw.split(",") if t.strip()
                ]

            # Phase 1 call
            _add_message(
                "system",
                "⚙️ Running diagnostics against CDP cluster… "
                "This may take 30–90 seconds.",
            )
            st.rerun()

        # Store pending call so it fires on next render
        if not errors:
            st.session_state["_pending_phase1"] = incident_payload

# ─────────────────────────────────────────────────────────────────────────────
# Execute deferred Phase 1 call (avoids running inside form callback)
# ─────────────────────────────────────────────────────────────────────────────
if "_pending_phase1" in st.session_state:
    incident_payload = st.session_state.pop("_pending_phase1")
    with st.spinner("SAGE is analysing the cluster…"):
        try:
            result = _phase1(incident_payload)

            # Locate the report object inside the returned body
            report_obj = result.get("report", result)

            # Store for Phase 2
            st.session_state.pending_report  = report_obj
            st.session_state.pending_inc_id  = incident_payload["incident_id"]

            # Remove "running" system message
            st.session_state.messages = [
                m for m in st.session_state.messages
                if m.get("html", "").find("Running diagnostics") == -1
            ]

            _add_message(
                "agent",
                _render_report_html(result),
                raw=result,
            )
            st.rerun()

        except Exception as exc:
            # Remove the "running" system message
            st.session_state.messages = [
                m for m in st.session_state.messages
                if m.get("html", "").find("Running diagnostics") == -1
            ]
            _add_message(
                "system",
                f"🚨 AgentCore error: <strong>{exc}</strong> — "
                "check the Runtime ARN and your AWS credentials.",
            )
            st.rerun()
