import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

BASE_URL = "http://ПОМЕНЯТЬ/v1"

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
OPENAI_TOKEN = getenv("OPENAI_API_TOKEN")

client = AsyncOpenAI(api_key=OPENAI_TOKEN, base_url=BASE_URL)

translator_router = Router()


class Translator(StatesGroup):
    translate_message = State()
    request_new_message = State()


# Стартовое сообщение
@translator_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Translator.translate_message)
    await message.answer(
        "Привет! Напиши мне любое сообщение на любом языке, которое ты хочешь перевести, и я постараюсь перевести его на русский!"
    )


# Переводчик
@translator_router.message(Translator.translate_message)
async def process_translate_message(message: Message, state: FSMContext) -> None:
    translation = await message.reply("Думаю...")

    # !!!! Вот тут самый сок !!!!
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a professional translator. You perfectly understand languages and can translate any langage to Russian",
            },
            {
                "role": "user",
                "content": f"Translate {message.text} into Russian. Reply with just the result of the translation, nothing else",
            },
        ],
        temperature=0.8,
    )

    await translation.edit_text(completion.choices[0].message.content)
    await message.answer("Вот перевод. Могу перевести что-то еще")

    await state.set_state(Translator.translate_message)
    # !!!! Вот тут самый сок заканчивается !!!!


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(translator_router)

    await dp.start_polling(bot)


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
asyncio.run(main())
