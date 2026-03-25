import html
import re
from urllib.parse import urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db
import metadata
import summarizer

URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.I)


def user_locale(update: Update) -> str:
    u = update.effective_user
    if u and u.language_code and u.language_code.lower().startswith("ru"):
        return "ru"
    return "en"


def t(locale: str, key: str) -> str:
    ru = {
        "saving": "Сохраняю ссылку…",
        "saved": "Сохранено.",
        "unread_left": "Непрочитанных ссылок: {n}.",
        "no_unread": "Непрочитанных ссылок нет — вы всё прочитали.",
        "list_empty": "Пока нет непрочитанных ссылок.",
        "pick_list": "Случайные непрочитанные (нажмите, чтобы открыть карточку):",
        "open": "Открыть",
        "summary": "Саммари",
        "mark_read": "Прочитано",
        "marked": "Отмечено как прочитанное.",
        "not_found": "Ссылка не найдена.",
        "help_title": "Linker — личный read-later в Telegram",
        "help_body": (
            "Отправьте сообщение с <b>URL</b> — бот сохранит ссылку, подтянет заголовок и "
            "сделает <b>превью статьи</b> (тема, сигнал/вода, время чтения).\n\n"
            "<b>/random</b> — одна случайная непрочитанная ссылка (открыть, саммари, прочитано).\n"
            "<b>/list</b> — 5 случайных непрочитанных; выберите одну — откроется та же карточка.\n"
            "<b>/help</b> или <b>/start</b> — эта справка.\n"
        ),
        "invalid": (
            "В сообщении нет ссылки. Отправьте URL (https://…), чтобы сохранить материал, "
            "или воспользуйтесь командами ниже."
        ),
        "bad_url": "Не удалось распознать ссылку.",
        "summary_wait": "Готовлю саммари…",
        "lang_en": "EN",
        "lang_ru": "RU",
    }
    en = {
        "saving": "Saving your link…",
        "saved": "Saved.",
        "unread_left": "Unread links: {n}.",
        "no_unread": "No unread links — you're all caught up!",
        "list_empty": "No unread links yet.",
        "pick_list": "Random unread (tap to open the card):",
        "open": "Open",
        "summary": "Summary",
        "mark_read": "Mark as read",
        "marked": "Marked as read.",
        "not_found": "Link not found.",
        "help_title": "Linker — your personal read-later bot",
        "help_body": (
            "Send a message with a <b>URL</b> — the bot saves it, fetches the title, and builds an "
            "<b>article preview</b> (topic, signal/water, reading time).\n\n"
            "<b>/random</b> — one random unread link (open, summary, mark as read).\n"
            "<b>/list</b> — five random unread links; pick one to open the same card.\n"
            "<b>/help</b> or <b>/start</b> — this help.\n"
        ),
        "invalid": (
            "No link in your message. Send a URL (https://…) to save it, or use the commands below."
        ),
        "bad_url": "Could not parse a valid link.",
        "summary_wait": "Preparing summary…",
        "lang_en": "EN",
        "lang_ru": "RU",
    }
    d = ru if locale == "ru" else en
    return d[key]


def commands_footer(locale: str) -> str:
    if locale == "ru":
        return "\n\n—\n<b>Команды:</b> /random · /list · /help"
    return "\n\n—\n<b>Commands:</b> /random · /list · /help"


def trunc(s: str, n: int = 3500) -> str:
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def cache_key_for_summary(link: dict, target: str) -> str:
    cl = (link.get("content_language") or "en").lower()
    if cl not in ("en", "ru"):
        cl = "en"
    if target == "article":
        return cl
    return target


def link_keyboard(link: dict, locale: str) -> InlineKeyboardMarkup:
    lid = link["id"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t(locale, "open"), url=link["url"])],
            [
                InlineKeyboardButton(
                    t(locale, "summary"), callback_data=f"s:{lid}"
                ),
                InlineKeyboardButton(
                    t(locale, "mark_read"), callback_data=f"r:{lid}"
                ),
            ],
        ]
    )


def summary_keyboard(link: dict, locale: str) -> InlineKeyboardMarkup:
    lid = link["id"]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t(locale, "lang_en"), callback_data=f"s:{lid}:en"),
                InlineKeyboardButton(t(locale, "lang_ru"), callback_data=f"s:{lid}:ru"),
            ],
            [
                InlineKeyboardButton(
                    t(locale, "mark_read"), callback_data=f"r:{lid}"
                ),
            ],
        ]
    )


def format_card_html(title: str, url: str, preview: str) -> str:
    safe_title = html.escape(title or url)
    display = html.escape(url)
    safe_preview = html.escape(preview)
    return (
        f"<b>{safe_title}</b>\n"
        f'<a href="{html.escape(url, quote=True)}">{display}</a>\n\n'
        f"<pre>{safe_preview}</pre>"
    )


def format_summary_html(body: str) -> str:
    return "<pre>" + html.escape(body) + "</pre>"


