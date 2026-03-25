import os
import random
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


def save_link(
    url: str,
    telegram_user_id: int,
    *,
    title: str | None = None,
    ai_preview: str | None = None,
    content_language: str | None = None,
) -> dict:
    client = get_client()
    data: dict = {"url": url, "read": False, "telegram_user_id": telegram_user_id}
    if title:
        data["title"] = title
    if ai_preview:
        data["summary"] = ai_preview
    if content_language:
        data["content_language"] = content_language
    result = client.table("links").insert(data).execute()
    return result.data[0] if result.data else {}


def get_link_by_id(link_id: int, telegram_user_id: int) -> dict | None:
    client = get_client()
    result = (
        client.table("links")
        .select("*")
        .eq("id", link_id)
        .eq("telegram_user_id", telegram_user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _unread_ids_for_user(telegram_user_id: int) -> list[int]:
    client = get_client()
    result = (
        client.table("links")
        .select("id")
        .eq("read", False)
        .eq("telegram_user_id", telegram_user_id)
        .execute()
    )
    return [row["id"] for row in (result.data or [])]


def get_random_unread_link(telegram_user_id: int) -> dict | None:
    ids = _unread_ids_for_user(telegram_user_id)
    if not ids:
        return None
    chosen = random.choice(ids)
    return get_link_by_id(chosen, telegram_user_id)


def list_random_unread_links(telegram_user_id: int, limit: int = 5) -> list[dict]:
    ids = _unread_ids_for_user(telegram_user_id)
    if not ids:
        return []
    pick = random.sample(ids, min(limit, len(ids)))
    client = get_client()
    out: list[dict] = []
    for lid in pick:
        row = (
            client.table("links")
            .select("*")
            .eq("id", lid)
            .eq("telegram_user_id", telegram_user_id)
            .limit(1)
            .execute()
        )
        if row.data:
            out.append(row.data[0])
    return out


def mark_link_read(link_id: int, telegram_user_id: int) -> None:
    client = get_client()
    client.table("links").update({"read": True}).eq("id", link_id).eq(
        "telegram_user_id", telegram_user_id
    ).execute()


def count_unread(telegram_user_id: int) -> int:
    client = get_client()
    result = (
        client.table("links")
        .select("id", count="exact")
        .eq("read", False)
        .eq("telegram_user_id", telegram_user_id)
        .execute()
    )
    return result.count or 0


def update_link_cache(
    link_id: int,
    telegram_user_id: int,
    *,
    content_language: str | None = None,
    cached_summary: str | None = None,
    cached_summary_lang: str | None = None,
) -> None:
    client = get_client()
    patch: dict = {}
    if content_language is not None:
        patch["content_language"] = content_language
    if cached_summary is not None:
        patch["cached_summary"] = cached_summary
    if cached_summary_lang is not None:
        patch["cached_summary_lang"] = cached_summary_lang
    if not patch:
        return
    client.table("links").update(patch).eq("id", link_id).eq(
        "telegram_user_id", telegram_user_id
    ).execute()
