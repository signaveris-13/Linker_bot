# Linker_bot

Telegram-бот для сохранения ссылок (Supabase + Anthropic).

## Быстрый старт (macOS / Linux)

Из папки проекта выполни **одну** команду:

```bash
chmod +x run.sh   # только первый раз
./run.sh
```

Скрипт сам:

1. создаст виртуальное окружение `.venv` (если его ещё нет) и **один раз** установит зависимости из `requirements.txt` (так обходится ошибка *externally-managed-environment* у Homebrew Python);
2. при следующих запусках только активирует `.venv`;
3. проверит наличие `.env`;
4. запустит `main.py`.

Если обновишь `requirements.txt`, поставь пакеты заново:

```bash
source .venv/bin/activate && pip install -r requirements.txt
```

На macOS команда `python` в системе может отсутствовать — скрипт использует `python3` для создания venv и `python` из `.venv` для запуска.

## Ручная установка

```bash
cd ~/Development/Linker_bot
cp .env.example .env
# отредактируй .env: TELEGRAM_BOT_TOKEN, SUPABASE_*, ANTHROPIC_API_KEY

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Каждый новый терминал: `cd .../Linker_bot && source .venv/bin/activate`, затем `python main.py`.

## Переменные окружения

См. `.env.example`. Файл `.env` в репозиторий не коммитится (указан в `.gitignore`).

## База (Supabase)

SQL-миграции лежат в `supabase/migrations/`.
