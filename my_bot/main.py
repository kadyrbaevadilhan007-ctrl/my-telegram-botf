import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Токен вашего бота
TOKEN = "8656586503:AAFoIeYyqJei6I0KKMAPGbpafP52Pb4o8lo"
# Ваш Telegram ID
ADMIN_ID = 6311691133

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР И АВТО-ПИНГЕР ДЛЯ RENDER (24/7) ---

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
    """Встроенный пингер для Render"""
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
            await asyncio.sleep(300)


# --- ХРАНИЛИЩЕ КОРЗИН ПОЛЬЗОВАТЕЛЕЙ ---
user_carts = {}
user_additions = {}


# --- ГЛАВНАЯ КЛАВИАТУРА (НИЖНЯЯ) ---
def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Выбрать Еду"), KeyboardButton(text="🛒 Корзина")],
            [KeyboardButton(text="📞 Контакты")]
        ],
        resize_keyboard=True
    )


# --- КАТЕГОРИИ МЕНЮ ---
def get_categories_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Бургеры", callback_data="cat_burgers")],
            [InlineKeyboardButton(text="🍕 Пицца", callback_data="cat_pizza")],
            [InlineKeyboardButton(text="🍟 Закуски и Напитки", callback_data="cat_snacks")]
        ]
    )


# --- ТОВАРЫ ПО КАТЕГОРИЯМ ---
def get_burgers_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Чизбургер XL - 250 сом", callback_data="add_burger_xl")],
            [InlineKeyboardButton(text="+ В корзину", callback_data="cart_burger_xl"),
             InlineKeyboardButton(text="+ Добавить соус/сыр", callback_data="add_to_burger_xl")],
            [InlineKeyboardButton(text="Двойной Бургер - 380 сом", callback_data="add_burger_double")],
            [InlineKeyboardButton(text="+ В корзину", callback_data="cart_burger_double"),
             InlineKeyboardButton(text="+ Добавить соус/сыр", callback_data="add_to_burger_double")],
            [InlineKeyboardButton(text="⬅️ Категории меню", callback_data="back_to_categories")]
        ]
    )


def get_pizza_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пепперони (30 см) - 500 сом", callback_data="cart_pizza_pep")],
            [InlineKeyboardButton(text="4 Сыра (30 см) - 550 сом", callback_data="cart_pizza_4cheese")],
            [InlineKeyboardButton(text="⬅️ Категории меню", callback_data="back_to_categories")]
        ]
    )


def get_snacks_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Картофель Фри - 140 сом", callback_data="cart_fries")],
            [InlineKeyboardButton(text="+ В корзину", callback_data="cart_fries_add")],
            [InlineKeyboardButton(text="Coca-Cola 0.5л - 90 сом", callback_data="cart_cola")],
            [InlineKeyboardButton(text="+ В корзину", callback_data="cart_cola_add")],
            [InlineKeyboardButton(text="⬅️ Категории меню", callback_data="back_to_categories")]
        ]
    )


def get_additions_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧀 Доп. сыр (+50 сом)", callback_data="add_cheese")],
            [InlineKeyboardButton(text="🥓 Бекон (+70 сом)", callback_data="add_bacon")],
            [InlineKeyboardButton(text="🌶 Халапеньо (+40 сом)", callback_data="add_jalapeno")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="cat_burgers")]
        ]
    )


def get_cart_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить заказ админу", callback_data="send_order")],
            [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart")]
        ]
    )


# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в Доставку Еды!\nВыберите раздел в меню ниже:",
        reply_markup=get_main_reply_keyboard()
    )


@dp.message(F.text == "🍔 Выбрать Еду")
async def show_food_categories(message: types.Message):
    await message.answer("Категории меню:", reply_markup=get_categories_keyboard())


@dp.message(F.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    additions = user_additions.get(user_id, [])

    if not cart and not additions:
        await message.answer("🛒 Корзина пуста!")
        return

    text = "🛒 **Ваш заказ:**\n\n"
    total = 0

    items_prices = {
        "Двойной Бургер": 380,
        "Чизбургер XL": 250,
        "Пепперони (30 см)": 500,
        "4 Сыра (30 см)": 550,
        "Картофель Фри": 140,
        "Coca-Cola 0.5л": 90,
        "Доп. сыр": 50,
        "Бекон": 70,
        "Халапеньо": 40
    }

    all_items = cart + additions
    for item in all_items:
        price = items_prices.get(item, 0)
        total += price
        text += f"• {item} — {price} сом\n"

    text += f"\n💰 **Итого: {total} сом**"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_cart_keyboard())


@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: types.Message):
    await message.answer("📞 Телефон: +996 555 12 34 56\n📍 Адрес: г. Талас", reply_markup=get_main_reply_keyboard())


