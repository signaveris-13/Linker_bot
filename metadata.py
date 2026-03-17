import httpx
from bs4 import BeautifulSoup


async def fetch_title(url: str) -> str | None:
    """Fetch the page title and og:title from a URL."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; LinkerBot/1.0)"},
            )
            response.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Prefer og:title, fall back to <title>
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        return title_tag.string.strip()

    return None
