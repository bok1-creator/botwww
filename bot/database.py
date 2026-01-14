import aiosqlite
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица настроек бота
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY,
                    welcome_video TEXT,
                    welcome_text TEXT,
                    reminder_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица вопросов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    option1 TEXT NOT NULL,
                    option2 TEXT NOT NULL,
                    option3 TEXT NOT NULL,
                    order_num INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    current_step INTEGER DEFAULT 0,
                    answers TEXT,
                    text_input TEXT,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица сообщений чата
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY,
                    user_telegram_id INTEGER,
                    message_text TEXT,
                    from_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            await self._init_default_data(db)
    
    async def _init_default_data(self, db):
        """Инициализация данных по умолчанию"""
        # Проверяем настройки
        cursor = await db.execute("SELECT COUNT(*) FROM bot_settings")
        count = await cursor.fetchone()
        
        if count[0] == 0:
            await db.execute("""
                INSERT INTO bot_settings (welcome_video, welcome_text, reminder_text)
                VALUES (?, ?, ?)
            """, [
                "",
                "Привет! 👋 Добро пожаловать! Давай знакомиться через несколько вопросов.",
                "Эй, ты забыл ответить! 😊 Продолжим?"
            ])
        
        # Проверяем вопросы
        cursor = await db.execute("SELECT COUNT(*) FROM questions")
        count = await cursor.fetchone()
        
        if count[0] == 0:
            default_questions = [
                ("Какой у тебя опыт работы?", "Новичок", "Средний уровень", "Эксперт", 1),
                ("Что тебя больше всего интересует?", "Технологии", "Бизнес", "Творчество", 2),
                ("Как предпочитаешь работать?", "В команде", "Самостоятельно", "Смешанно", 3)
            ]
            
            for q in default_questions:
                await db.execute("""
                    INSERT INTO questions (question_text, option1, option2, option3, order_num)
                    VALUES (?, ?, ?, ?, ?)
                """, q)
        
        await db.commit()
    
    # Методы для работы с пользователями
    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_or_update_user(self, user_data: Dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users 
                (telegram_id, username, first_name, current_step, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, [
                user_data['telegram_id'],
                user_data.get('username', ''),
                user_data.get('first_name', ''),
                user_data.get('current_step', 0)
            ])
            await db.commit()
    
    async def update_user_step(self, telegram_id: int, step: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET current_step = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE telegram_id = ?
            """, (step, telegram_id))
            await db.commit()
    
    async def update_user_answers(self, telegram_id: int, answers: List[Dict]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET answers = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE telegram_id = ?
            """, (json.dumps(answers, ensure_ascii=False), telegram_id))
            await db.commit()
    
    async def update_user_text_input(self, telegram_id: int, text_input: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET text_input = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE telegram_id = ?
            """, (text_input, telegram_id))
            await db.commit()
    
    # Методы для работы с настройками
    async def get_settings(self) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM bot_settings ORDER BY id DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_settings(self, settings: Dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE bot_settings 
                SET welcome_video = ?, welcome_text = ?, reminder_text = ?
                WHERE id = (SELECT id FROM bot_settings ORDER BY id DESC LIMIT 1)
            """, [
                settings.get('welcome_video', ''),
                settings.get('welcome_text', ''),
                settings.get('reminder_text', '')
            ])
            await db.commit()
    
    # Методы для работы с вопросами
    async def get_questions(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM questions ORDER BY order_num"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_question(self, question_id: int, question_data: Dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE questions 
                SET question_text = ?, option1 = ?, option2 = ?, option3 = ?
                WHERE id = ?
            """, [
                question_data['question_text'],
                question_data['option1'],
                question_data['option2'],
                question_data['option3'],
                question_id
            ])
            await db.commit()
    
    async def add_question(self, question_data: Dict):
        """Добавление нового вопроса"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем максимальный order_num
            cursor = await db.execute("SELECT MAX(order_num) FROM questions")
            max_order = await cursor.fetchone()
            next_order = (max_order[0] or 0) + 1
            
            await db.execute("""
                INSERT INTO questions (question_text, option1, option2, option3, order_num)
                VALUES (?, ?, ?, ?, ?)
            """, [
                question_data['question_text'],
                question_data['option1'],
                question_data['option2'],
                question_data['option3'],
                next_order
            ])
            await db.commit()
    
    async def delete_question(self, question_id: int):
        """Удаление вопроса"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем order_num удаляемого вопроса
            cursor = await db.execute("SELECT order_num FROM questions WHERE id = ?", (question_id,))
            result = await cursor.fetchone()
            
            if result:
                deleted_order = result[0]
                
                # Удаляем вопрос
                await db.execute("DELETE FROM questions WHERE id = ?", (question_id,))
                
                # Обновляем порядковые номера остальных вопросов
                await db.execute("""
                    UPDATE questions 
                    SET order_num = order_num - 1 
                    WHERE order_num > ?
                """, (deleted_order,))
                
                await db.commit()
                return True
            return False
    
    async def reorder_questions(self, question_orders: List[Dict]):
        """Изменение порядка вопросов"""
        async with aiosqlite.connect(self.db_path) as db:
            for item in question_orders:
                await db.execute("""
                    UPDATE questions 
                    SET order_num = ? 
                    WHERE id = ?
                """, (item['order'], item['id']))
            await db.commit()
    
    # Методы для чата
    async def add_chat_message(self, telegram_id: int, message_text: str, from_admin: bool = False):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO chat_messages (user_telegram_id, message_text, from_admin)
                VALUES (?, ?, ?)
            """, (telegram_id, message_text, from_admin))
            await db.commit()
    
    async def get_chat_history(self, telegram_id: int) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM chat_messages 
                WHERE user_telegram_id = ? 
                ORDER BY created_at
            """, (telegram_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Получить пользователей для напоминаний
    async def get_users_for_reminder(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем количество вопросов
            cursor = await db.execute("SELECT COUNT(*) FROM questions")
            question_count = (await cursor.fetchone())[0]
            max_step = question_count  # Последний шаг с вопросами
            
            # Пользователи, которые не отвечали более 15 минут и не завершили опрос
            cursor = await db.execute("""
                SELECT * FROM users 
                WHERE current_step > 0 AND current_step <= ? 
                AND datetime(last_activity, '+15 minutes') <= datetime('now')
            """, (max_step,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Получить всех пользователей
    async def get_all_users(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Удалить пользователя и все его данные
    async def delete_user(self, telegram_id: int):
        """Удаление пользователя и всех его данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем сообщения чата
            await db.execute("DELETE FROM chat_messages WHERE user_telegram_id = ?", (telegram_id,))
            
            # Удаляем пользователя
            await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            
            await db.commit()
            return True