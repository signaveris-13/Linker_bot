import httpx
from bs4 import BeautifulSoup


async def fetch_html(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; LinkerBot/1.0)"},
            )
            response.raise_for_status()
    except Exception:
        return None
    return response.text


def title_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        return title_tag.string.strip()
    return None


def article_text_from_html(html: str, max_chars: int = 50000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [ln for ln in (line.strip() for line in text.splitlines()) if ln]
    joined = "\n".join(lines)
    if len(joined) > max_chars:
        return joined[:max_chars]
    return joined


async def fetch_title(url: str) -> str | None:
    html = await fetch_html(url)
    if not html:
        return None
    return title_from_html(html)


async def fetch_article_text(url: str, max_chars: int = 50000) -> str | None:
    """Plain text from HTML for LLM prompts (truncated)."""
    html = await fetch_html(url)
    if not html:
        return None
    return article_text_from_html(html, max_chars=max_chars)
