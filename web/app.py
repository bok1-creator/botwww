import os
import json
import asyncio
from flask import Flask, request, jsonify, render_template_string, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from functools import wraps
from bot.database import Database
from bot.config import DATABASE_PATH, UPLOAD_FOLDER
from bot.bot_main import send_message_to_user

# Данные для входа (в реальном проекте лучше хранить в базе с хешированием)
ADMIN_CREDENTIALS = {
    'username': 'botadmin',
    'password': 'TgBot2026!'
}

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Секретный ключ для сессий
    app.secret_key = 'your-secret-key-change-in-production-2026'
    
    # Настройки загрузки файлов
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    db = Database(DATABASE_PATH)
    
    # Декоратор для проверки авторизации
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    # Страница входа
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if (username == ADMIN_CREDENTIALS['username'] and 
                password == ADMIN_CREDENTIALS['password']):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template_string(LOGIN_TEMPLATE, error='Неверный логин или пароль')
        
        return render_template_string(LOGIN_TEMPLATE)
    
    # Выход
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
    
    # Главная страница (защищена авторизацией)
    @app.route('/')
    @login_required
    def index():
        return render_template_string(ADMIN_HTML_TEMPLATE)
    
    # API для получения настроек
    @app.route('/api/settings', methods=['GET'])
    @login_required
    def get_settings():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            settings = loop.run_until_complete(db.get_settings())
            loop.close()
            return jsonify(settings or {})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для обновления настроек
    @app.route('/api/settings', methods=['POST'])
    @login_required
    def update_settings():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(db.update_settings(request.json))
            loop.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для получения вопросов
    @app.route('/api/questions', methods=['GET'])
    @login_required
    def get_questions():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            questions = loop.run_until_complete(db.get_questions())
            loop.close()
            return jsonify(questions)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для обновления вопроса
    @app.route('/api/questions/<int:question_id>', methods=['PUT'])
    @login_required
    def update_question(question_id):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(db.update_question(question_id, request.json))
            loop.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для добавления нового вопроса
    @app.route('/api/questions', methods=['POST'])
    @login_required
    def add_question():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(db.add_question(request.json))
            loop.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для удаления вопроса
    @app.route('/api/questions/<int:question_id>', methods=['DELETE'])
    @login_required
    def delete_question(question_id):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(db.delete_question(question_id))
            loop.close()
            
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Вопрос не найден'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для изменения порядка вопросов
    @app.route('/api/questions/reorder', methods=['POST'])
    @login_required
    def reorder_questions():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(db.reorder_questions(request.json))
            loop.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для получения пользователей
    @app.route('/api/users', methods=['GET'])
    @login_required
    def get_users():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            users = loop.run_until_complete(db.get_all_users())
            loop.close()
            return jsonify(users)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для удаления пользователя
    @app.route('/api/users/<int:telegram_id>', methods=['DELETE'])
    @login_required
    def delete_user(telegram_id):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(db.delete_user(telegram_id))
            loop.close()
            
            if success:
                return jsonify({'success': True, 'message': 'Пользователь удален'})
            else:
                return jsonify({'error': 'Пользователь не найден'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для получения истории чата
    @app.route('/api/chat/<int:telegram_id>', methods=['GET'])
    @login_required
    def get_chat_history(telegram_id):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            messages = loop.run_until_complete(db.get_chat_history(telegram_id))
            loop.close()
            return jsonify(messages)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API для отправки сообщения пользователю
    @app.route('/api/chat/<int:telegram_id>', methods=['POST'])
    @login_required
    def send_message(telegram_id):
        try:
            message_text = request.json.get('message', '')
            
            # Отправляем сообщение через бота
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(send_message_to_user(telegram_id, message_text))
            
            if success:
                # Сохраняем в базу
                loop.run_until_complete(db.add_chat_message(telegram_id, message_text, True))
            
            loop.close()
            
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Не удалось отправить сообщение'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Загрузка видео
    @app.route('/api/upload-video', methods=['POST'])
    @login_required
    def upload_video():
        try:
            if 'video' not in request.files:
                return jsonify({'error': 'Файл не найден'}), 400
            
            file = request.files['video']
            if file.filename == '':
                return jsonify({'error': 'Файл не выбран'}), 400
            
            if file:
                filename = secure_filename(file.filename)
                # Добавляем timestamp к имени файла
                import time
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(time.time())}{ext}"
                
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                return jsonify({'videoPath': f'/uploads/{filename}'})
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Статические файлы (загруженные видео)
    @app.route('/uploads/<filename>')
    @login_required
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # API для получения ответов пользователя
    @app.route('/api/user/<int:telegram_id>/answers', methods=['GET'])
    @login_required
    def get_user_answers(telegram_id):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            user = loop.run_until_complete(db.get_user(telegram_id))
            loop.close()
            
            if user:
                answers = []
                if user['answers']:
                    try:
                        answers = json.loads(user['answers'])
                    except:
                        answers = []
                
                return jsonify({
                    'user_info': {
                        'telegram_id': user['telegram_id'],
                        'first_name': user['first_name'],
                        'username': user['username'],
                        'current_step': user['current_step'],
                        'created_at': user['created_at']
                    },
                    'answers': answers,
                    'text_input': user['text_input']
                })
            else:
                return jsonify({'error': 'Пользователь не найден'}), 404
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # API для синхронизации с AmoCRM
    @app.route('/api/amocrm/sync/<int:telegram_id>', methods=['POST'])
    @login_required
    def sync_amocrm(telegram_id):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            user = loop.run_until_complete(db.get_user(telegram_id))
            loop.close()
            
            if user:
                # Здесь будет интеграция с AmoCRM
                lead_data = {
                    'name': user['first_name'],
                    'telegram_id': user['telegram_id'],
                    'answers': user['answers'],
                    'text_input': user['text_input']
                }
                
                print(f"Синхронизация с AmoCRM: {lead_data}")
                return jsonify({'success': True, 'data': lead_data})
            else:
                return jsonify({'error': 'Пользователь не найден'}), 404
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

# HTML шаблон для страницы входа
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в админ-панель</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            padding: 2rem;
            width: 100%;
            max-width: 400px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header i {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 1rem;
        }
        .btn-login {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            color: white;
        }
        .form-control {
            border-radius: 8px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .alert {
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="login-header">
            <i class="fas fa-robot"></i>
            <h3>Админ-панель бота</h3>
            <p class="text-muted">Введите данные для входа</p>
        </div>
        
        {% if error %}
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>{{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">
                    <i class="fas fa-user me-2"></i>Логин
                </label>
                <input type="text" class="form-control" name="username" required 
                       placeholder="Введите логин">
            </div>
            
            <div class="mb-4">
                <label class="form-label">
                    <i class="fas fa-lock me-2"></i>Пароль
                </label>
                <input type="password" class="form-control" name="password" required 
                       placeholder="Введите пароль">
            </div>
            
            <button type="submit" class="btn btn-login">
                <i class="fas fa-sign-in-alt me-2"></i>Войти
            </button>
        </form>
        
        <div class="text-center mt-4">
            <small class="text-muted">
                <i class="fas fa-shield-alt me-1"></i>
                Защищенная зона администратора
            </small>
        </div>
    </div>
</body>
</html>
'''

# HTML шаблон для админ-панели
ADMIN_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель Telegram Bot</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .sidebar {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .nav-link {
            color: rgba(255,255,255,0.8) !important;
            border-radius: 8px;
            margin: 2px 0;
        }
        .nav-link:hover, .nav-link.active {
            background: rgba(255,255,255,0.2);
            color: white !important;
        }
        .card {
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 12px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        .chat-message {
            max-width: 70%;
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 18px;
        }
        .chat-message.user {
            background: #e3f2fd;
            margin-left: auto;
        }
        .chat-message.admin {
            background: #f3e5f5;
        }
        .video-preview {
            max-width: 200px;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 sidebar p-3">
                <h4 class="text-white mb-4">
                    <i class="fas fa-robot me-2"></i>
                    Bot Admin
                </h4>
                <nav class="nav flex-column">
                    <a class="nav-link active" href="#" onclick="showSection('settings')">
                        <i class="fas fa-cog me-2"></i>Настройки
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('questions')">
                        <i class="fas fa-question-circle me-2"></i>Вопросы
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('users')">
                        <i class="fas fa-users me-2"></i>Пользователи
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('chat')">
                        <i class="fas fa-comments me-2"></i>Чаты
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('amocrm')">
                        <i class="fas fa-sync me-2"></i>AmoCRM
                    </a>
                </nav>
                
                <div class="mt-auto pt-4">
                    <hr class="text-white-50">
                    <a href="/logout" class="nav-link text-white-50">
                        <i class="fas fa-sign-out-alt me-2"></i>Выйти
                    </a>
                </div>
            </div>

            <!-- Main content -->
            <div class="col-md-9 col-lg-10 p-4">
                <!-- Настройки -->
                <div id="settings-section" class="section">
                    <h2><i class="fas fa-cog me-2"></i>Настройки бота</h2>
                    <div class="row">
                        <div class="col-lg-8">
                            <div class="card">
                                <div class="card-body">
                                    <form id="settings-form">
                                        <div class="mb-3">
                                            <label class="form-label">Приветственное видео</label>
                                            <input type="file" class="form-control" id="welcome-video" accept="video/*">
                                            <div id="video-preview" class="mt-2"></div>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Текст приветствия</label>
                                            <textarea class="form-control" id="welcome-text" rows="3"></textarea>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Текст напоминания</label>
                                            <textarea class="form-control" id="reminder-text" rows="2"></textarea>
                                        </div>
                                        <button type="submit" class="btn btn-primary">
                                            <i class="fas fa-save me-2"></i>Сохранить
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Вопросы -->
                <div id="questions-section" class="section" style="display: none;">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2><i class="fas fa-question-circle me-2"></i>Управление вопросами</h2>
                        <button class="btn btn-success" onclick="addNewQuestion()">
                            <i class="fas fa-plus me-2"></i>Добавить вопрос
                        </button>
                    </div>
                    
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Совет:</strong> Вы можете добавлять неограниченное количество вопросов. 
                        Бот автоматически адаптируется к новому количеству вопросов.
                    </div>
                    
                    <div id="questions-container"></div>
                </div>

                <!-- Пользователи -->
                <div id="users-section" class="section" style="display: none;">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2><i class="fas fa-users me-2"></i>Пользователи</h2>
                        <div>
                            <button class="btn btn-danger" id="delete-selected-btn" onclick="deleteSelectedUsers()" style="display: none;">
                                <i class="fas fa-trash me-2"></i>Удалить выбранные (<span id="selected-count">0</span>)
                            </button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table" id="users-table">
                                    <thead>
                                        <tr>
                                            <th>
                                                <input type="checkbox" id="select-all-users" onchange="toggleSelectAll()">
                                            </th>
                                            <th>ID</th>
                                            <th>Имя</th>
                                            <th>Username</th>
                                            <th>Этап</th>
                                            <th>Дата</th>
                                            <th>Действия</th>
                                        </tr>
                                    </thead>
                                    <tbody></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Чат -->
                <div id="chat-section" class="section" style="display: none;">
                    <h2><i class="fas fa-comments me-2"></i>Чат с пользователями</h2>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">Выберите пользователя</div>
                                <div class="card-body">
                                    <div id="chat-users-list"></div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header">
                                    <span id="chat-user-name">Выберите пользователя</span>
                                </div>
                                <div class="card-body">
                                    <div id="chat-messages" style="height: 400px; overflow-y: auto;"></div>
                                    <div class="mt-3">
                                        <div class="input-group">
                                            <input type="text" class="form-control" id="chat-input" placeholder="Введите сообщение...">
                                            <button class="btn btn-primary" onclick="sendMessage()">
                                                <i class="fas fa-paper-plane"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AmoCRM -->
                <div id="amocrm-section" class="section" style="display: none;">
                    <h2><i class="fas fa-sync me-2"></i>Интеграция с AmoCRM</h2>
                    <div class="card">
                        <div class="card-body">
                            <p>Здесь будут настройки интеграции с AmoCRM</p>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                Функция в разработке. Скоро будет доступна синхронизация лидов.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Модальное окно для просмотра ответов -->
    <div class="modal fade" id="answersModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-user me-2"></i>
                        Ответы пользователя: <span id="modal-user-name"></span>
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="user-answers-content">
                        <div class="text-center">
                            <div class="spinner-border" role="status">
                                <span class="visually-hidden">Загрузка...</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                    <button type="button" class="btn btn-primary" onclick="openChatFromModal()">
                        <i class="fas fa-comments me-2"></i>Открыть чат
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentChatUser = null;
        let currentModalUser = null;

        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            loadSettings();
            loadQuestions();
            loadUsers();
            
            // Обработчик формы настроек
            document.getElementById('settings-form').addEventListener('submit', saveSettings);
            
            // Обработчик загрузки видео
            document.getElementById('welcome-video').addEventListener('change', handleVideoUpload);
        });

        // Переключение разделов
        function showSection(sectionName) {
            // Скрываем все разделы
            document.querySelectorAll('.section').forEach(section => {
                section.style.display = 'none';
            });
            
            // Показываем выбранный раздел
            document.getElementById(sectionName + '-section').style.display = 'block';
            
            // Обновляем активную ссылку
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Загружаем данные для раздела
            if (sectionName === 'users') {
                loadUsers();
            } else if (sectionName === 'chat') {
                loadChatUsers();
            }
        }

        // Загрузка настроек
        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                const settings = await response.json();
                
                document.getElementById('welcome-text').value = settings.welcome_text || '';
                document.getElementById('reminder-text').value = settings.reminder_text || '';
                
                if (settings.welcome_video) {
                    showVideoPreview(settings.welcome_video);
                }
            } catch (error) {
                console.error('Ошибка загрузки настроек:', error);
            }
        }

        // Сохранение настроек
        async function saveSettings(event) {
            event.preventDefault();
            
            const settings = {
                welcome_text: document.getElementById('welcome-text').value,
                reminder_text: document.getElementById('reminder-text').value,
                welcome_video: document.getElementById('video-preview').dataset.videoPath || ''
            };
            
            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(settings)
                });
                
                if (response.ok) {
                    showAlert('Настройки сохранены!', 'success');
                }
            } catch (error) {
                showAlert('Ошибка сохранения настроек', 'danger');
            }
        }

        // Обработка загрузки видео
        async function handleVideoUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('video', file);
            
            try {
                const response = await fetch('/api/upload-video', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (response.ok) {
                    showVideoPreview(result.videoPath);
                    showAlert('Видео загружено!', 'success');
                }
            } catch (error) {
                showAlert('Ошибка загрузки видео', 'danger');
            }
        }

        // Показ превью видео
        function showVideoPreview(videoPath) {
            const preview = document.getElementById('video-preview');
            preview.innerHTML = `
                <video class="video-preview" controls>
                    <source src="${videoPath}" type="video/mp4">
                </video>
            `;
            preview.dataset.videoPath = videoPath;
        }

        // Загрузка вопросов
        async function loadQuestions() {
            try {
                const response = await fetch('/api/questions');
                const questions = await response.json();
                
                const container = document.getElementById('questions-container');
                container.innerHTML = '';
                
                questions.forEach((question, index) => {
                    const questionCard = createQuestionCard(question, index + 1);
                    container.appendChild(questionCard);
                });
            } catch (error) {
                console.error('Ошибка загрузки вопросов:', error);
            }
        }

        // Создание карточки вопроса
        function createQuestionCard(question, number) {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            card.dataset.questionId = question.id;
            card.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">Вопрос ${number}</h5>
                    <div>
                        <button class="btn btn-sm btn-outline-secondary me-2" onclick="moveQuestion(${question.id}, 'up')" ${number === 1 ? 'disabled' : ''}>
                            <i class="fas fa-arrow-up"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary me-2" onclick="moveQuestion(${question.id}, 'down')">
                            <i class="fas fa-arrow-down"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteQuestion(${question.id})" ${number <= 1 ? 'disabled title="Нельзя удалить единственный вопрос"' : ''}>
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Текст вопроса</label>
                        <input type="text" class="form-control" value="${question.question_text}" 
                               onchange="updateQuestion(${question.id})">
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <label class="form-label">Вариант 1</label>
                            <input type="text" class="form-control" value="${question.option1}"
                                   onchange="updateQuestion(${question.id})">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Вариант 2</label>
                            <input type="text" class="form-control" value="${question.option2}"
                                   onchange="updateQuestion(${question.id})">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Вариант 3</label>
                            <input type="text" class="form-control" value="${question.option3}"
                                   onchange="updateQuestion(${question.id})">
                        </div>
                    </div>
                </div>
            `;
            return card;
        }

        // Обновление вопроса
        async function updateQuestion(questionId) {
            // Собираем все данные вопроса
            const card = document.querySelector(`[data-question-id="${questionId}"]`);
            if (!card) return;
            
            const questionData = {
                question_text: card.querySelector('input[onchange*="updateQuestion"]').value,
                option1: card.querySelectorAll('.row input')[0].value,
                option2: card.querySelectorAll('.row input')[1].value,
                option3: card.querySelectorAll('.row input')[2].value
            };
            
            try {
                const response = await fetch(`/api/questions/${questionId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(questionData)
                });
                
                if (response.ok) {
                    showAlert('Вопрос обновлен!', 'success');
                }
            } catch (error) {
                showAlert('Ошибка обновления вопроса', 'danger');
            }
        }

        // Добавление нового вопроса
        async function addNewQuestion() {
            const newQuestion = {
                question_text: 'Новый вопрос',
                option1: 'Вариант 1',
                option2: 'Вариант 2',
                option3: 'Вариант 3'
            };
            
            try {
                const response = await fetch('/api/questions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(newQuestion)
                });
                
                if (response.ok) {
                    showAlert('Новый вопрос добавлен!', 'success');
                    loadQuestions(); // Перезагружаем список вопросов
                }
            } catch (error) {
                showAlert('Ошибка добавления вопроса', 'danger');
            }
        }

        // Удаление вопроса
        async function deleteQuestion(questionId) {
            if (!confirm('Вы уверены, что хотите удалить этот вопрос?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/questions/${questionId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    showAlert('Вопрос удален!', 'success');
                    loadQuestions(); // Перезагружаем список вопросов
                } else {
                    const error = await response.json();
                    showAlert('Ошибка: ' + error.error, 'danger');
                }
            } catch (error) {
                showAlert('Ошибка удаления вопроса', 'danger');
            }
        }

        // Перемещение вопроса вверх/вниз
        async function moveQuestion(questionId, direction) {
            // Получаем текущий список вопросов
            try {
                const response = await fetch('/api/questions');
                const questions = await response.json();
                
                const currentIndex = questions.findIndex(q => q.id === questionId);
                if (currentIndex === -1) return;
                
                let newIndex;
                if (direction === 'up' && currentIndex > 0) {
                    newIndex = currentIndex - 1;
                } else if (direction === 'down' && currentIndex < questions.length - 1) {
                    newIndex = currentIndex + 1;
                } else {
                    return; // Нельзя переместить
                }
                
                // Меняем местами
                [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];
                
                // Создаем массив для обновления порядка
                const reorderData = questions.map((q, index) => ({
                    id: q.id,
                    order: index + 1
                }));
                
                const reorderResponse = await fetch('/api/questions/reorder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(reorderData)
                });
                
                if (reorderResponse.ok) {
                    showAlert('Порядок вопросов изменен!', 'success');
                    loadQuestions(); // Перезагружаем список
                }
                
            } catch (error) {
                showAlert('Ошибка изменения порядка', 'danger');
            }
        }

        // Загрузка пользователей
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const users = await response.json();
                
                const tbody = document.querySelector('#users-table tbody');
                tbody.innerHTML = '';
                
                users.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <input type="checkbox" class="user-checkbox" value="${user.telegram_id}" onchange="updateSelectedCount()">
                        </td>
                        <td>${user.telegram_id}</td>
                        <td>${user.first_name || 'Не указано'}</td>
                        <td>@${user.username || 'Не указано'}</td>
                        <td>${getStepName(user.current_step)}</td>
                        <td>${new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-info me-1" onclick="viewUserAnswers(${user.telegram_id})" title="Просмотр ответов">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary me-1" onclick="openChat(${user.telegram_id}, '${user.first_name}')" title="Открыть чат">
                                <i class="fas fa-comments"></i>
                            </button>
                            <button class="btn btn-sm btn-success me-1" onclick="syncWithAmoCRM(${user.telegram_id})" title="Синхронизация с AmoCRM">
                                <i class="fas fa-sync"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.telegram_id}, '${user.first_name}')" title="Удалить пользователя">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                
                // Сбрасываем выбор
                document.getElementById('select-all-users').checked = false;
                updateSelectedCount();
                
            } catch (error) {
                console.error('Ошибка загрузки пользователей:', error);
            }
        }

        // Переключение выбора всех пользователей
        function toggleSelectAll() {
            const selectAll = document.getElementById('select-all-users');
            const checkboxes = document.querySelectorAll('.user-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAll.checked;
            });
            
            updateSelectedCount();
        }

        // Обновление счетчика выбранных пользователей
        function updateSelectedCount() {
            const checkboxes = document.querySelectorAll('.user-checkbox:checked');
            const count = checkboxes.length;
            
            document.getElementById('selected-count').textContent = count;
            
            const deleteBtn = document.getElementById('delete-selected-btn');
            if (count > 0) {
                deleteBtn.style.display = 'inline-block';
            } else {
                deleteBtn.style.display = 'none';
            }
        }

        // Удаление выбранных пользователей
        async function deleteSelectedUsers() {
            const checkboxes = document.querySelectorAll('.user-checkbox:checked');
            const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
            
            if (selectedIds.length === 0) {
                return;
            }
            
            const confirmMessage = `Вы уверены, что хотите удалить ${selectedIds.length} пользователей?\n\nБудут удалены все их данные:\n- Ответы на вопросы\n- Текстовый ввод\n- История чата\n\nЭто действие нельзя отменить!`;
            
            if (!confirm(confirmMessage)) {
                return;
            }
            
            let successCount = 0;
            let errorCount = 0;
            
            // Показываем прогресс
            showAlert(`Удаление ${selectedIds.length} пользователей...`, 'info');
            
            for (const telegramId of selectedIds) {
                try {
                    const response = await fetch(`/api/users/${telegramId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        successCount++;
                    } else {
                        errorCount++;
                    }
                } catch (error) {
                    errorCount++;
                    console.error(`Ошибка удаления пользователя ${telegramId}:`, error);
                }
            }
            
            // Показываем результат
            if (errorCount === 0) {
                showAlert(`Успешно удалено ${successCount} пользователей!`, 'success');
            } else {
                showAlert(`Удалено: ${successCount}, Ошибок: ${errorCount}`, 'warning');
            }
            
            // Перезагружаем список
            loadUsers();
        }

        // Получение названия этапа
        function getStepName(step) {
            if (step === 0) return 'Новый';
            
            // Получаем количество вопросов из загруженных данных
            const questionsCount = document.querySelectorAll('#questions-container .card').length || 3;
            
            if (step >= 1 && step <= questionsCount) {
                return `Вопрос ${step}`;
            } else if (step === questionsCount + 1) {
                return 'Текстовый ввод';
            } else if (step >= questionsCount + 2) {
                return 'Завершен';
            }
            
            return 'Неизвестно';
        }

        // Загрузка пользователей для чата
        async function loadChatUsers() {
            try {
                const response = await fetch('/api/users');
                const users = await response.json();
                
                // Получаем количество вопросов
                const questionsResponse = await fetch('/api/questions');
                const questions = await questionsResponse.json();
                const completedStep = questions.length + 2;
                
                const container = document.getElementById('chat-users-list');
                container.innerHTML = '';
                
                users.filter(user => user.current_step >= completedStep).forEach(user => {
                    const userItem = document.createElement('div');
                    userItem.className = 'list-group-item list-group-item-action';
                    userItem.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${user.first_name || 'Пользователь'}</h6>
                            <small>@${user.username || 'Нет username'}</small>
                        </div>
                    `;
                    userItem.onclick = () => openChat(user.telegram_id, user.first_name);
                    container.appendChild(userItem);
                });
            } catch (error) {
                console.error('Ошибка загрузки пользователей чата:', error);
            }
        }

        // Открытие чата с пользователем
        async function openChat(telegramId, firstName) {
            currentChatUser = telegramId;
            document.getElementById('chat-user-name').textContent = firstName || 'Пользователь';
            
            // Переключаемся на раздел чата
            showSection('chat');
            
            // Загружаем историю сообщений
            try {
                const response = await fetch(`/api/chat/${telegramId}`);
                const messages = await response.json();
                
                const container = document.getElementById('chat-messages');
                container.innerHTML = '';
                
                messages.forEach(message => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `chat-message ${message.from_admin ? 'admin' : 'user'}`;
                    messageDiv.innerHTML = `
                        <div>${message.message_text}</div>
                        <small class="text-muted">${new Date(message.created_at).toLocaleString()}</small>
                    `;
                    container.appendChild(messageDiv);
                });
                
                container.scrollTop = container.scrollHeight;
            } catch (error) {
                console.error('Ошибка загрузки чата:', error);
            }
        }

        // Отправка сообщения
        async function sendMessage() {
            if (!currentChatUser) return;
            
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;
            
            try {
                const response = await fetch(`/api/chat/${currentChatUser}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });
                
                if (response.ok) {
                    input.value = '';
                    // Обновляем чат
                    openChat(currentChatUser, document.getElementById('chat-user-name').textContent);
                }
            } catch (error) {
                showAlert('Ошибка отправки сообщения', 'danger');
            }
        }

        // Просмотр ответов пользователя
        async function viewUserAnswers(telegramId) {
            currentModalUser = telegramId;
            
            try {
                const response = await fetch(`/api/user/${telegramId}/answers`);
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('modal-user-name').textContent = 
                        data.user_info.first_name || 'Пользователь';
                    
                    const content = document.getElementById('user-answers-content');
                    content.innerHTML = '';
                    
                    // Информация о пользователе
                    const userInfo = document.createElement('div');
                    userInfo.className = 'card mb-3';
                    userInfo.innerHTML = `
                        <div class="card-header">
                            <h6 class="mb-0">Информация о пользователе</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>Имя:</strong> ${data.user_info.first_name || 'Не указано'}<br>
                                    <strong>Username:</strong> @${data.user_info.username || 'Не указано'}<br>
                                </div>
                                <div class="col-md-6">
                                    <strong>Telegram ID:</strong> ${data.user_info.telegram_id}<br>
                                    <strong>Этап:</strong> ${getStepName(data.user_info.current_step)}<br>
                                </div>
                            </div>
                            <div class="mt-2">
                                <strong>Дата регистрации:</strong> ${new Date(data.user_info.created_at).toLocaleString()}
                            </div>
                        </div>
                    `;
                    content.appendChild(userInfo);
                    
                    // Ответы на вопросы
                    if (data.answers && data.answers.length > 0) {
                        const answersCard = document.createElement('div');
                        answersCard.className = 'card mb-3';
                        answersCard.innerHTML = `
                            <div class="card-header">
                                <h6 class="mb-0">Ответы на вопросы</h6>
                            </div>
                            <div class="card-body">
                                ${data.answers.map((answer, index) => `
                                    <div class="mb-3 p-3 bg-light rounded">
                                        <strong>Вопрос ${index + 1}:</strong> ${answer.question}<br>
                                        <strong>Ответ:</strong> <span class="text-primary">${answer.answer}</span>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                        content.appendChild(answersCard);
                    }
                    
                    // Текстовый ввод
                    if (data.text_input) {
                        const textCard = document.createElement('div');
                        textCard.className = 'card mb-3';
                        textCard.innerHTML = `
                            <div class="card-header">
                                <h6 class="mb-0">Текстовое сообщение</h6>
                            </div>
                            <div class="card-body">
                                <div class="p-3 bg-light rounded">
                                    ${data.text_input}
                                </div>
                            </div>
                        `;
                        content.appendChild(textCard);
                    }
                    
                    // Если нет данных
                    if ((!data.answers || data.answers.length === 0) && !data.text_input) {
                        content.innerHTML = `
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                Пользователь еще не ответил на вопросы
                            </div>
                        `;
                    }
                    
                    // Показываем модальное окно
                    const modal = new bootstrap.Modal(document.getElementById('answersModal'));
                    modal.show();
                    
                } else {
                    showAlert('Ошибка загрузки ответов: ' + data.error, 'danger');
                }
            } catch (error) {
                showAlert('Ошибка загрузки ответов', 'danger');
                console.error('Ошибка:', error);
            }
        }

        // Открыть чат из модального окна
        function openChatFromModal() {
            if (currentModalUser) {
                const userName = document.getElementById('modal-user-name').textContent;
                
                // Закрываем модальное окно
                const modal = bootstrap.Modal.getInstance(document.getElementById('answersModal'));
                modal.hide();
                
                // Открываем чат
                openChat(currentModalUser, userName);
            }
        }

        // Удаление пользователя
        async function deleteUser(telegramId, userName) {
            // Подтверждение удаления
            const confirmMessage = `Вы уверены, что хотите удалить пользователя "${userName || 'Пользователь'}"?\n\nБудут удалены:\n- Все ответы на вопросы\n- Текстовый ввод\n- История чата\n\nЭто действие нельзя отменить!`;
            
            if (!confirm(confirmMessage)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/users/${telegramId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert('Пользователь успешно удален!', 'success');
                    // Перезагружаем список пользователей
                    loadUsers();
                } else {
                    showAlert('Ошибка: ' + result.error, 'danger');
                }
            } catch (error) {
                showAlert('Ошибка удаления пользователя', 'danger');
                console.error('Ошибка:', error);
            }
        }

        // Синхронизация с AmoCRM
        async function syncWithAmoCRM(telegramId) {
            try {
                const response = await fetch(`/api/amocrm/sync/${telegramId}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    showAlert('Данные синхронизированы с AmoCRM!', 'success');
                }
            } catch (error) {
                showAlert('Ошибка синхронизации с AmoCRM', 'danger');
            }
        }

        // Показ уведомлений
        function showAlert(message, type) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            alert.style.top = '20px';
            alert.style.right = '20px';
            alert.style.zIndex = '9999';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(alert);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }

        // Обработчик Enter в чате
        document.addEventListener('keypress', function(event) {
            if (event.target.id === 'chat-input' && event.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
'''