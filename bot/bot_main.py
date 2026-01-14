import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import BOT_TOKEN, DATABASE_PATH
from bot.database import Database
from bot.handlers import router, send_reminder

# Глобальные переменные
bot = None
scheduler = None

async def check_reminders():
    """Проверка и отправка напоминаний"""
    if not bot:
        return
        
    db = Database(DATABASE_PATH)
    users = await db.get_users_for_reminder()
    
    for user in users:
        await send_reminder(user['telegram_id'], bot)

async def start_bot():
    """Запуск бота"""
    global bot, scheduler
    
    # Инициализация бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Инициализация диспетчера
    dp = Dispatcher()
    dp.include_router(router)
    
    # Инициализация базы данных
    db = Database(DATABASE_PATH)
    await db.init_db()
    
    # Настройка планировщика для напоминаний
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_reminders,
        'interval',
        minutes=5,  # Проверяем каждые 5 минут
        id='reminder_check'
    )
    scheduler.start()
    
    print("🤖 Telegram бот запущен!")
    print(f"📱 Bot username: @{(await bot.get_me()).username}")
    
    try:
        # Запуск бота
        await dp.start_polling(bot)
    finally:
        if scheduler:
            scheduler.shutdown()
        await bot.session.close()

# Функция для отправки сообщения из веб-интерфейса
async def send_message_to_user(telegram_id: int, message_text: str):
    """Отправка сообщения пользователю из админки"""
    if bot:
        try:
            await bot.send_message(telegram_id, message_text)
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False
    return False