# ShopScout — AI Shopping Recommendation Agent

An autonomous shopping assistant built for **Agentic AI & Automation**. It
takes a natural-language shopping request, plans what it needs to find out,
pulls real product data through a tool call, evaluates the options, and
returns a ranked, explained recommendation — refining across turns as the
user adds constraints.

## Why this counts as "agentic"

| Agentic concept | Where it shows up |
|---|---|
| **Planning** | The LLM decides *whether* and *what* to search for before acting, and re-plans on follow-ups instead of just re-filtering old results. |
| **Tool use / grounding** | `search_products` and `get_product_reviews_snippet` are real callable tools (LangChain `@tool`) hitting live e-commerce data — the model is instructed never to invent products or prices. |
| **Autonomy** | The agent chooses the number and order of tool calls itself (`AgentExecutor`, up to 6 iterations) rather than following a fixed script. |
| **Memory / state** | Conversation history is carried across turns so "make it cheaper" or "only boAt" refines the same session. |
| **Reflection** | It can call the review-snippet tool to sanity-check a pick before finalizing, not just sort by price. |

## Architecture

```
User query
   │
   ▼
ChatGroq (Llama 3.3 70B, tool-calling)
   │  plans + decides tool calls
   ▼
AgentExecutor  ──►  search_products()          (SerpApi Google Shopping)
   │            └─► get_product_reviews_snippet() (SerpApi Google Search)
   ▼
Ranked recommendation with reasoning, returned to user
```

- **LLM / brain:** [Groq](https://console.groq.com/) running `llama-3.3-70b-versatile` — free tier, fast, native tool-calling.
- **Framework:** LangChain's `create_tool_calling_agent` + `AgentExecutor` — standard, well-documented agent pattern, easy to explain in a report/demo.
- **Real product data:** [SerpApi](https://serpapi.com/) Google Shopping engine (free tier: 100 searches/month). If no `SERPAPI_API_KEY` is set, the agent automatically falls back to a small bundled mock catalog so the project still runs end-to-end offline/for grading.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add GROQ_API_KEY (required) and SERPAPI_API_KEY (optional)
```

Get keys here:
- Groq (free): https://console.groq.com/keys
- SerpApi (free tier): https://serpapi.com/manage-api-key

### Run it — two ways

**Terminal:**
```bash
python main.py
```

**Web UI (recommended for a demo):**
```bash
streamlit run app.py
```
Opens a branded chat page in your browser (`app.py` — dark "night market" theme,
suggestion chips, live/mock data indicator). Same agent underneath — `app.py`
only adds presentation, no agent logic lives there. If you didn't put keys in
`.env`, the sidebar has password fields to paste them in directly, which is
handy for a viva/demo on a machine that isn't yours.

### Deploying the web UI

[Streamlit Community Cloud](https://streamlit.io/cloud) is the easiest free
option:
1. Push this folder to a GitHub repo.
2. On share.streamlit.io, "New app" → point it at `app.py`.
3. In the app's *Settings → Secrets*, add:
   ```
   GROQ_API_KEY = "your_key"
   SERPAPI_API_KEY = "your_key"
   ```
4. Deploy — you get a public `*.streamlit.app` link to share or submit.

## Example session

```
You: I want a smartwatch under 1500 rupees with good battery and rating above 4
ShopScout:
1. Noise ColorFit Pulse 2 — ₹1499, ★4.1, Flipkart — fits your budget exactly, strong rating.
2. Fire-Boltt Ninja Call Pro Plus — ₹1399, ★4.0, Amazon — cheaper option, still rated well.
...

You: actually only show boAt options
ShopScout: [re-plans, calls search_products again with a narrowed query]
...
```

## Extending it

- **Swap the data source:** replace the body of `search_products` in
  `tools.py` with a direct scraper (e.g. `requests` + `BeautifulSoup`
  against a specific retailer's search page) if your course wants scraping
  specifically instead of an API. Keep the function's input/output shape
  the same and nothing else needs to change.
- **Add a budget-tracking tool** that remembers a running budget across
  multiple items in one session.
- **Wrap in a UI:** the `ShoppingAgentSession` class in `agent.py` is
  UI-agnostic — you can call `.ask(text)` from a Streamlit or Flask app
  instead of `main.py`'s CLI loop.

## Files

- `agent.py` — builds the LangChain tool-calling agent + session/memory wrapper
- `tools.py` — the two tools (product search, review snippet) + mock fallback catalog
- `main.py` — CLI chat loop
- `app.py` — Streamlit web UI (same agent, browser front end)
- `.streamlit/config.toml` — app color theme
- `requirements.txt`, `.env.example` — setup
