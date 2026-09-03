import asyncio
import json
import logging
import os
from collections import OrderedDict

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, MessageOriginChannel


#—————————————————————————Setup—————————————————————————————

#importing bot api token and admin's user id 
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DISCUSSION_GROUP_ID = int(os.getenv("DISCUSSION_GROUP_ID"))

# logic to saves states of bot's memory of message IDs so that it won't be wiped after each relaunch
# bot is intended to be deployed to Railway, so the state file location will need to be set locally
STATE_FILE = os.getenv("STATE_FILE", "bot_state.json")


# Caps the bot's memory
MAX_THREAD_ENTRIES = 500
MAX_NOTIFICATION_ENTRIES = 200


#setting up logs for incoming messages
logging.basicConfig(level = logging.INFO)

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()   
#——————————————————————————Bot Memory—————————————————————————————


#Thread map to tie channel posts in a channel with the same posts
#from discussion supergroup. Basically, channel's message_id —> discussion group's message_id
THREAD_MAP: dict [int, int] = {}

# Map for saving info about messages in discussion group and relaying them to owner and bot's dms
# Basically, notification message's message_id -> original comment's message_id
NOTIFICATION_MAP: OrderedDict[int, int] = OrderedDict()

#checks if the bot is awaiting for a comment text and which thread should the answer be posted into
pending_comment_thread_id: int | None = None

def prune( d: dict, max_size: int):
    #drops the oldest entries when the memory reaches its cap. 

    while len(d) > max_size:
        oldest_key = next(iter(d))
        d.pop(oldest_key)


def save_state():
    # write THREAD_MAP and NOTIFICATION_MAP to the memory as a json file.
    # json's keys' strings are converted to int and vice versa

    data = {
        "thread_map": {str(k): v for k,v in THREAD_MAP.items()},
        "notification_map": {str(k): v for k, v in NOTIFICATION_MAP.items()},
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def load_state():
    # Load the maps from save file, if one exists of course

    if not os.path.exists(STATE_FILE):
        print("No existing STATE_FILE found, we'll have to start from a blank sheet")
        return

    with open(STATE_FILE, "r") as f:
        data = json.load(f)

        THREAD_MAP.update({int(k): v for k, v in data.get("thread_map", {}).items()})
        for k, v in data.get("notification_map", {}).items():
            NOTIFICATION_MAP[int(k)] = v
        print(f"Loaded state: {len(THREAD_MAP)} threads, {len(NOTIFICATION_MAP)} pending notifications.")

def get_text(message: Message) -> str | None:
    # helps the bot react to .text msgs, so that the bot doesn't crash when it gets anything else

    return message.text or message.caption

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
        prune(THREAD_MAP, MAX_THREAD_ENTRIES)
        save_state()
        print(f"Mapped channel post {origin.message_id} -> thread {message.message_id}")


@dp.message(F.chat.id == DISCUSSION_GROUP_ID)
async def relay_comment_to_owner(message: Message):

    # Basically relays every human-made msg from discussion group to the chat with the owner
    # When you reply to the relayed msg the bot will know exactly what msg to reply to in the discussion group

    name = message.from_user.first_name if message.from_user else "Someone"

    text = get_text(message) or "[a non-text message: photo/sticker/gif/etc.]"

    notification = await bot.send_message(
        chat_id = ADMIN_ID,
        text = f"New comment from {name}: \n{text}",
    )

    NOTIFICATION_MAP[notification.message_id] = message.message_id
    prune(NOTIFICATION_MAP, MAX_NOTIFICATION_ENTRIES)
    save_state()


#handler to react to admin's messages in the private channel
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_ID)
async def handle_owner_private_messages(message: Message):

    #Three, no, four! possible message cases:
    #0. A reply to one of our comment notifications -> post your reply, threaded under that original comment.
    #1. forwarded channel post -> bot remembers the origin id and the next msg will be sent by bot as a reply
    #2. plain text after forwarded msg -> bot sends the text as a reply
    #3. plain text -> bot sends it as a regular post in the designated channel 

    global pending_comment_thread_id

    #case 0 

    if message.reply_to_message and message.reply_to_message.message_id in NOTIFICATION_MAP:
        text = get_text(message)
        if text is None:
            await message.reply("Please reply with text — for now, I can only post text comments/posts")
            return
        
        original_comment_id = NOTIFICATION_MAP[message.reply_to_message.message_id]
        # we have an implemented LRU, so the most recently replied to comment/post also moves up to be most recent in the memory
        NOTIFICATION_MAP.move_to_end(message.reply_to_message.message_id)
        save_state()


        await bot.send_message(
            chat_id=DISCUSSION_GROUP_ID,
            text= text,
            reply_to_message_id= original_comment_id,
        )
        await message.reply("Reply posted.")
        return
   
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
        text = get_text(message)
        if text is None:
            await message.reply("Please send text — for now, I can only post text comments/posts.")
            return
        
        await bot.send_message(
            chat_id= DISCUSSION_GROUP_ID,
            text= text,
            reply_to_message_id= pending_comment_thread_id,
        )
        pending_comment_thread_id = None
        await message.reply("Comment posted.")
        return

    #case 3 
    text = get_text(message)
    if text is None:
        await message.reply("Please send text — for now, I can only post text messages/posts.")
        return
    
    await bot.send_message(chat_id=CHANNEL_ID, text= text)
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
    print(f"text:         {get_text(message)}")
    print("---------------------------------")




#——————————————————————————"the main" part—————————————————————————————

async def main():
    load_state()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
