import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message

#importing bot api token and admin's user id 
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_TOKEN")


#setting up logs for incoming messages
logging.basicConfig(level = logging.INFO)

bot = Bot(token = BOT_TOKEN)

dp = Dispatcher()



@dp.message()
async def terminal_logs(message: Message):

    print("----- New message received -----")
    print(f"chat.id:      {message.chat.id}")
    print(f"chat.type:    {message.chat.type}")
    print(f"chat.title:   {message.chat.title}")
    print(f"from_user:    {message.from_user}")
    print(f"text:         {message.text}")
    print("---------------------------------")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())