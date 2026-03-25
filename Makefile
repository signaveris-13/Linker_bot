# Удобные цели для тех, кто привык к make
.PHONY: setup run

setup:
	python3 -m venv .venv
	./.venv/bin/python -m pip install --upgrade pip
	./.venv/bin/python -m pip install -r requirements.txt
	@echo "Готово. Скопируйте .env.example в .env и заполните ключи, затем: make run"

run:
	@test -d .venv || (echo "Сначала: make setup" && exit 1)
	@test -f .env || (echo "Нужен файл .env (см. .env.example)" && exit 1)
	./.venv/bin/python -u main.py