# --- ОБРАБОТЧИКИ КНОПОК МЕНЮ ---

@dp.callback_query(F.data == "cat_burgers")
async def open_burgers(callback: types.CallbackQuery):
    await callback.message.edit_text("🍔 **Бургеры:**", reply_markup=get_burgers_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "cat_pizza")
async def open_pizza(callback: types.CallbackQuery):
    await callback.message.edit_text("🍕 **Пицца:**", reply_markup=get_pizza_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "cat_snacks")
async def open_snacks(callback: types.CallbackQuery):
    await callback.message.edit_text("🍟 **Закуски и Напитки:**", reply_markup=get_snacks_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery):
    await callback.message.edit_text("Категории меню:", reply_markup=get_categories_keyboard())
    await callback.answer()


# --- ДОБАВЛЕНИЕ ТОВАРОВ В КОРЗИНУ ---

@dp.callback_query(F.data.in_({"cart_burger_xl", "add_burger_xl"}))
async def add_burger_xl(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append("Чизбургер XL")
    await callback.answer("✅ Добавлено: Чизбургер XL", show_alert=True)

@dp.callback_query(F.data.in_({"cart_burger_double", "add_burger_double"}))
async def add_burger_double(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append("Двойной Бургер")
    await callback.answer("✅ Добавлено: Двойной Бургер", show_alert=True)

@dp.callback_query(F.data.startswith("add_to_burger"))
async def open_additions(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите добавку:", reply_markup=get_additions_keyboard())
    await callback.answer()

@dp.callback_query(F.data.in_({"add_cheese", "add_bacon", "add_jalapeno"}))
async def add_addition(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    names = {"add_cheese": "Доп. сыр", "add_bacon": "Бекон", "add_jalapeno": "Халапеньо"}
    item = names[callback.data]
    user_additions.setdefault(user_id, []).append(item)
    await callback.answer(f"✅ Добавлено: {item}", show_alert=True)

@dp.callback_query(F.data == "cart_pizza_pep")
async def add_pizza_pep(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append("Пепперони (30 см)")
    await callback.answer("✅ Добавлено: Пепперони (30 см)", show_alert=True)

@dp.callback_query(F.data == "cart_pizza_4cheese")
async def add_pizza_4cheese(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append("4 Сыра (30 см)")
    await callback.answer("✅ Добавлено: 4 Сыра (30 см)", show_alert=True)

@dp.callback_query(F.data.in_({"cart_fries", "cart_fries_add"}))
async def add_fries(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append("Картофель Фри")
    await callback.answer("✅ Добавлено: Картофель Фри", show_alert=True)

@dp.callback_query(F.data.in_({"cart_cola", "cart_cola_add"}))
async def add_cola(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append("Coca-Cola 0.5л")
    await callback.answer("✅ Добавлено: Coca-Cola 0.5л", show_alert=True)


# --- ОФОРМЛЕНИЕ ЗАКАЗА ---

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    user_additions[user_id] = []
    await callback.message.edit_text("🗑 Корзина очищена!")
    await callback.answer()

@dp.callback_query(F.data == "send_order")
async def send_order(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    additions = user_additions.get(user_id, [])

    if not cart and not additions:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    user_name = callback.from_user.first_name
    username = callback.from_user.username
    user_contact = f"@{username}" if username else "(@None)"

    items_prices = {
        "Двойной Бургер": 380,
        "Чизбургер XL": 250,
        "Пепперони (30 см)": 500,
        "4 Сыра (30 см)": 550,
        "Картофель Фри": 140,
        "Coca-Cola 0.5л": 90,
        "Доп. сыр": 50,
        "Бекон": 70,
        "Халапеньо": 40
    }

    total = 0
    order_details = ""
    all_items = cart + additions
    for item in all_items:
        price = items_prices.get(item, 0)
        total += price
        order_details += f"• {item} ({price} сом)\n"

    admin_text = (
        f"🚨 **НОВЫЙ ЗАКАЗ!** 🚨\n"
        f"👤 **От:** {user_name} {user_contact}\n\n"
        f"**Состав:**\n{order_details}\n"
        f"💰 **Сумма:** {total} сом"
    )

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")

    await callback.message.edit_text(
        "✅ Ваш заказ успешно отправлен администратору!\n"
        "Менеджер скоро свяжется с вами.",
        parse_mode="Markdown"
    )
    
    user_carts[user_id] = []
    user_additions[user_id] = []
    await callback.answer("Заказ отправлен!")


# --- ЗАПУСК ---

async def main():
    asyncio.create_task(start_web_server())
    asyncio.create_task(self_ping())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
