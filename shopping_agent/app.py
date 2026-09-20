"""
app.py
------
A proper web front end for ShopScout, built on the exact same agent brain
(agent.py / tools.py) used by the CLI in main.py. No agent logic lives here
— this file is purely presentation + chat state.

Run with:
    streamlit run app.py
"""

import os
import textwrap
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="ShopScout — AI Shopping Scout",
    page_icon="🧭",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Visual identity: a "night market" theme — ink-navy backdrop, a warm amber
# accent for prices/CTAs and a teal accent for ratings/trust signals, a
# characterful serif for the masthead, monospace for prices (receipt feel).
# ---------------------------------------------------------------------------
st.markdown(
    textwrap.dedent(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Quicksand:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

    :root {
        --bg: #ffeaf2;
        --panel: #ffffff;
        --panel-line: #ffc2d8;
        --ink: #5b2333;
        --pink: #ff4f8b;
        --lavender: #a684ff;
    }

    .stApp {
        background: var(--bg);
        color: var(--ink);
    }

    #MainMenu, footer {visibility: hidden;}
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    .stDeployButton { display: none !important; }

    .scout-hero {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 6px 0 2px 0;
    }
    .scout-mark {
        flex-shrink: 0;
    }
    .scout-title {
        font-family: 'Fredoka', sans-serif;
        font-weight: 600;
        font-size: 2.2rem;
        color: var(--pink);
        line-height: 1;
        margin: 0;
    }
    .scout-tagline {
        font-family: 'Quicksand', sans-serif;
        color: #a4677f;
        font-size: 0.95rem;
        margin-top: 4px;
    }
    .scout-divider {
        border: none;
        border-top: 2px dashed var(--panel-line);
        margin: 18px 0 16px 0;
    }

    /* Suggestion chips */
    div[data-testid="stButton"] > button {
        background: #fff5f9;
        border: 2px dashed var(--pink);
        color: var(--pink);
        border-radius: 999px;
        padding: 6px 16px;
        font-family: 'Quicksand', sans-serif;
        font-weight: 600;
        font-size: 0.88rem;
        transition: transform 0.12s ease, background 0.12s ease;
    }
    div[data-testid="stButton"] > button:hover {
        background: var(--pink);
        color: white;
        transform: scale(1.04);
    }

    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        background: var(--panel);
        border-radius: 18px;
        border: 2px solid var(--panel-line);
        padding: 6px 8px;
        box-shadow: 0 3px 0 var(--panel-line);
    }
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li {
        font-family: 'Quicksand', sans-serif;
        font-size: 0.98rem;
        color: var(--ink);
    }
    [data-testid="stChatMessageContent"] strong {
        color: var(--pink);
    }

    /* Prices / numbers */
    [data-testid="stChatMessageContent"] code {
        font-family: 'IBM Plex Mono', monospace;
        background: rgba(166, 132, 255, 0.15);
        color: var(--lavender);
        padding: 1px 6px;
        border-radius: 6px;
    }

    .stChatInputContainer {
        border-top: 2px dashed var(--panel-line);
    }

    .scout-status {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem;
        color: #c48ba3;
    }
    .scout-status.live { color: var(--lavender); }
    .scout-status.mock { color: var(--pink); }
    </style>
    """
    ),
    unsafe_allow_html=True,
)
COMPASS_SVG = """
<svg class="scout-mark" width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="18" stroke="#ff4f8b" stroke-width="2"/>
  <path d="M26 14L17 18L14 26L23 22L26 14Z" fill="#a684ff"/>
  <circle cx="20" cy="20" r="2" fill="#ffffff"/>
</svg>
"""

st.markdown(
f"""<div class="scout-hero">{COMPASS_SVG}<div>
<p class="scout-title">ShopScout</p>
<p class="scout-tagline">Your scout for real deals — grounded in live listings, not guesses.</p>
</div></div>
<hr class="scout-divider" />""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar: keys + status + how it works (kept out of the main flow so the
# chat itself stays clean)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Setup")
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    serp_configured = bool(os.getenv("SERPAPI_API_KEY"))

    groq_key_input = st.text_input(
        "Groq API key" + (" ✅ loaded from .env" if groq_configured else ""),
        value="",
        type="password",
        placeholder="Paste here if not already in .env",
    )
    serp_key_input = st.text_input(
        "SerpApi key (optional)" + (" ✅ loaded from .env" if serp_configured else ""),
        value="",
        type="password",
        placeholder="Paste here if not already in .env",
    )
    if groq_key_input:
        os.environ["GROQ_API_KEY"] = groq_key_input
    if serp_key_input:
        os.environ["SERPAPI_API_KEY"] = serp_key_input

    st.markdown("---")
    st.markdown("#### How it works")
    st.markdown(
        "1. You describe what you want to buy\n"
        "2. ShopScout plans a search and calls a live product-data tool\n"
        "3. It checks review sentiment on strong candidates\n"
        "4. It returns a ranked, reasoned pick — and refines it as you reply"
    )
    st.markdown("---")
    data_mode = "live" if os.getenv("SERPAPI_API_KEY") else "mock"
    st.markdown(
        f'<span class="scout-status {data_mode}">'
        f'● data source: {"live marketplace (SerpApi)" if data_mode == "live" else "sample catalog (no SerpApi key)"}'
        f"</span>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Session state: lazily build the agent once a Groq key is present
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session" not in st.session_state:
    st.session_state.session = None


def get_session():
    if st.session_state.session is None:
        from agent import ShoppingAgentSession  # imported here so a missing
        st.session_state.session = ShoppingAgentSession()  # key fails gracefully below
    return st.session_state.session


def send(query: str):
    st.session_state.messages.append(("user", query))
    try:
        session = get_session()
        with st.spinner("ShopScout is scouting..."):
            reply = session.ask(query)
    except Exception as e:
        reply = f"Couldn't complete that: {e}"
    st.session_state.messages.append(("assistant", reply))


if not st.session_state.messages:
    st.markdown("**Try one of these to start:**")
    chip_cols = st.columns(2)
    suggestions = [
        "Wireless earbuds under ₹2000 with good bass",
        "Gift under ₹1000 for a friend who loves tech",
        "Smartwatch with battery life over 7 days",
        "Budget laptop bag under ₹1500",
    ]
    for i, s in enumerate(suggestions):
        if chip_cols[i % 2].button(s, key=f"chip_{i}"):
            send(s)
            st.rerun()

for role, content in st.session_state.messages:
    avatar = "🧭" if role == "assistant" else "🙂"
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

user_query = st.chat_input("What are you shopping for?")
if user_query:
    send(user_query)
    st.rerun()

if not os.getenv("GROQ_API_KEY"):
    st.info("Add your Groq API key in the sidebar to start chatting. Get one free at console.groq.com/keys")
