import json
import asyncio
from telegram import Bot

BOT_TOKEN = "ТВОЙ_ТОКЕН"
bot = Bot(BOT_TOKEN)

async def update_usernames():
    # Загружаем данные
    with open("../../.venv/Data.json", "r", encoding="utf-8") as f:
        users_data = json.load(f)

    for user_id_str, info in users_data.items():
        user_id = int(user_id_str)
        try:
            user = await bot.get_chat(user_id)  # <--- await обязательно
            info["username"] = user.username if user.username else "неизвестен"
            print(f"{info.get('name','NoName')} — {info['username']}")
        except Exception as e:
            info["username"] = "неизвестен"
            print(f"ID {user_id} — не удалось получить данные: {e}")

    # Сохраняем обратно
    with open("../../.venv/Data.json", "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

# Запуск
asyncio.run(update_usernames())
