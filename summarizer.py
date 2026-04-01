import os
import re

import anthropic
from dotenv import load_dotenv

import prompts

load_dotenv()

_client: anthropic.AsyncAnthropic | None = None

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def detect_content_language(text: str | None) -> str:
    """Return 'ru' or 'en' for summary default language."""
    if not text:
        return "en"
    sample = text[:4000]
    cyr = len(re.findall(r"[\u0400-\u04FF]", sample))
    lat = len(re.findall(r"[A-Za-z]", sample))
    if cyr > lat * 0.15:
        return "ru"
    return "en"


def telegram_lang_to_name(code: str | None) -> str:
    if not code:
        return "English"
    c = code.lower().split("-")[0]
    if c == "ru":
        return "Russian"
    return "English"


def summary_output_language_name(content_lang: str, target: str) -> str:
    """target is 'article' | 'en' | 'ru'."""
    if target == "article":
        return "Russian" if content_lang == "ru" else "English"
    if target == "ru":
        return "Russian"
    return "English"


async def article_preview(
    url: str,
    *,
    user_language_name: str,
    article_text: str | None,
) -> str:
    prompt = prompts.format_preview_prompt(
        user_language=user_language_name,
        url=url,
        article_text=article_text or "",
    )
    client = get_client()
    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


async def article_summary(
    article_text: str | None,
    *,
    content_lang: str,
    target: str,
) -> str:
    lang_name = summary_output_language_name(content_lang, target)
    prompt = prompts.format_summary_prompt(
        article_text=article_text or "",
        output_language=lang_name,
    )
    client = get_client()
    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
