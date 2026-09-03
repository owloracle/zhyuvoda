import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, MessageOriginChannel

#importing bot api token and admin's user id 
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DISCUSSION_GROUP_ID = int(os.getenv("DISCUSSION_GROUP_ID"))

#setting up logs for incoming messages
logging.basicConfig(level = logging.INFO)

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()   
#——————————————————————————Bot Memory—————————————————————————————


#Thread map to tie channel posts in a channel with the same posts
#from discussion supergroup. Basically, channel's message_id —> discussion group's message_id
THREAD_MAP: dict [int, int] = {}

#checks if the bot is awaiting for a comment text and which thread should the answer be posted into
pending_comment_thread_id: int | None = None

#——————————————————————————Handlers—————————————————————————————

#separate handler to get channel's unique id
@dp.channel_post()
async def log_channel_post(message: Message):

    print("----- Channel post received -----")
    print(f"chat.id:      {message.chat.id}")
    print(f"message_id:   {message.message_id}")
    print(f"text:         {message.text}")
    print("---------------------------------")

@dp.message(F.chat.id == DISCUSSION_GROUP_ID, F.forward_origin.as_("origin"))
async def capture_thread_mapping(message: Message, origin: MessageOriginChannel):

    #We record: original channel message_id -> this group message_id.
    #turns up only when msgs from discussion group are forwarded

    if origin.chat.id == CHANNEL_ID:
        THREAD_MAP[origin.message_id] = message.message_id
        print(f"Mapped channel post {origin.message_id} -> thread {message.message_id}")



#handler to react to admin's messages in the private channel
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_ID)
async def handle_owner_private_messages(message: Message):

    #Three possible message cases:
    #1. forwarded message -> bot remembers the origin id and the next msg will be sent by bot as a reply
    #2. plain text after forwarded msg -> bot sends the text as a reply
    #3. plain text -> bot sends it as a regular post in the designated channel 

    global pending_comment_thread_id

    #case 1

    if message.forward_origin and isinstance(message.forward_origin, MessageOriginChannel):
        origin = message.forward_origin
        if origin.chat.id != CHANNEL_ID:
            await message.reply("That is not a post from your channel")
            return

        thread_id = THREAD_MAP.get(origin.message_id)
        if thread_id is None:
            await message.reply(
               "I don't have a discussion thread recorded for that post yet. "
               "Make sure the bot was running when it was posted, or try a more recent post."
            )
            return

        pending_comment_thread_id = thread_id
        await message.reply("Got it. Send me the comment text now.")
        return

    #case 2

    if pending_comment_thread_id is not None:
        await bot.send_message(
            chat_id= DISCUSSION_GROUP_ID,
            text= message.text,
            message_thread_id= pending_comment_thread_id,
        )
        pending_comment_thread_id = None
        await message.reply("Comment posted.")
        return

    #case 3 

    await bot.send_message(chat_id=CHANNEL_ID, text= message.text)
    await message.reply("Posted to channel.")

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




#——————————————————————————"the main" part—————————————————————————————

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
