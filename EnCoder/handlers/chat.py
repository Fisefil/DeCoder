from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from html import escape
import logging
import re

from tools.storage import users_data, get_user_ids_by_codes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

GROUP_ID = -1003169335486
MAX_REPLY_LEN = 50


def build_nested_reply(raw_reply: str, reply_name: str|None = None, reply_code: str|None = None, max_len: int = MAX_REPLY_LEN) -> str:
    if not raw_reply:
        return ""
    matches = list(re.finditer(r'\[[^\[\]]+#\d{5}\]', raw_reply))
    snippet = raw_reply[matches[-3].start():] if len(matches) >= 3 else raw_reply
    last_match = re.search(r'\[.*?#\d{5}\]', snippet)
    if last_match:
        snippet = snippet[last_match.start():last_match.start() + max_len]
    if reply_name != None:
        return f"[{reply_name}#{reply_code}]\n{snippet}"
    else: return snippet


def can_have_caption(message) -> bool:
    return any([message.photo, message.video, message.animation, message.document, message.audio, message.voice])


async def send_anything(context, chat_id, message, caption):
    caption = caption if caption else None
    if can_have_caption(message):
        if message.photo:
            await context.bot.send_photo(chat_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        elif message.video:
            await context.bot.send_video(chat_id, video=message.video.file_id, caption=caption, parse_mode="HTML")
        elif message.animation:
            await context.bot.send_animation(chat_id, animation=message.animation.file_id, caption=caption, parse_mode="HTML")
        elif message.document:
            await context.bot.send_document(chat_id, document=message.document.file_id, caption=caption, parse_mode="HTML")
        elif message.audio:
            await context.bot.send_audio(chat_id, audio=message.audio.file_id, caption=caption, parse_mode="HTML")
        elif message.voice:
            await context.bot.send_voice(chat_id, voice=message.voice.file_id, caption=caption, parse_mode="HTML")
    else:
        if message.sticker:
            if caption:
                await context.bot.send_message(chat_id, text=caption, parse_mode="HTML")
            await context.bot.send_sticker(chat_id, sticker=message.sticker.file_id)
        elif message.text:
            await context.bot.send_message(chat_id, text=caption, parse_mode="HTML")


async def chat_ressender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    supported = any([msg.text, msg.photo, msg.video, msg.animation, msg.document, msg.audio, msg.voice, msg.sticker])
    if not supported:
        await msg.reply_text("❌ Данный формат не поддерживается")
        return

    text = msg.text or msg.caption or ""
    user_id = str(msg.from_user.id)
    chat_id = msg.chat.id

    user = users_data.get(user_id, {})
    code = user.get("code", "?????")
    name = user.get("name", "Неизвестный")

    if msg.reply_to_message:
        raw_reply = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        reply_user_id = str(msg.reply_to_message.from_user.id)
        reply_user = users_data.get(reply_user_id, {})
        reply_name = reply_user.get("name", None)
        reply_code = reply_user.get("code", None)
        nested_reply = build_nested_reply(raw_reply, reply_name, reply_code, MAX_REPLY_LEN)
        msg_text = f"<blockquote><i>{nested_reply}</i></blockquote>\n{escape(text)}"
    else:
        msg_text = escape(text)

    final_text = f"[{escape(name)}#<i>{code}</i>]\n{msg_text}"
    logging.info(f"\n{final_text}")

    with open("chat.log", "a", encoding="utf-8") as f:
        f.write(f"\n{final_text}\n")

    for uid, udata in users_data.items():
        if str(uid) == user_id and chat_id != GROUP_ID:
            continue
        if not udata.get("chat_mode", False):
            continue
        try:
            await send_anything(context, uid, msg, final_text)
        except Exception as e:
            logging.warning(f"Не удалось отправить {uid}: {e}")

    if chat_id != GROUP_ID:
        try:
            await send_anything(context, GROUP_ID, msg, final_text)
        except Exception as e:
            logging.warning(f"Не удалось отправить в группу: {e}")

    if code == "?????":
        await msg.reply_text("Сначала задайте себе имя в настройках профиля")


async def direct_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if context.user_data.get("is_blocked"):
        await msg.reply_text("Вы заблокированы, вам личный чат не доступен.")
    supported = any([msg.text, msg.photo, msg.video, msg.animation, msg.document, msg.audio, msg.voice, msg.sticker])
    if not supported:
        await msg.reply_text("❌ Данный формат не поддерживается")
        return

    message_text = msg.text or msg.caption or ""
    codes = context.user_data.get("direct_codes", [])

    user_id = str(msg.from_user.id)
    user = users_data.get(user_id, {})
    code = user.get("code", "?????")
    name = user.get("name", "Неизвестный")

    if not codes:
        await msg.reply_text("Ошибка: не выбраны коды")
        return

    user_ids = get_user_ids_by_codes(codes)
    if not user_ids:
        await msg.reply_text("Не найдено таких кодов")
        return

    final_text = f"[{escape(name)}#<i>{escape(code)}</i>]\n{message_text}"
    sent_to = []

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"Вам прямое сообщение от [{escape(name)}#<i>{escape(code)}</i>]", parse_mode="HTML")
            await send_anything(context, uid, msg, final_text)
            sent_to.append(users_data[uid].get("name", uid))
        except Exception as e:
            await msg.reply_text(f"Не удалось отправить {uid}: {e}")

    if sent_to:
        await msg.reply_text(f"Отправлено {', '.join(sent_to)}")
