import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
ТОКЕН_БОТА = "8656586503:AAFoIeYyqJei6I0KKMAPGbpafP52Pb4o8lo"  # <--- Сюда токен от BotFather
АДМИН_ЮЗЕРНЕЙМ = "@Dldiiprdn6666"               # Твой юзернейм на русском языке в коде
ПОРТ_РЕНДЕР = int(os.environ.get("PORT", 10000))

# Инициализация бота
бот = Bot(token=ТОКЕН_БОТА)
хранилище = MemoryStorage()
диспетчер = Dispatcher(бот, storage=хранилище)

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы ошибка порта пропала) ---

async def обработка_веб_запроса(запрос):
    return web.Response(text=f"Бот успешно запущен для {АДМИН_ЮЗЕРНЕЙМ}!")

приложение = web.Application()
приложение.router.add_get('/', обработка_веб_запроса)

async def при_запуске(dp):
    logging.info(f"Бот запущен! Администратор: {АДМИН_ЮЗЕРНЕЙМ}")

async def при_остановке(dp):
    await бот.session.close()

# --- ТВОИ КОМАНДЫ И МЕНЮ ---

@диспетчер.message_handler(commands=['start'])
async def приветствие(сообщение: types.Message):
    await сообщение.reply(f"Привет, {сообщение.from_user.first_name}! Добро пожаловать в Доставку Еды.\nАдминистратор: {АДМИН_ЮЗЕРНЕЙМ}")


# --- ЗАПУСК ---

if __name__ == "__main__":
    веб_раннер = web.AppRunner(приложение)
    
    async def запустить_сервисы():
        await веб_раннер.setup()
        сайт = web.TCPSite(веб_раннер, '0.0.0.0', ПОРТ_РЕНДЕР)
        await сайт.start()
        logging.info(f"Веб-сервер запущен на порту {ПОРТ_РЕНДЕР}")

        # Запуск бота
        executor.start_polling(диспетчер, skip_updates=True, on_startup=при_запуске, on_shutdown=при_остановке)

    цикл = asyncio.new_event_loop()
    asyncio.set_event_loop(цикл)
    цикл.run_until_complete(запустить_сервисы())
