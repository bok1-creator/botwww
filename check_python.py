#!/usr/bin/env python3
"""
Простая проверка системы для Python версии бота
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print(f"🐍 Python версия: {sys.version}")
    
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше!")
        return False
    else:
        print("✅ Версия Python подходит")
        return True

def check_files():
    """Проверка наличия файлов"""
    required_files = [
        'main.py',
        'requirements.txt',
        'bot/config.py',
        'bot/database.py',
        'bot/handlers.py',
        'bot/bot_main.py',
        'web/app.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} не найден")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_directories():
    """Проверка наличия папок"""
    required_dirs = [
        'bot',
        'web', 
        'data',
        'static',
        'static/uploads'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Папка {dir_path}")
        else:
            print(f"❌ Папка {dir_path} не найдена")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Создана папка {dir_path}")
            except Exception as e:
                print(f"❌ Ошибка создания {dir_path}: {e}")

def check_dependencies():
    """Проверка установленных зависимостей"""
    required_packages = [
        'aiogram',
        'aiohttp', 
        'aiosqlite',
        'flask',
        'flask_cors'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} не установлен")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Для установки зависимостей выполните:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Главная функция проверки"""
    print("🔍 Проверка системы для Telegram Bot Constructor (Python)\n")
    
    # Проверяем Python
    python_ok = check_python_version()
    print()
    
    # Проверяем файлы
    print("📁 Проверка файлов:")
    files_ok = check_files()
    print()
    
    # Проверяем папки
    print("📂 Проверка папок:")
    check_directories()
    print()
    
    # Проверяем зависимости
    print("📦 Проверка зависимостей:")
    deps_ok = check_dependencies()
    print()
    
    # Итоговый результат
    if python_ok and files_ok and deps_ok:
        print("🎉 Система готова к запуску!")
        print("\n📋 Следующие шаги:")
        print("1. python main.py")
        print("2. Откройте http://localhost:3000")
        print("3. Найдите бота в Telegram и отправьте /start")
    else:
        print("⚠️ Есть проблемы, которые нужно исправить")
        
        if not python_ok:
            print("- Обновите Python до версии 3.8+")
        if not files_ok:
            print("- Проверьте, что все файлы на месте")
        if not deps_ok:
            print("- Установите зависимости: pip install -r requirements.txt")

if __name__ == "__main__":
    main()