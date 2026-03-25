import os
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import handlers

load_dotenv()


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Справка и команды"),
            BotCommand("help", "Справка и команды"),
            BotCommand("random", "Случайная непрочитанная ссылка"),
            BotCommand("list", "Пять случайных непрочитанных"),
        ]
    )


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", handlers.cmd_help))
    app.add_handler(CommandHandler("help", handlers.cmd_help))
    app.add_handler(CommandHandler("random", handlers.cmd_random))
    app.add_handler(CommandHandler("list", handlers.cmd_list))
    app.add_handler(CallbackQueryHandler(handlers.handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
