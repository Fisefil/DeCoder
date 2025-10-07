from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from tools.storage import get_user, upsert_user, assign_codes

async def profile_settings(update: Update):
    keyboard = [
        [InlineKeyboardButton("Сменить имя", callback_data="set_name")],
        [InlineKeyboardButton("Моё имя", callback_data="get_name")],
        [InlineKeyboardButton("Назад в меню", callback_data="back")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Настройки:", reply_markup=markup)

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    name = update.message.text

    if user is None:
        upsert_user(user_id, name=name, username=update.effective_user.username or "неизвестен")
    else:
        upsert_user(user_id, name=name)

    assign_codes()

    await update.message.reply_text(f"Имя сохранено: {name}")

    from handlers.menu import send_main_menu
    await send_main_menu(update, context)
    return -1  # ConversationHandler.END

async def get_name(update: Update):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    name = user.get("name")
    if name:
        await update.effective_message.reply_text(f"Ваше имя: {name}")
    else:
        await update.effective_message.reply_text("Имя ещё не задано.")
