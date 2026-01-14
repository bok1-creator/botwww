import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from bot.database import Database
from bot.config import DATABASE_PATH

router = Router()
db = Database(DATABASE_PATH)

@router.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    user_data = {
        'telegram_id': message.from_user.id,
        'username': message.from_user.username or '',
        'first_name': message.from_user.first_name or '',
        'current_step': 0
    }
    
    await db.create_or_update_user(user_data)
    await send_welcome(message)

async def send_welcome(message: Message):
    """Отправка приветствия"""
    settings = await db.get_settings()
    if not settings:
        return
    
    # Отправляем видео если есть
    if settings['welcome_video']:
        try:
            await message.answer_video(
                video=settings['welcome_video'],
                caption=settings['welcome_text']
            )
        except:
            # Если видео не удалось отправить, отправляем только текст
            await message.answer(settings['welcome_text'])
    else:
        await message.answer(settings['welcome_text'])
    
    # Переходим к первому вопросу
    await db.update_user_step(message.from_user.id, 1)
    await send_question(message, 1)

async def send_question(message: Message, question_number: int):
    """Отправка вопроса с вариантами ответов"""
    questions = await db.get_questions()
    
    if question_number > len(questions):
        return
    
    question = questions[question_number - 1]
    
    # Создаем клавиатуру с вариантами ответов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=question['option1'], 
            callback_data=f"answer_{question_number}_1"
        )],
        [InlineKeyboardButton(
            text=question['option2'], 
            callback_data=f"answer_{question_number}_2"
        )],
        [InlineKeyboardButton(
            text=question['option3'], 
            callback_data=f"answer_{question_number}_3"
        )]
    ])
    
    await message.answer(question['question_text'], reply_markup=keyboard)

@router.callback_query(F.data.startswith("answer_"))
async def answer_handler(callback: CallbackQuery):
    """Обработчик ответов на вопросы"""
    data_parts = callback.data.split('_')
    question_number = int(data_parts[1])
    option_number = int(data_parts[2])
    
    user = await db.get_user(callback.from_user.id)
    if not user:
        return
    
    # Получаем текущие ответы
    answers = []
    if user['answers']:
        try:
            answers = json.loads(user['answers'])
        except:
            answers = []
    
    # Получаем все вопросы для определения общего количества
    questions = await db.get_questions()
    total_questions = len(questions)
    
    if question_number > total_questions:
        return
    
    # Получаем текст выбранного варианта
    question = questions[question_number - 1]
    selected_option = question[f'option{option_number}']
    
    # Сохраняем ответ
    while len(answers) < question_number:
        answers.append({})
    
    answers[question_number - 1] = {
        'question': question['question_text'],
        'answer': selected_option
    }
    
    await db.update_user_answers(callback.from_user.id, answers)
    
    # Отвечаем на callback
    await callback.answer("✅ Ответ сохранен!")
    
    if question_number < total_questions:
        # Переходим к следующему вопросу
        next_step = question_number + 1
        await db.update_user_step(callback.from_user.id, next_step)
        await callback.message.answer("Отлично! Следующий вопрос:")
        await send_question(callback.message, next_step)
    else:
        # Все вопросы отвечены, просим текстовый ввод
        await db.update_user_step(callback.from_user.id, total_questions + 1)
        await callback.message.answer(
            "🎉 Супер! Теперь расскажи немного о себе своими словами:"
        )

@router.message(F.text)
async def text_handler(message: Message):
    """Обработчик текстовых сообщений"""
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    # Получаем общее количество вопросов
    questions = await db.get_questions()
    total_questions = len(questions)
    text_input_step = total_questions + 1
    completed_step = total_questions + 2
    
    if user['current_step'] == text_input_step:
        # Сохраняем текстовый ввод
        await db.update_user_text_input(message.from_user.id, message.text)
        await db.update_user_step(message.from_user.id, completed_step)
        
        await message.answer(
            "🎉 Спасибо! Твои ответы получены. "
            "Скоро с тобой свяжется наш специалист."
        )
        
        # Здесь можно добавить уведомление админа
        print(f"Новый пользователь завершил опрос: {message.from_user.id}")
        
    elif user['current_step'] == completed_step:
        # Пользователь в режиме чата с админом
        await db.add_chat_message(message.from_user.id, message.text, False)
        
        # Здесь можно добавить пересылку админу
        print(f"Сообщение от {message.from_user.id}: {message.text}")

async def send_reminder(telegram_id: int, bot):
    """Отправка напоминания пользователю"""
    settings = await db.get_settings()
    reminder_text = settings['reminder_text'] if settings else "Эй, ты забыл ответить! 😊 Продолжим?"
    
    try:
        await bot.send_message(telegram_id, reminder_text)
    except Exception as e:
        print(f"Ошибка отправки напоминания {telegram_id}: {e}")