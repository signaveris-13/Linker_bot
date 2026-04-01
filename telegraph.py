import json
import os

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

TELEGRAPH_API = "https://api.telegra.ph"
_ALLOWED_TAGS = {
    "p", "h3", "h4", "ul", "ol", "li",
    "blockquote", "strong", "em", "a", "figure", "figcaption", "br",
}


def _parse_element(el) -> list:
    result = []
    if isinstance(el, NavigableString):
        text = str(el)
        if text:
            result.append(text)
    elif isinstance(el, Tag):
        tag = el.name
        if tag not in _ALLOWED_TAGS:
            for child in el.children:
                result.extend(_parse_element(child))
        else:
            children = []
            for child in el.children:
                children.extend(_parse_element(child))
            node: dict = {"tag": tag}
            if tag == "a" and el.get("href"):
                node["attrs"] = {"href": el["href"]}
            if children:
                node["children"] = children
            result.append(node)
    return result


def html_to_nodes(html_content: str) -> list:
    soup = BeautifulSoup(html_content, "html.parser")
    nodes = []
    for child in soup.children:
        nodes.extend(_parse_element(child))
    return [n for n in nodes if not (isinstance(n, str) and not n.strip())]


async def create_page(title: str, html_content: str) -> str | None:
    access_token = os.environ.get("TELEGRAPH_ACCESS_TOKEN")
    if not access_token:
        return None

    nodes = html_to_nodes(html_content)
    if not nodes:
        return None

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{TELEGRAPH_API}/createPage",
                data={
                    "access_token": access_token,
                    "title": title[:256],
                    "content": json.dumps(nodes, ensure_ascii=False),
                    "return_content": "false",
                },
            )
            data = resp.json()
            if data.get("ok"):
                return data["result"]["url"]
    except Exception:
        pass
    return None
