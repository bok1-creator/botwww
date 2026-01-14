@echo off
chcp 65001 >nul
echo ============================================================
echo ЗАГРУЗКА ПРОЕКТА НА GITHUB
echo ============================================================
echo.
echo Репозиторий: https://github.com/bok1-creator/botwww
echo.
pause

echo.
echo [1/6] Настройка Git...
git config --global user.name "bok1-creator"
git config --global user.email "bot@example.com"

echo.
echo [2/6] Инициализация репозитория...
git init

echo.
echo [3/6] Добавление файлов...
git add .

echo.
echo [4/6] Создание коммита...
git commit -m "Initial commit - Telegram Bot Admin Panel"

echo.
echo [5/6] Подключение к GitHub...
git remote add origin https://github.com/bok1-creator/botwww.git

echo.
echo [6/6] Отправка кода на GitHub...
echo.
echo ВАЖНО: Сейчас попросит авторизацию!
echo Username: bok1-creator
echo Password: используй Personal Access Token (не обычный пароль!)
echo.
echo Как получить токен:
echo 1. GitHub.com - Settings - Developer settings
echo 2. Personal access tokens - Generate new token
echo 3. Выбери: repo (все галочки)
echo 4. Скопируй токен и вставь вместо пароля
echo.
pause

git branch -M main
git push -u origin main

echo.
echo ============================================================
if %errorlevel% equ 0 (
    echo УСПЕШНО! Код загружен на GitHub
    echo.
    echo Проверь: https://github.com/bok1-creator/botwww
    echo.
    echo СЛЕДУЮЩИЙ ШАГ: Развертывание на Render.com
    echo 1. Иди на https://render.com
    echo 2. Войди через GitHub
    echo 3. New + - Web Service
    echo 4. Выбери репозиторий: bok1-creator/botwww
    echo 5. Build Command: pip install -r requirements_deploy.txt
    echo 6. Start Command: gunicorn app:app
    echo 7. Create Web Service
    echo.
) else (
    echo ОШИБКА! Не удалось загрузить код
    echo.
    echo Возможные причины:
    echo 1. Неправильный токен - получи новый на GitHub
    echo 2. Репозиторий не существует - создай на GitHub
    echo 3. Нет интернета - проверь подключение
    echo.
)
echo ============================================================
pause