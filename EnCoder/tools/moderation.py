import datetime
import re

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from tools.storage import get_user, get_user_ids_by_codes, upsert_user


def parse_duration(arg: str) -> datetime.datetime | None:
    if not arg:
        return None
    try:
        amount = int(arg[:-1])
        unit = arg[-1]
        if unit == "m":
            delta = datetime.timedelta(minutes=amount)
        elif unit == "h":
            delta = datetime.timedelta(hours=amount)
        elif unit == "d":
            delta = datetime.timedelta(days=amount)
        else:
            return None
        return datetime.datetime.now() + delta
    except Exception:
        return None

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user = get_user(user_id)

    args = context.args or []
    target_id = None
    if args:
        first_arg = args[0]
        if first_arg.isdigit():
            target_id = int(first_arg)
            args = args[1:]
        elif update.message.reply_to_message:
            reply_id = update.message.reply_to_message.from_user.id

            if reply_id == 7994342968 and update.message.reply_to_message.text:
                match = re.search(r"#(.{5})", update.message.reply_to_message.text)
                if match:
                    code = match.group(1)
                    user_ids = get_user_ids_by_codes([code])
                    target_id = user_ids[0] if user_ids else reply_id
                else:
                    await update.message.reply_text("Не найден пользователь.")
            else:
                target_id = reply_id
        else:
            await update.message.reply_text("Использование: /ban <user_id> [<time>] [<reason>]")
            return
    else:
        if update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
        else:
            await update.message.reply_text("Использование: /ban <user_id> [<time>] [<reason>]")
            return

    if update.effective_chat.type == "private" or not user.get("is_admin"):
        await update.message.reply_text("Вы не являетесь администратором!")
        return
    if target_id == user_id:
        await update.message.reply_text("Пожалуйста, не пытайтесь заблокировать себя...")
        return

    target_data = get_user(target_id)
    if target_data.get("is_banned"):
        await update.message.reply_text("Пользователь уже заблокирован!")
        return

    until = None
    reason = "без причины"
    if args:
        parsed = parse_duration(args[0])
        if parsed:
            until = parsed
            if len(args) > 1:
                reason = " ".join(args[1:])
        else:
            reason = " ".join(args)

    upsert_user(target_id, is_banned=True)

    if update.effective_chat.type in ("group", "supergroup") and target_id != 7994342968:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            until_date=until
        )

    if until:
        final_text = f"Пользователь заблокирован до {until} UTC. Причина: {reason}"
        await update.message.reply_text(final_text)
    else:
        final_text = f"Пользователь заблокирован до {until} UTC. Причина: {reason}"
        await update.message.reply_text(f"Пользователь заблокирован навсегда. Причина: {reason}")

    with open("moderation.log", "a", encoding="utf-8") as f:
        f.write(f"\n{final_text} Пользователь: {target_id}\n")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user = get_user(user_id)

    reply_to = update.message.reply_to_message.from_user.id

    args = context.args or []
    target_id = None
    if args:
        if args[0].isdigit():
            target_id = int(args[0])
        elif update.message.reply_to_message:
            reply_id = update.message.reply_to_message.from_user.id

            if reply_id == 7994342968 and update.message.reply_to_message.text:
                match = re.search(r"#(.{5})", update.message.reply_to_message.text)
                if match:
                    code = match.group(1)
                    user_ids = get_user_ids_by_codes([code])
                    target_id = user_ids[0] if user_ids else reply_id
                else:
                    await update.message.reply_text("Не найден пользователь.")
            else:
                target_id = reply_id
        else:
            await update.message.reply_text("Использование: /unban <user_id>")
            return
    else:
        if update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
        else:
            await update.message.reply_text("Использование: /unban <user_id>")
            return

    if update.effective_chat.type == "private" or not user.get("is_admin"):
        await update.message.reply_text("Вы не являетесь администратором!")
        return
    if target_id == user_id:
        await update.message.reply_text("Пожалуйста, не пытайтесь разблокировать себя...")
        return

    target_data = get_user(target_id)
    if not target_data.get("is_banned"):
        await update.message.reply_text("Пользователь не заблокирован!")
        return

    upsert_user(target_id, is_banned=False)

    if update.effective_chat.type in ("group", "supergroup") and target_id != 7994342968:
        await context.bot.unban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            only_if_banned=True
        )
    final_text = f"Пользователь успешно разблокирован!"
    await update.message.reply_text(final_text)
    with open("moderation.log", "a", encoding="utf-8") as f:
        f.write(f"\n{final_text} Пользователь: {target_id}\n")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user = get_user(user_id)

    args = context.args or []
    target_id = None
    if args:
        if args[0].isdigit():
            target_id = int(args[0])
            args = args[1:]
        elif update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
        else:
            await update.message.reply_text("Использование: /mute <user_id> [<time>] [<reason>]")
            return
    else:
        if update.message.reply_to_message:
            reply_id = update.message.reply_to_message.from_user.id

            if reply_id == 7994342968 and update.message.reply_to_message.text:
                match = re.search(r"#(.{5})", update.message.reply_to_message.text)
                if match:
                    code = match.group(1)
                    user_ids = get_user_ids_by_codes([code])
                    target_id = user_ids[0] if user_ids else reply_id
                else:
                    await update.message.reply_text("Не найден пользователь.")
            else:
                target_id = reply_id
        else:
            await update.message.reply_text("Использование: /mute <user_id> [<time>] [<reason>]")
            return

    if update.effective_chat.type == "private" or not user.get("is_admin"):
        await update.message.reply_text("Вы не являетесь администратором!")
        return
    if target_id == user_id:
        await update.message.reply_text("Пожалуйста, не пытайтесь заткнуть себя...")
        return

    target_data = get_user(target_id)
    if target_data.get("is_muted"):
        await update.message.reply_text("Пользователь уже заткнут!")
        return

    until = None
    reason = "без причины"
    if args:
        parsed = parse_duration(args[0])
        if parsed:
            until = parsed
            if len(args) > 1:
                reason = " ".join(args[1:])
        else:
            reason = " ".join(args)

    upsert_user(target_id, is_muted=True)

    if update.effective_chat.type in ("group", "supergroup") and target_id != 7994342968:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            ),
            until_date=until
        )

    if until:
        final_text = f"Пользователь заткнут до {until} UTC. Причина: {reason}"
        await update.message.reply_text(final_text)
    else:
        final_text = f"Пользователь заткнут навсегда. Причина: {reason}"
        await update.message.reply_text(final_text)

    with open("moderation.log", "a", encoding="utf-8") as f:
        f.write(f"\n{final_text} Пользователь: {target_id}\n")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user = get_user(user_id)

    args = context.args or []
    target_id = None
    if args:
        if args[0].isdigit():
            target_id = int(args[0])
        elif update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
        else:
            await update.message.reply_text("Использование: /unmute <user_id>")
            return
    else:
        if update.message.reply_to_message:
            reply_id = update.message.reply_to_message.from_user.id

            if reply_id == 7994342968 and update.message.reply_to_message.text:
                match = re.search(r"#(.{5})", update.message.reply_to_message.text)
                if match:
                    code = match.group(1)
                    user_ids = get_user_ids_by_codes([code])
                    target_id = user_ids[0] if user_ids else reply_id
                else:
                    await update.message.reply_text("Не найден пользователь.")
            else:
                target_id = reply_id
        else:
            await update.message.reply_text("Использование: /unmute <user_id>")
            return

    if update.effective_chat.type == "private" or not user.get("is_admin"):
        await update.message.reply_text("Вы не являетесь администратором!")
        return
    if target_id == user_id:
        await update.message.reply_text("Пожалуйста, не пытайтесь снять заткнутость себе...")
        return

    target_data = get_user(target_id)
    if not target_data.get("is_muted"):
        await update.message.reply_text("Пользователь не заткнут!")
        return

    upsert_user(target_id, is_mutted=False)

    if update.effective_chat.type in ("group", "supergroup") and target_id != 7994342968:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )

    final_text = "Пользователь теперь может говорить!"
    await update.message.reply_text(final_text)

    with open("moderation.log", "a", encoding="utf-8") as f:
        f.write(f"\n{final_text} Пользователь: {target_id}\n")
