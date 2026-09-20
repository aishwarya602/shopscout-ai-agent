"""
agent.py
--------
Builds the actual agentic loop:

  user goal -> LLM plans -> LLM decides to call tool(s) -> tool executes
  against real product data -> LLM observes results -> LLM either calls
  another tool or produces a final ranked recommendation.

This is LangChain's tool-calling agent pattern running on Groq's Llama 3.3
70B, which supports native function/tool calling. Conversation memory is
kept so the user can refine their ask across turns ("cheaper", "only boAt",
"add wireless earbuds too") without repeating context -- that persistence
of state across turns is part of what makes this "agentic" rather than a
single-shot Q&A.
"""

import os
from langchain_groq import ChatGroq
try:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from tools import TOOLS

SYSTEM_PROMPT = """You are ShopScout, an autonomous AI shopping assistant.

Your job: understand what the user wants to buy (category, budget, must-have
features, brand preferences), PLAN which tool calls you need, use the
search_products tool to pull real product data (never invent products,
prices, or sellers), optionally check get_product_reviews_snippet for
quality signals, and then return a clear ranked recommendation.

Rules:
- Always ground concrete product names/prices in tool output, not memory.
- If the user's request is vague (no budget or category), ask one short
  clarifying question before searching.
- When you recommend, explain WHY each pick fits (price, rating, features
  mentioned by the user) in 1-2 lines per item, ranked best-fit first.
- If the user refines their ask in a follow-up (e.g. "cheaper", "only
  Amazon"), re-plan and search again rather than just filtering your
  previous answer from memory.
- Keep the final answer concise: a short intro line + a numbered list.

When giving your final recommendation, format each product like this
(using the exact link and image URL from the tool output — never invent
or alter a URL, and skip the image line only if none was provided):

**1. Product Name** — ₹price · ⭐rating
![](image_url)
[View product](link)
"""


def build_agent():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
            "key from https://console.groq.com/keys"
        )

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        api_key=api_key,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=False,
        max_iterations=10,
        early_stopping_method="generate",
        handle_parsing_errors=True,
    )
    return executor


class ShoppingAgentSession:
    """Wraps the executor with simple turn-by-turn chat memory."""

    def __init__(self):
        self.executor = build_agent()
        self.history: list = []

    def ask(self, user_input: str) -> str:
        result = self.executor.invoke(
            {"input": user_input, "chat_history": self.history}
        )
        output = result["output"]
        self.history.append(HumanMessage(content=user_input))
        self.history.append(AIMessage(content=output))
        return output
