#!/usr/bin/env python3
"""
Тестирование динамических вопросов
"""

import asyncio
from bot.database import Database
from bot.config import DATABASE_PATH

async def test_dynamic_questions():
    """Тестируем добавление и удаление вопросов"""
    db = Database(DATABASE_PATH)
    await db.init_db()
    
    print("🧪 Тестирование динамических вопросов\n")
    
    # Показываем текущие вопросы
    questions = await db.get_questions()
    print(f"📊 Текущее количество вопросов: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q['question_text']}")
    
    # Добавляем новый вопрос
    print("\n➕ Добавляем новый вопрос...")
    new_question = {
        'question_text': 'Какой у тебя любимый язык программирования?',
        'option1': 'Python',
        'option2': 'JavaScript', 
        'option3': 'Java'
    }
    await db.add_question(new_question)
    
    # Показываем обновленный список
    questions = await db.get_questions()
    print(f"✅ Новое количество вопросов: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q['question_text']}")
    
    # Добавляем еще один вопрос
    print("\n➕ Добавляем еще один вопрос...")
    another_question = {
        'question_text': 'Сколько часов в день ты работаешь?',
        'option1': 'Менее 6 часов',
        'option2': '6-8 часов',
        'option3': 'Более 8 часов'
    }
    await db.add_question(another_question)
    
    # Финальный список
    questions = await db.get_questions()
    print(f"✅ Итоговое количество вопросов: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q['question_text']}")
    
    print(f"\n🎯 Теперь бот будет задавать {len(questions)} вопросов вместо 3!")
    print("🌐 Проверьте в админ-панели: http://localhost:3000")
    print("📱 Протестируйте бота: @createboobs_bot")

if __name__ == "__main__":
    asyncio.run(test_dynamic_questions())