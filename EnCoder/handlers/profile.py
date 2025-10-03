from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from tools.storage import users_data, save_data, assign_codes

async def profile_settings(update: Update):
    keyboard = [
        [InlineKeyboardButton("Сменить имя", callback_data="set_name")],
        [InlineKeyboardButton("Моё имя", callback_data="get_name")],
        [InlineKeyboardButton("Назад в меню", callback_data="back")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Настройки:", reply_markup=markup)

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    name = update.message.text

    if user_id not in users_data:
        users_data[user_id] = {}

    # Сохраняем введённое имя
    users_data[user_id]["name"] = name
    # Сохраняем username (если нет — "неизвестен")
    users_data[user_id]["username"] = user.username or "неизвестен"

    assign_codes(users_data)
    save_data(users_data)

    await update.message.reply_text(f"Имя сохранено: {name}")

    from handlers.menu import send_main_menu
    await send_main_menu(update, context)
    return -1  # ConversationHandler.END

async def get_name(update: Update):
    user_id = str(update.effective_user.id)
    name = users_data.get(user_id, {}).get("name")
    if name:
        await update.effective_message.reply_text(f"Ваше имя: {name}")
    else:
        await update.effective_message.reply_text("Имя ещё не задано.")
