import asyncio
from telethon import TelegramClient, events, types
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------- CONFIG ----------
API_ID = int(os.environ.get("TG_API_ID", "23983239"))    # <-- замените или выставьте через переменную окружения
API_HASH = os.environ.get("TG_API_HASH", "e6e195529ae0ce89df1a9f4ca7fb23d5")   # <-- замените или выставьте через переменную окружения

# Идентификаторы/username источника и цели.
# Можно указать: numeric id (int), username ("@example") или None.
# Примеры: SOURCE_CHAT = "https://t.me/somechannel" or SOURCE_CHAT = -1001234567890
SOURCE_CHAT = [-1003169335486, -4825976241]    # слушать все чаты, или указать отдельный чат/чат(список)
DEST_CHAT = None     # куда эхо слать. None = в тот же чат (echo in place)

# Если хочешь слушать несколько конкретных чатов:
# SOURCE_CHAT = ["@chat1", -1001234567890]
# DEST_CHAT можно тоже задать как словарь маппинга {source: dest} — см. расширение ниже.
# ---------------------------

SESSION = "userbot.session"


async def main():
    if API_ID == "YOUR_API_ID" or API_HASH == "YOUR_API_HASH":
        logger.error("Пожалуйста, укажи API_ID и API_HASH в коде или через переменные окружения TG_API_ID и TG_API_HASH.")
        return

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()  # при первом запуске попросит телефон и код

    me = await client.get_me()
    logger.info(f"Authorized as {me.username or me.first_name} (id={me.id})")

    # Normalize config: allow single value or list
    sources = None
    if SOURCE_CHAT is None:
        sources = None
    elif isinstance(SOURCE_CHAT, (list, tuple)):
        sources = SOURCE_CHAT
    else:
        sources = [SOURCE_CHAT]

    # For simplicity: if DEST_CHAT is a dict we will map sources->dest; otherwise single dest or None.
    mapping = None
    if isinstance(DEST_CHAT, dict):
        mapping = DEST_CHAT
    else:
        mapping = None

    @client.on(events.NewMessage(chats=sources))
    async def handler(event: events.NewMessage.Event):
        if event.out:
            return  # игнор своих сообщений

        target = DEST_CHAT or event.chat_id

        try:
            if event.message.media:
                await client.forward_messages(entity=target, messages=event.message, from_peer=event.chat_id)
            else:
                text = event.message.message
                if not text:
                    return

                reply_to = event.message.reply_to_msg_id if event.message.is_reply and target == event.chat_id else None

                await client.send_message(
                    entity=target,
                    message=text,
                    formatting_entities=event.message.entities,  # вот ключевое изменение
                    reply_to=reply_to
                )
        except Exception as e:
            logger.exception("Ошибка при эхо:")

    logger.info("Echo handler установлен. Запуск клиента...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")