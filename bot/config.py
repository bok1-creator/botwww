import os

# Конфигурация бота
BOT_TOKEN = "8222569014:AAEDljGGBuMWdMc8oZ9wXMrz-AEVL_qC_Po"

# Настройки базы данных
DATABASE_PATH = "data/bot.db"

# Настройки веб-сервера
WEB_HOST = "0.0.0.0"
WEB_PORT = 3000

# Настройки напоминаний (в минутах)
REMINDER_INTERVAL = 15

# Папка для загрузок
UPLOAD_FOLDER = "static/uploads"

# Создаем необходимые папки
os.makedirs("data", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)