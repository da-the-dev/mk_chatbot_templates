import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

BASE_URL = "http://ПОМЕНЯТЬ/v1"

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
OPENAI_TOKEN = getenv("OPENAI_API_TOKEN")

client = AsyncOpenAI(
    api_key=OPENAI_TOKEN,
    base_url=BASE_URL,
)

rp_router = Router()


class RolePlayer(StatesGroup):
    rp_reply = State()


dialog = []


@rp_router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await message.answer("Привет! Напиши мне персонажа, которого я должен отыгрывать")
    await state.set_state(RolePlayer.rp_reply)


@rp_router.message(Command("restart"))
async def restart(message: Message, state: FSMContext) -> None:
    await message.answer("Перезапускаюсь...")

    await state.clear()
    dialog = []

    await message.answer("Привет! Напиши мне персонажа, которого я должен отыгрывать")
    await state.set_state(RolePlayer.rp_reply)


@rp_router.message(RolePlayer.rp_reply)
async def process_translate_message(message: Message, state: FSMContext) -> None:
    global dialog

    # Заполняем диалог ролью
    if len(dialog) <= 0:
        dialog = [
            {
                "role": "system",
                "content": f"Role play as {message.text}. Respond in Russian",
            },
        ]

    # Добавляем в диалог пользовательское сообщение
    dialog.append(
        {
            "role": "user",
            "content": message.text,
        }
    )

    # Генерируем продолжение диалога, опираясь на его историю
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=dialog,
        temperature=0.8,
    )

    # Добавляем продолжение в диалоговую историю
    dialog.append(
        {
            "role": "assistant",
            "content": completion.choices[0].message.content,
        }
    )

    # Отправялем ответ
    await message.answer(completion.choices[0].message.content)

    # Цикл состояний
    await state.set_state(RolePlayer.rp_reply)


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(rp_router)

    await dp.start_polling(bot)


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
asyncio.run(main())
