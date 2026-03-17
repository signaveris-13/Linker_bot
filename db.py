import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client


def save_link(url: str, title: str | None = None, summary: str | None = None) -> dict:
    client = get_client()
    data = {"url": url, "read": False}
    if title:
        data["title"] = title
    if summary:
        data["summary"] = summary
    result = client.table("links").insert(data).execute()
    return result.data[0] if result.data else {}


def get_random_unread_link() -> dict | None:
    client = get_client()
    result = (
        client.table("links")
        .select("*")
        .eq("read", False)
        .limit(1)
        # Supabase doesn't have native RANDOM() via the client, so we use offset trick
        # For a small table this is fine; for large tables add a random ordering RPC
        .execute()
    )
    return result.data[0] if result.data else None


def mark_link_read(link_id: int) -> None:
    client = get_client()
    client.table("links").update({"read": True}).eq("id", link_id).execute()


def list_unread_links(limit: int = 10) -> list[dict]:
    client = get_client()
    result = (
        client.table("links")
        .select("*")
        .eq("read", False)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def count_unread() -> int:
    client = get_client()
    result = client.table("links").select("id", count="exact").eq("read", False).execute()
    return result.count or 0
