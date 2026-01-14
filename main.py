import asyncio
import logging
from threading import Thread
from bot.bot_main import start_bot
from web.app import create_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_web_app():
    """Запуск веб-приложения в отдельном потоке"""
    app = create_app()
    app.run(host='0.0.0.0', port=3000, debug=False)

async def main():
    """Главная функция запуска"""
    print("🚀 Запуск Telegram Bot Constructor...")
    
    # Запускаем веб-приложение в отдельном потоке
    web_thread = Thread(target=run_web_app, daemon=True)
    web_thread.start()
    
    print("🌐 Веб-админка запущена: http://localhost:3000")
    
    # Запускаем бота
    await start_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")