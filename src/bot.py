import asyncio
from functools import partial
from asyncio import get_running_loop
from shutil import rmtree
from pathlib import Path
import logging
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.events import NewMessage, StopPropagation
from telethon.tl.custom import Message

from utils import download_files, add_to_zip

load_dotenv()

API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
CONC_MAX = int(os.environ.get('CONC_MAX', 3))
STORAGE = Path('./files/')

MessageEvent = NewMessage.Event | Message

logging.basicConfig(
    format='[%(levelname)s/%(asctime)s] %(name)s: %(message)s',
    level=logging.DEBUG,  # Set to DEBUG for detailed logging
    handlers=[
        logging.StreamHandler(),
    ]
)

tasks: dict[int, list[int]] = {}

bot = TelegramClient(
    'quick-zip-bot', api_id=API_ID, api_hash=API_HASH
).start(bot_token=BOT_TOKEN)


@bot.on(NewMessage(pattern='/add'))
async def start_task_handler(event: MessageEvent):
    tasks[event.sender_id] = []
    await event.respond('OK, send me some files.')
    raise StopPropagation


@bot.on(NewMessage(
    func=lambda e: e.sender_id in tasks and e.file is not None))
async def add_file_handler(event: MessageEvent):
    tasks[event.sender_id].append(event.id)
    raise StopPropagation


@bot.on(NewMessage(pattern='/zip (?P<name>\w+)'))
async def zip_handler(event: MessageEvent):
    if event.sender_id not in tasks:
        await event.respond('You must use /add first.')
    elif not tasks[event.sender_id]:
        await event.respond('You must send me some files first.')
    else:
        messages = await bot.get_messages(
            event.sender_id, ids=tasks[event.sender_id])
        zip_size = sum([m.file.size for m in messages])

        if zip_size > 1024 * 1024 * 2000:  # zip_size > 1.95 GB approximately
            await event.respond('Total filesize must not exceed 2.0 GB.')
        else:
            root = STORAGE / f'{event.sender_id}/'
            zip_name = root / (event.pattern_match['name'] + '.zip')

            async for file in download_files(messages, CONC_MAX, root):
                await get_running_loop().run_in_executor(
                    None, partial(add_to_zip, zip_name, file))
            
            await event.respond('Done!', file=zip_name)

            await get_running_loop().run_in_executor(
                None, rmtree, STORAGE / str(event.sender_id))

        tasks.pop(event.sender_id)

    raise StopPropagation


@bot.on(NewMessage(pattern='/cancel'))
async def cancel_handler(event: MessageEvent):
    try:
        tasks.pop(event.sender_id)
    except KeyError:
        pass

    await event.respond('Canceled zip. For a new one, use /add.')

    raise StopPropagation


async def main():
    await bot.start()
    logging.info("Bot started successfully.")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