def first_url(text: str) -> str | None:
    m = URL_PATTERN.search(text.strip())
    return m.group(0).rstrip(").,;]") if m else None


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    locale = user_locale(update)
    body = f"<b>{t(locale, 'help_title')}</b>\n\n{t(locale, 'help_body')}{commands_footer(locale)}"
    await update.message.reply_text(body, parse_mode="HTML")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    locale = user_locale(update)
    text = update.message.text or ""
    uid = update.effective_user.id
    url = first_url(text)

    if not url:
        await update.message.reply_text(
            t(locale, "invalid") + commands_footer(locale),
            parse_mode="HTML",
        )
        return

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            await update.message.reply_text(
                t(locale, "bad_url") + commands_footer(locale),
                parse_mode="HTML",
            )
            return
    except Exception:
        await update.message.reply_text(
            t(locale, "bad_url") + commands_footer(locale),
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(t(locale, "saving"))

    page_html = await metadata.fetch_html(url)
    if page_html:
        title = metadata.title_from_html(page_html)
        article_text = metadata.article_text_from_html(page_html)
    else:
        title, article_text = None, None

    user_lang_name = summarizer.telegram_lang_to_name(
        update.effective_user.language_code if update.effective_user else None
    )
    content_lang = summarizer.detect_content_language(article_text)

    preview_task = summarizer.article_preview(
        url,
        user_language_name=user_lang_name,
        article_text=article_text,
    )
    preview = await preview_task

    saved = db.save_link(
        url,
        uid,
        title=title,
        ai_preview=preview,
        content_language=content_lang,
    )

    n = db.count_unread(uid)
    title_line = title or url
    msg = (
        f"{t(locale, 'saved')}\n\n"
        f"{format_card_html(title_line, url, trunc(preview))}\n\n"
        f"{t(locale, 'unread_left').format(n=n)}"
        f"{commands_footer(locale)}"
    )
    card = dict(saved)
    if "id" not in card:
        await update.message.reply_text(msg, parse_mode="HTML")
        return
    await update.message.reply_text(
        msg,
        parse_mode="HTML",
        reply_markup=link_keyboard(card, locale),
    )


async def cmd_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    locale = user_locale(update)
    uid = update.effective_user.id
    link = db.get_random_unread_link(uid)
    if not link:
        await update.message.reply_text(
            t(locale, "no_unread") + commands_footer(locale),
            parse_mode="HTML",
        )
        return

    title = link.get("title") or link["url"]
    preview = link.get("summary") or ""
    body = format_card_html(title, link["url"], trunc(preview)) + commands_footer(locale)
    await update.message.reply_text(
        body,
        parse_mode="HTML",
        reply_markup=link_keyboard(link, locale),
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    locale = user_locale(update)
    uid = update.effective_user.id
    links = db.list_random_unread_links(uid, limit=5)
    if not links:
        await update.message.reply_text(
            t(locale, "list_empty") + commands_footer(locale),
            parse_mode="HTML",
        )
        return

    lines = [t(locale, "pick_list")]
    buttons: list[list[InlineKeyboardButton]] = []
    for i, link in enumerate(links, 1):
        label = link.get("title") or link["url"]
        if len(label) > 48:
            label = label[:45] + "…"
        lines.append(f"{i}. {html.escape(label)}")
        buttons.append(
            [InlineKeyboardButton(f"{i}. {label[:32]}", callback_data=f"p:{link['id']}")]
        )

    list_body = "\n".join(lines) + commands_footer(locale)
    await update.message.reply_text(
        list_body,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    locale = user_locale(update)
    uid = update.effective_user.id
    data = query.data or ""

    if data.startswith("r:"):
        lid = int(data.split(":")[1])
        link = db.get_link_by_id(lid, uid)
        if not link:
            await query.answer(t(locale, "not_found"), show_alert=True)
            return
        await query.answer()
        db.mark_link_read(lid, uid)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            t(locale, "marked") + commands_footer(locale),
            parse_mode="HTML",
        )
        return

    if data.startswith("p:"):
        lid = int(data.split(":")[1])
        link = db.get_link_by_id(lid, uid)
        if not link:
            await query.answer(t(locale, "not_found"), show_alert=True)
            return
        await query.answer()
        title = link.get("title") or link["url"]
        preview = link.get("summary") or ""
        body = format_card_html(title, link["url"], trunc(preview)) + commands_footer(locale)
        await query.message.reply_text(
            body,
            parse_mode="HTML",
            reply_markup=link_keyboard(link, locale),
        )
        return

    if data.startswith("s:"):
        parts = data.split(":")
        lid = int(parts[1])
        target = parts[2] if len(parts) > 2 else "article"
        if target not in ("article", "en", "ru"):
            target = "article"
        link = db.get_link_by_id(lid, uid)
        if not link:
            await query.answer(t(locale, "not_found"), show_alert=True)
            return
        await query.answer()

        try:
            await query.edit_message_text(
                t(locale, "summary_wait"),
                parse_mode="HTML",
            )
        except Exception:
            pass

        article_text = await metadata.fetch_article_text(link["url"])
        cl = link.get("content_language") or summarizer.detect_content_language(article_text)
        if not link.get("content_language") and article_text:
            db.update_link_cache(lid, uid, content_language=cl)
        link = db.get_link_by_id(lid, uid) or link
        if not link.get("content_language") and cl:
            link["content_language"] = cl

        key = cache_key_for_summary(link, target)
        body: str | None = None
        if link.get("cached_summary") and (link.get("cached_summary_lang") or "") == key:
            body = link["cached_summary"]
        if body is None:
            body = await summarizer.article_summary(
                article_text,
                content_lang=cl,
                target=target,
            )
            db.update_link_cache(
                lid,
                uid,
                cached_summary=body,
                cached_summary_lang=key,
            )

        body_trunc = body
        summary_text = ""
        for _ in range(4):
            summary_text = (
                f"<b>{t(locale, 'summary')}</b>\n"
                + format_summary_html(body_trunc)
                + commands_footer(locale)
            )
            if len(summary_text) <= 4096:
                break
            body_trunc = trunc(body_trunc, max(500, len(body_trunc) * 2 // 3))

        try:
            await query.edit_message_text(
                summary_text,
                parse_mode="HTML",
                reply_markup=summary_keyboard(link, locale),
            )
        except Exception:
            await query.message.reply_text(
                summary_text,
                parse_mode="HTML",
                reply_markup=summary_keyboard(link, locale),
            )
        return

    await query.answer()
