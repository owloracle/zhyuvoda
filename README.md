# Zhuyvoda Telegram Bot
A simple telegram bot for personal purposes, allowing the user to relay messages from a different person on a private channel;

### Version 0.1
The bot now relays everything the owner writes in the private channel as a post to the chosen channel. Terminal now also logs message_id needed for the next installment.

### Version 0 
A simple skeleton that can be tied to a personal channel. It reads all incoming messages and logs them with all relevant details in the inner terminal.




## Set-Up

In order to use this bot, you need to download the files and tie them with a .env file containing the following information:
> BOT_TOKEN 
when you create the bot in Telegram using the BotFather bot (I know, apologies for the tautology), you can receive the token to tie the actual bot to this code
> ADMIN_ID 
Just your account's ID so the bot knows who to listen to in particular. There is a plethora of Telegram bots that can help you find your ID.
> CHANNEL_ID 
Your channel's unique ID. This bot allows logging the messages so all you have to do is make this bot an admin in your channel, launch the code and, while it's running, type something. In the message info you'll see the desired info. 
> (Optional) GROUP_ID 
If your channel has an attached supergroup (for stuff like comment sections under your posts), you can attach it to the code as well to enable the bot to answer people's comments in your stead (you're still piloting, just so we're clear). The steps to getting the ID are identical to CHANNEL_ID. Just add the bot to the supergroup as an admin and type something!