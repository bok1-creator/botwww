#!/usr/bin/env bash
# Обновляем pip
python -m pip install --upgrade pip setuptools wheel

# Устанавливаем зависимости без компиляции
pip install --no-cache-dir aiogram flask flask-cors APScheduler requests aiosqlite gunicorn