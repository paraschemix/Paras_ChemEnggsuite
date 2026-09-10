"""
utils/wiki_sheets.py
======================
Google Sheets-backed Q&A storage for the Wiki/Know-How module.

STATUS (as of this file's creation): OAuth setup is not yet complete —
GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN /
WIKI_QA_SHEET_ID are not yet in Streamlit Secrets. This module is
written to degrade gracefully rather than crash the page: every public
function checks is_configured() first and returns an empty/failure
result with an explanatory message if the secrets aren't there yet.
Once the OAuth flow (auth_setup.py) is completed and the four secrets
above are added, this starts working with no code changes needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
import streamlit as st

TOKEN_URL = "https://oauth2.googleapis.com/token"
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
QA_TAB_NAME = "QA"
QA_HEADER = ["id", "domain", "question", "answer", "author", "date"]

_REQUIRED_SECRETS = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
    "WIKI_QA_SHEET_ID",
]


@dataclass
class QAEntry:
    id: str
    domain: str
    question: str
    answer: str
    author: str
    date: str


def is_configured() -> bool:
    return all(st.secrets.get(k) for k in _REQUIRED_SECRETS)


def missing_secrets() -> list[str]:
    return [k for k in _REQUIRED_SECRETS if not st.secrets.get(k)]


@st.cache_data(ttl=60, show_spinner=False)
def _get_access_token() -> Optional[str]:
    """Exchanges the long-lived refresh token for a short-lived access
    token. Cached 60s since access tokens are valid ~1 hour but we don't
    want to rely on that; re-fetching cheaply is simpler than tracking
    expiry ourselves."""
    if not is_configured():
        return None
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "refresh_token": st.secrets["GOOGLE_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json().get("access_token")


@st.cache_data(ttl=60, show_spinner=False)
def list_qa(domain: Optional[str] = None) -> list[QAEntry]:
    if not is_configured():
        return []
    token = _get_access_token()
    if not token:
        return []

    sheet_id = st.secrets["WIKI_QA_SHEET_ID"]
    url = f"{SHEETS_API}/{sheet_id}/values/{QA_TAB_NAME}!A2:F"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if resp.status_code != 200:
        return []

    rows = resp.json().get("values", [])
    entries = []
    for row in rows:
        padded = row + [""] * (6 - len(row))  # tolerate short rows from manual sheet edits
        entry = QAEntry(id=padded[0], domain=padded[1], question=padded[2],
                         answer=padded[3], author=padded[4], date=padded[5])
        if domain is None or entry.domain == domain:
            entries.append(entry)

    entries.sort(key=lambda e: e.date, reverse=True)
    return entries


def append_qa(domain: str, question: str, answer: str, author: str) -> tuple[bool, str]:
    if not is_configured():
        return False, (
            "Q&A isn't connected yet — missing: " + ", ".join(missing_secrets()) +
            ". Complete the Google OAuth setup, then this will work automatically."
        )
    token = _get_access_token()
    if not token:
        return False, "Could not obtain a Google access token — check the refresh token is still valid."

    sheet_id = st.secrets["WIKI_QA_SHEET_ID"]
    new_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    row = [[new_id, domain, question, answer, author or "Anonymous",
            datetime.now(timezone.utc).strftime("%Y-%m-%d")]]

    url = f"{SHEETS_API}/{sheet_id}/values/{QA_TAB_NAME}!A:F:append"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
        json={"values": row},
        timeout=15,
    )
    if resp.status_code == 200:
        list_qa.clear()
        return True, "Question & answer added."
    return False, f"Sheets API error {resp.status_code}: {resp.text[:300]}"
