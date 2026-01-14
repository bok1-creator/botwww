import os

# Конфигурация бота
BOT_TOKEN = "8299699398:AAEFKo5SkoOfOYpK-xJ4t-ZJ3ho9YA7NSxc"

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