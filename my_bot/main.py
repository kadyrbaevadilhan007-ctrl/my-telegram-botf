import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# 1. Токен вашего бота
TOKEN = "8656586503:AAFoIeYyqJei6I0KKMAPGbpafP52Pb4o8lo"

# 2. Ваш Telegram ID
ADMIN_ID = 6311691133

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- ВЕБ-СЕРВЕР И АВТО-ПИНГЕР ДЛЯ RENDER ---

async def handle(request):
    return web.Response(text="Бот активен и работает 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port}")

async def self_ping():
    """Встроенный пингер: стучится на собственный адрес Render каждые 5 минут"""
    await asyncio.sleep(15)
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if url:
        import aiohttp
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        logging.info(f"Авто-пинг выполнен, статус: {response.status}")
            except Exception as e:
                logging.error(f"Ошибка авто-пинга: {e}")
            await asyncio.sleep(300)   каждые 5 минут


# --- КЛАВИАТУРЫ ---


def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="🍕 Меню / Товары", callback_data="catalog")],
        [
            InlineKeyboardButton(text="ℹ️ О нас", callback_data="about"),
            InlineKeyboardButton(
                text="📞 Контакты", callback_data="contacts"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_catalog_menu():
    kb = [
        [
            InlineKeyboardButton(
                text="🍕 Пепперони — 450 сом", callback_data="order_pizza"
            )
        ],
        [
            InlineKeyboardButton(
                text="🥤 Кола — 80 сом", callback_data="order_drink"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню", callback_data="back_to_main"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_back_button():
    kb = [
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню", callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# --- ХЕНДЛЕРЫ ---


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! 👋\n\n"
        "Выберите нужный раздел в меню ниже:",
        reply_markup=get_main_menu(),
    )


@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📋 **Наше меню:**\nВыберите позицию для заказа:",
        reply_markup=get_catalog_menu(),
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ **О нас:**\nМы готовим самую вкусную еду в городе!\n⏰ С 10:00 до 22:00 ежедневно.",
        reply_markup=get_back_button(),
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.callback_query(F.data == "contacts")
async def show_contacts(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📞 **Наши контакты:**\n📍 г. Талас, ул. Центральная, 12\n📱 WhatsApp: +996 (XXX) XX-XX-XX",
        reply_markup=get_back_button(),
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите нужный раздел в меню ниже:", reply_markup=get_main_menu()
    )
    await callback.answer()


# --- ОБРАБОТКА ЗАКАЗА И ОТПРАВКА УВЕДОМЛЕНИЯ АДМИНУ ---


@dp.callback_query(F.data.startswith("order_"))
async def process_order(callback: types.CallbackQuery):
    # Определяем товар
    item_name = "Пепперони (450 сом)" if callback.data == "order_pizza" else "Кола (80 сом)"

    # Получаем данные покупателя
    user_first_name = callback.from_user.first_name
    username = callback.from_user.username

    # Формируем юзернейм для ссылки
    if username:
        user_contact = f"@{username}"
    else:
        user_contact = f"Без @username (ID: {callback.from_user.id})"

    # 1. Отправляем уведомление владельцу / в группу
    admin_text = (
        f"🚨 **НОВЫЙ ЗАКАЗ!** 🚨\n\n"
        f"🛒 **Товар:** {item_name}\n"
        f"👤 **Покупатель:** {user_first_name}\n"
        f"💬 **Связь:** {user_contact}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу: {e}")

    # 2. Отвечаем клиенту
    await callback.message.answer(
        f"✅ Ваш заказ на **{item_name}** принят!\n"
        f"Менеджер скоро свяжется с вами ({user_contact}).",
        parse_mode="Markdown",
    )
    await callback.answer("Заказ оформлен!")


# --- ЗАПУСК ---


async def main():
    # Запускаем веб-сервер и встроенный пингер
    asyncio.create_task(start_web_server())
    asyncio.create_task(self_ping())
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
