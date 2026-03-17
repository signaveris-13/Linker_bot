import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def summarize_url(url: str, title: str | None = None) -> str:
    """Ask Claude to summarize what a URL is about."""
    title_hint = f' (titled "{title}")' if title else ""
    prompt = (
        f"I saved this link{title_hint}: {url}\n\n"
        "In 2-3 sentences, describe what this page is likely about based on the URL and title. "
        "Be concise and useful — this is a reading list note to my future self."
    )

    client = get_client()
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
