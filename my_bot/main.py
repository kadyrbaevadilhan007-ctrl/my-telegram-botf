import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# Logging setup
logging.basicConfig(level=logging.INFO)

# --- SETTINGS ---
BOT_TOKEN = "8656586503:AAFoIeYyqJei6I0KKMAPGbpafP52Pb4o8lo"  # <--- Put your BotFather token here
ADMIN_ID = 6311691133                            # Your numeric administrator ID
RENDER_PORT = int(os.environ.get("PORT", 10000))

# Initialize bot and dispatcher for aiogram 3.x
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- WEB SERVER FOR RENDER ---

async def handle_web_request(request):
    return web.Response(text=f"Bot successfully running for administrator ID: {ADMIN_ID}!")

app = web.Application()
app.router.add_get('/', handle_web_request)

# --- YOUR COMMANDS AND MENU ---

@dp.message(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"Hello, boss! This is the admin panel (Your ID: {ADMIN_ID}).")
    else:
        await message.answer(f"Hello, {message.from_user.first_name}! Welcome to Food Delivery.")


# --- LAUNCH ---

async def main():
    # Setup web server
    web_runner = web.AppRunner(app)
    await web_runner.setup()
    site = web.TCPSite(web_runner, '0.0.0.0', RENDER_PORT)
    await site.start()
    logging.info(f"Web server started on port {RENDER_PORT}")

    # Start bot polling
    logging.info(f"Bot started! Admin ID: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
