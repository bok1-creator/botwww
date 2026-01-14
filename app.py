#!/usr/bin/env python3
"""
Основной файл для развертывания на хостинге
"""

import os
import asyncio
import threading
import time
from web.app import create_app
from bot.bot_main import start_bot

# Создаем Flask приложение
app = create_app()

def run_bot():
    """Запуск бота в отдельном потоке"""
    try:
        # Небольшая задержка для инициализации веб-сервера
        time.sleep(5)
        print("🤖 Запуск Telegram бота...")
        asyncio.run(start_bot())
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

def setup_environment():
    """Настройка окружения при первом запуске"""
    try:
        from setup_deploy import setup_deployment
        asyncio.run(setup_deployment())
    except Exception as e:
        print(f"⚠️ Ошибка настройки окружения: {e}")

if __name__ == "__main__":
    print("🚀 Запуск Telegram Bot Constructor...")
    
    # Настройка окружения
    setup_environment()
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-приложение
    port = int(os.environ.get("PORT", 3000))
    print(f"🌐 Веб-сервер запускается на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
else:
    # Для gunicorn
    setup_environment()
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()