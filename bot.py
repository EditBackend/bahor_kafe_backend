import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Bot tokeningizni yozing
BOT_TOKEN = "8605510081:AAF2QRx4ihyCPYjJL3EUps-GX6ONaOY3KME"
# Frontendchining mini app havolasi
MINI_APP_URL = "https://dancing-babka-7d347f.netlify.app/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_command(message: types.Message):
    # Diyorbek xohlagan o'sha inline tugmalar matritsasi:
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open 📱", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="✍️ Leave feedback", callback_data="feedback")]
    ])

    await message.answer(
        "Xush kelibsiz! Quyidagi tugma orqali menyuni ochishingiz mumkin 👇",
        reply_markup=inline_kb
    )


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())