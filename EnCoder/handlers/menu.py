from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from handlers.profile import profile_settings, get_name
from handlers.chat import GROUP_ID
from tools.storage import users_data

WAITING_FOR_NAME = 1


def main_menu_markup(context):
    if not context.user_data.get("chat_mode"):
        keyboard = [
            [InlineKeyboardButton("Запуск чата", callback_data="run_chat")],
            [InlineKeyboardButton("Настройки профиля", callback_data="settings")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Остановка чата", callback_data="stop_chat")],
            [InlineKeyboardButton("Настройки профиля", callback_data="settings")],
        ]
    return InlineKeyboardMarkup(keyboard)


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    context.user_data.setdefault("hidden_mode", False)
    context.user_data.setdefault("chat_mode", False)
    if update.message.chat.id == GROUP_ID:
        markup = ...
    markup = main_menu_markup(context)
    if update.callback_query:
        await update.callback_query.edit_message_text("Главное меню:", reply_markup=markup)
    elif update.message:
        await update.message.reply_text("Главное меню:", reply_markup=markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "run_chat":
        if users_data.get(query.from_user.id, {}).get("is_banned"):
            await query.edit_message_text("Вы заблокированы, вам чат не доступен.", reply_markup=main_menu_markup(context))
        else:
            users_data[str(query.from_user.id)]["chat_mode"] = True
            context.user_data["chat_mode"] = True
            await query.edit_message_text("Чат запущен.", reply_markup=main_menu_markup(context))

    elif query.data == "stop_chat":
        users_data[str(query.from_user.id)]["chat_mode"] = False
        context.user_data["chat_mode"] = False
        await query.edit_message_text("Чат остановлен.", reply_markup=main_menu_markup(context))

    elif query.data == "settings":
        await profile_settings(update, context)

    elif query.data == "get_name":
        await get_name(update, context)

    elif query.data == "back":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu_markup(context))

    elif query.data == "set_name":
        await query.edit_message_text("Введите имя:")
        return WAITING_FOR_NAME
