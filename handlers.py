import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import db
import metadata
import summarizer

URL_PATTERN = re.compile(r"https?://\S+")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any plain message — if it contains a URL, save it."""
    text = update.message.text or ""
    urls = URL_PATTERN.findall(text)

    if not urls:
        await update.message.reply_text(
            "Send me a link to save it, or use /random, /list, /help."
        )
        return

    url = urls[0]
    await update.message.reply_text("Saving your link...")

    title = await metadata.fetch_title(url)
    summary = await summarizer.summarize_url(url, title)
    link = db.save_link(url, title=title, summary=summary)

    title_line = f"*{title}*\n" if title else ""
    await update.message.reply_markdown(
        f"Saved!\n\n{title_line}{summary}\n\n"
        f"You have {db.count_unread()} unread link(s)."
    )


async def cmd_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return a random unread link."""
    link = db.get_random_unread_link()
    if not link:
        await update.message.reply_text("No unread links — you're all caught up!")
        return

    title = link.get("title") or link["url"]
    summary = link.get("summary") or ""

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Mark as read", callback_data=f"read:{link['id']}")]]
    )
    await update.message.reply_markdown(
        f"*{title}*\n{link['url']}\n\n{summary}",
        reply_markup=keyboard,
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List the 10 most recently saved unread links."""
    links = db.list_unread_links(limit=10)
    if not links:
        await update.message.reply_text("No unread links saved yet.")
        return

    lines = []
    for i, link in enumerate(links, 1):
        title = link.get("title") or link["url"]
        lines.append(f"{i}. [{title}]({link['url']})")

    await update.message.reply_markdown(
        "Your unread links:\n\n" + "\n".join(lines)
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Linker Bot — your personal reading list\n\n"
        "Send any URL to save it.\n\n"
        "/random — get a random unread link\n"
        "/list   — list your 10 latest unread links\n"
        "/help   — show this message"
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("read:"):
        link_id = int(query.data.split(":")[1])
        db.mark_link_read(link_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("Marked as read.")
