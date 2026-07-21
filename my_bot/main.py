import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiohttp import web

# Logging setup
logging.basicConfig(level=logging.INFO)

# --- SETTINGS ---
BOT_TOKEN = "8656586503:AAFoIeYyqJei6I0KKMAPGbpafP52Pb4o8lo"  # <--- Put your BotFather token here
ADMIN_ID = 6311691133                            # Your numeric administrator ID
RENDER_PORT = int(os.environ.get("PORT", 10000))

# Initialize bot
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- WEB SERVER FOR RENDER (to fix the port error) ---

async def handle_web_request(request):
    return web.Response(text=f"Bot successfully running for administrator ID: {ADMIN_ID}!")

app = web.Application()
app.router.add_get('/', handle_web_request)

async def on_startup(dispatcher):
    logging.info(f"Bot started! Admin ID: {ADMIN_ID}")

async def on_shutdown(dispatcher):
    await bot.session.close()

# --- YOUR COMMANDS AND MENU ---

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply(f"Hello, boss! This is the admin panel (Your ID: {ADMIN_ID}).")
    else:
        await message.reply(f"Hello, {message.from_user.first_name}! Welcome to Food Delivery.")


# --- LAUNCH ---

if __name__ == "__main__":
    web_runner = web.AppRunner(app)
    
    async def run_services():
        await web_runner.setup()
        site = web.TCPSite(web_runner, '0.0.0.0', RENDER_PORT)
        await site.start()
        logging.info(f"Web server started on port {RENDER_PORT}")

        # Start bot polling
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_services())
