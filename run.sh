#!/usr/bin/env bash
# Запуск бота: создаёт .venv при первом запуске и ставит зависимости.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo ">>> Создаю виртуальное окружение .venv ..."
  python3 -m venv .venv
  # shellcheck source=/dev/null
  source .venv/bin/activate
  echo ">>> Ставлю зависимости (один раз при создании .venv) ..."
  python -m pip install -q --upgrade pip
  python -m pip install -q -r requirements.txt
else
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

if [[ ! -f .env ]]; then
  echo ""
  echo "!!! Файл .env не найден. Скопируйте .env.example в .env и заполните ключи:"
  echo "    cp .env.example .env"
  echo ""
  exit 1
fi

echo ">>> Запуск бота..."
exec python -u main.py
