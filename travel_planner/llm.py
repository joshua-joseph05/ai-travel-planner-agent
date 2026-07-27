"""Shared Gemini LLM used by all agents."""

import os
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# gemini-3.5-flash free tier is only ~20 requests/day — use Flash-Lite by default
DEFAULT_MODEL = "gemini-3.1-flash-lite"


def get_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing API key. Set GEMINI_API_KEY in a .env file "
            "(see .env.example)."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    return ChatGoogleGenerativeAI(
        model=model,
        api_key=api_key,
        temperature=0.4,
        max_retries=3,
    )


def message_text(content: Any) -> str:
    """Normalize Gemini/LangChain message content to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
        return "\n".join(p for p in parts if p)
    return str(content)
