import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

#importing bot api token and admin's user id 
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))


#setting up logs for incoming messages
logging.basicConfig(level = logging.INFO)

bot = Bot(token = BOT_TOKEN)

dp = Dispatcher()   

#——————————————————————————Handlers—————————————————————————————


#handler to react to admin's messages in the private channel
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_ID)
async def post_to_channel(message: Message):
    await bot.send_message(chat_id=CHANNEL_ID, text=message.text)
    await message.reply("Повідомлення надіслано") # "message sent". This is what will be written in response to your entries. Can be changed



#handler to catch simple messages and display their info
@dp.message()
async def terminal_logs(message: Message):

    print("----- New message received -----")
    print(f"chat.id:      {message.chat.id}")
    print(f"chat.type:    {message.chat.type}")
    print(f"chat.title:   {message.chat.title}")
    print(f"from_user:    {message.from_user}")
    print(f"message_id:   {message.message_id}")
    print(f"text:         {message.text}")
    print("---------------------------------")

#separate handler to get channel's unique id
@dp.channel_post()
async def terminal_logs(message: Message):

    print("----- New message received -----")
    print(f"chat.id:      {message.chat.id}")
    print(f"chat.type:    {message.chat.type}")
    print(f"chat.title:   {message.chat.title}")
    print(f"from_user:    {message.from_user}")
    print(f"message_id:   {message.message_id}")
    print(f"text:         {message.text}")
    print("---------------------------------")





#——————————————————————————"the main" part—————————————————————————————

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
