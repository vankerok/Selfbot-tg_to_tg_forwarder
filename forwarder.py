from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChat
from telethon import events
from config import tg_user, forward_from, forward_to, user_to_parse
from loguru import logger
from sys import stderr

logger.remove()
logger.add("mirror.log", rotation="1 week", level="INFO",
           format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message: <8}</white>")
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message: <8}</white>")

def telegram_client_authorise():
    try:
        client = TelegramClient(tg_user['name'], tg_user['api_id'], tg_user['api_hash']).start()
        client.connect()

        me = client.get_me()
        account_username = me.username
        
        logger.success(f"Succesfully logged in as @{account_username}")
        receiver = InputPeerChat(forward_to)
        return receiver, client
    
    except Exception as auth_error:
            if "database is locked" in str(auth_error):
                logger.error('Bot is already launched in another window or device')
                raise auth_error
            else:
                logger.error(f"Authorization error: {auth_error}")
                raise auth_error

def get_message_type(message):
    if message.text:
        return message.message
    elif message.photo:
        return 'photo'
    elif message.video:
        return 'video or gif'
    elif message.voice:
        return 'voice message'
    elif message.sticker:
        return 'sticker'
    else:
        return 'file'

receiver, client = telegram_client_authorise()

@client.on(events.NewMessage(chats=forward_from, from_users=user_to_parse))
async def handler(event):
    try:
        forward_messages = [event.message]

        replied_to_message = await event.message.get_reply_message()
        if replied_to_message and replied_to_message.sender_id != event.message.sender_id:
            already_existing_messages = await client.get_messages(forward_to, reply_to_msg_id=[replied_to_message.id])
            if already_existing_messages:
                forward_messages.append(replied_to_message)

        await client.forward_messages(forward_to, forward_messages, with_my_score=True)
        logger.success(f'''Message was succefully forwarded: "{get_message_type(event.message)}"''')
    except Exception as forward_error:
        logger.error(f"Message forwarding error: {forward_error}")

client.run_until_disconnected()
