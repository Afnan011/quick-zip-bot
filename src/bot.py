import os
import logging
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
OWNER_ID = int(os.environ['OWNER_ID'])  # Telegram user ID of the bot owner

logging.basicConfig(
    format='[%(levelname)s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ]
)

from telethon import events

# Reuse the previous initialization
bot = TelegramClient('quick-zip-bot', api_id=API_ID, api_hash=API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond('Hello! The bot is running.')

if __name__ == '__main__':
    with bot:
        bot.loop.run_until_complete(bot.send_message(OWNER_ID, "Bot has started successfully!"))
        bot.run_until_disconnected()
