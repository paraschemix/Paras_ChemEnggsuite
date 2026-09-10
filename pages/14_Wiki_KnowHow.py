"""
pages/14_📚_Wiki_KnowHow.py
=============================
Wiki / Know-How / Q&A hub. Like page 13 (Unit Converter), this is a
standalone utility page — not one of the 12 engineering domains, not
counted in utils/tool_roadmap.py's ROADMAP/DOMAIN_PAGES roadmap
invariant. Linked from every domain page's footer nav instead
(utils/ui_components.render_domain_footer_nav).

Two storage backends, per the persistence decision made for this
module (see project notes): long-form Articles/Know-How are committed
to this GitHub repo as markdown (utils/wiki_github.py); short Q&A
entries live in a Google Sheet (utils/wiki_sheets.py). Both are
optional at runtime - if GITHUB_TOKEN or the Google OAuth secrets
aren't configured yet, the relevant tab degrades to a clear "not
connected yet" message instead of crashing the page.

Contribution is gated by a single shared WIKI_EDIT_TOKEN (Streamlit
secret) rather than full per-user auth - see project decision log.
"""

import streamlit as st

from utils.ui_components import (
    inject_global_css, render_page_header, render_brand_header, render_unit_toggle,
    render_domain_footer_nav,
)
from utils.tool_roadmap import get_domain_order
from utils import wiki_github, wiki_sheets

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="📚")
inject_global_css()

with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()

render_page_header(
    "📚 Wiki / Know-How",
    "Technical articles, engineering know-how, and Q&A contributed and maintained by the "
    "licensee community - cross-linked from every domain's tool pages.",
)

DOMAIN_OPTIONS = ["All domains"] + get_domain_order()

# Pre-select a domain if arrived at via a domain page's "Related Wiki
# articles" footer link (?domain=<label>).
query_domain = st.query_params.get("domain")
default_domain_index = DOMAIN_OPTIONS.index(query_domain) if query_domain in DOMAIN_OPTIONS else 0


def _is_editor_unlocked() -> bool:
    """Session-scoped gate: once the correct shared token is entered,
    stays unlocked for the rest of this browser session (not persisted
    beyond it - re-entering the token after a hard refresh is expected,
    same friction level as most shared-password setups)."""
    return st.session_state.get("wiki_editor_unlocked", False)


def _render_editor_gate() -> None:
    configured_token = st.secrets.get("WIKI_EDIT_TOKEN")
    if not configured_token:
        st.info("Contribution is disabled: WIKI_EDIT_TOKEN is not set in Streamlit Secrets yet.")
        return
    entered = st.text_input("Enter the contributor access token to add/edit content", type="password", key="wiki_token_input")
    if st.button("Unlock", key="wiki_unlock_btn"):
        if entered == configured_token:
            st.session_state["wiki_editor_unlocked"] = True
            st.rerun()
        else:
            st.error("Incorrect token.")


tab_articles, tab_knowhow, tab_qa = st.tabs(["📄 Articles", "🛠️ Know-How", "❓ Q&A"])

# ---------------------------------------------------------------------
# Articles + Know-How share the same GitHub-backed storage and layout;
# they're split into two tabs purely as a content-type filter (meta
# field could later distinguish them, e.g. meta["kind"] - kept simple
# here by using the domain-tag + free browsing for now, with Know-How
# framed as the "quick tips/gotchas" tab and Articles as the "full
# writeups" tab, both pulling from the same wiki/articles/ folder).
# ---------------------------------------------------------------------

def _render_article_browser(tab_label: str) -> None:
    domain_choice = st.selectbox(
        "Filter by domain", DOMAIN_OPTIONS, index=default_domain_index, key=f"domain_filter_{tab_label}",
    )
    filter_domain = None if domain_choice == "All domains" else domain_choice

    try:
        articles = wiki_github.list_articles(domain=filter_domain)
    except Exception as exc:
        st.warning(f"Could not load articles from GitHub right now ({exc}). "
                    "This usually means GITHUB_TOKEN isn't set, or the repo/wiki/articles folder doesn't exist yet.")
        articles = []

    if not articles:
        st.caption("No articles yet for this filter. Be the first to add one below.")
    for article in articles:
        with st.expander(f"**{article.title}**  ·  {article.domain}  ·  {article.date}  ·  by {article.author}"):
            st.markdown(article.body)
            if article.tags:
                st.caption("Tags: " + ", ".join(article.tags))


def _render_contribute_form(tab_label: str) -> None:
    st.markdown("##### ➕ Add / update an article")
    if not _is_editor_unlocked():
        _render_editor_gate()
        return

    with st.form(key=f"wiki_article_form_{tab_label}"):
        title = st.text_input("Title")
        domain = st.selectbox("Domain", get_domain_order(), key=f"new_article_domain_{tab_label}")
        author = st.text_input("Your name")
        tags_raw = st.text_input("Tags (comma-separated, optional)")
        body = st.text_area("Content (Markdown supported)", height=250)
        submitted = st.form_submit_button("Save to Wiki")

    if submitted:
        if not title.strip() or not body.strip():
            st.error("Title and content are both required.")
        else:
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            ok, msg = wiki_github.commit_article(title=title, domain=domain, author=author, tags=tags, body=body)
            (st.success if ok else st.error)(msg)


with tab_articles:
    _render_article_browser("articles")
    st.divider()
    _render_contribute_form("articles")

with tab_knowhow:
    st.caption("Same library as Articles - use this tab for quick tips, gotchas, and field notes; use Articles for full writeups.")
    _render_article_browser("knowhow")
    st.divider()
    _render_contribute_form("knowhow")

with tab_qa:
    domain_choice_qa = st.selectbox("Filter by domain", DOMAIN_OPTIONS, index=default_domain_index, key="domain_filter_qa")
    filter_domain_qa = None if domain_choice_qa == "All domains" else domain_choice_qa

    if not wiki_sheets.is_configured():
        st.info(
            "Q&A isn't connected yet - Google OAuth setup is in progress. "
            "Missing: " + ", ".join(wiki_sheets.missing_secrets()) +
            ". This tab will start working automatically once those are added to Streamlit Secrets, no code changes needed."
        )
    else:
        entries = wiki_sheets.list_qa(domain=filter_domain_qa)
        if not entries:
            st.caption("No questions yet for this filter. Be the first to ask below.")
        for entry in entries:
            with st.expander(f"**Q: {entry.question}**  ·  {entry.domain}  ·  {entry.date}"):
                st.markdown(entry.answer)
                st.caption(f"Answered by {entry.author}")

    st.divider()
    st.markdown("##### ➕ Ask / answer a question")
    if not _is_editor_unlocked():
        _render_editor_gate()
    else:
        with st.form(key="wiki_qa_form"):
            qa_domain = st.selectbox("Domain", get_domain_order(), key="new_qa_domain")
            question = st.text_input("Question")
            answer = st.text_area("Answer", height=150)
            qa_author = st.text_input("Your name", key="new_qa_author")
            qa_submitted = st.form_submit_button("Add Q&A")

        if qa_submitted:
            if not question.strip() or not answer.strip():
                st.error("Both question and answer are required.")
            else:
                ok, msg = wiki_sheets.append_qa(domain=qa_domain, question=question, answer=answer, author=qa_author)
                (st.success if ok else st.error)(msg)

render_domain_footer_nav("pages/14_📚_Wiki_KnowHow.py")
