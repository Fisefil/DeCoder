import os
import re

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)

from handlers.chat import chat_ressender, direct_message_handler
from handlers.menu import send_main_menu, button_handler, WAITING_FOR_NAME, main_menu_markup
from handlers.profile import receive_name
from tools.moderation import ban, unban, mute, unmute
from tools.storage import get_user, upsert_user, assign_codes, init_db

# --- Новое состояние для команды /direct ---
WAITING_DIRECT_MESSAGE = 1001

init_db()


async def direct_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /direct <код1> <код2> ...")
        return ConversationHandler.END

    # Собираем введённые коды (разделённые пробелами или запятыми)
    codes_str = " ".join(args)
    codes = [c.strip() for c in re.split(r"[,\s]+", codes_str) if c.strip()]

    if not codes:
        await update.message.reply_text("Укажите хотя бы один код")
        return ConversationHandler.END

    # Обработка специального кода ALL
    if len(codes) == 1 and codes[0].upper() == "ALL":
        from tools.storage import get_all_codes
        codes = get_all_codes

    context.user_data["direct_codes"] = codes
    await update.message.reply_text(f"Введите сообщение для {', '.join(codes)}:")
    return WAITING_DIRECT_MESSAGE


async def global_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(str(update.effective_user.id))
    if update.effective_chat.type in ("group", "supergroup") and context.user_data.get("hidden_mode"):
        return
    elif update.effective_chat.type in ("group", "supergroup"):
        await chat_ressender(update, context)
    elif user.get("is_banned"):
        await update.message.reply_text("Вы были заблокированы администратором, "
                                        "пока нет функции аппеляции вам предлагается поплакать.")
        return
    elif user.get("is_mutted"):
        await update.message.reply_text("Вы были заткнуты администратором, "
                                        "пока нет функции аппеляции вам предлагается поплакать.")
        return
    elif context.user_data.get("chat_mode"):
        await chat_ressender(update, context)
    else:
        markup = main_menu_markup(context)
        await update.message.reply_text("Чат выключен!", reply_markup=markup)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработчик отмены разговора (fallback)
    await update.message.reply_text("Действие отменено.", reply_markup=main_menu_markup(context))
    return ConversationHandler.END


# Загрузка токена из переменной окружения
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise RuntimeError("Ошибка: не задан токен бота в переменной TELEGRAM_BOT_TOKEN")
app = ApplicationBuilder().token(token).build()


async def hidden(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(str(update.effective_user.id))
    if not user.get("name"):
        await update.message.reply_text("Простите, но вам нужно сначала ввести ваше фейковое имя в базу данных.")
        return
    if update.effective_chat.type == "private":
        return
    hidden_mode = context.user_data.get("hidden_mode", False)
    if hidden_mode:
        context.user_data["hidden_mode"] = False
        await update.message.reply_text("Ваши сообщения теперь видны в боте.")
    elif not hidden_mode:
        context.user_data["hidden_mode"] = True
        await update.message.reply_text("Ваши сообщения теперь скрыты от бота.")


# Запись нового пользователя
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)

    if not user:
        upsert_user(user_id)
        assign_codes()

    if not context.user_data.get("keyboard_shown"):
        context.user_data["keyboard_shown"] = True
        reply_markup = ReplyKeyboardMarkup([[KeyboardButton("/menu")]], resize_keyboard=True)
        await update.message.reply_text("Клавиатура активирована 👇", reply_markup=reply_markup)

    await send_main_menu(update, context)


# ConversationHandler для установки имени
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="set_name")],
    states={
        WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_user=True
)

# ConversationHandler для команды /direct
direct_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("direct", direct_command)],
    states={
        WAITING_DIRECT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, direct_message_handler)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_user=True
)

app.add_handler(CommandHandler(["menu", "start"], start))
app.add_handler(CommandHandler("hidden", hidden))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(conv_handler)
app.add_handler(direct_conv_handler)
# Хэндлер для всех сообщений (кроме команд)
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, global_message_handler))
# Обработчик колбэков кнопок (убрали дублирование "set_name")
app.add_handler(
    CallbackQueryHandler(
        button_handler,
        pattern="^(hello|settings|get_name|back|run_chat|stop_chat)$"
    )
)

app.run_polling()
