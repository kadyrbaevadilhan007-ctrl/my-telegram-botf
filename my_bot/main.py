import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

# -------------------------------------------------------------
# НАСТРОЙКИ
# -------------------------------------------------------------
API_TOKEN = '8656586503:AAEt1DjvxcTkgpJXk5ov13B5ltZZ6QQsKFk'
ADMIN_ID = 6311691133  # Твой Telegram ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Корзина (в памяти)
user_carts = {}

# МЕНЮ
MENU = {
    "🍔 Бургеры": [
        {"id": "b1", "name": "Чизбургер XL", "price": 250},
        {"id": "b2", "name": "Двойной Бургер", "price": 380},
    ],
    "🍕 Пицца": [
        {"id": "p1", "name": "Пепперони (30 см)", "price": 500},
        {"id": "p2", "name": "4 Сыра (30 см)", "price": 550},
    ],
    "🍟 Закуски и Напитки": [
        {"id": "z1", "name": "Картофель Фри", "price": 140},
        {"id": "d1", "name": "Coca-Cola 0.5л", "price": 90},
    ]
}

TOPPINGS = [
    {"id": "t1", "name": "🧀 Доп. сыр", "price": 50},
    {"id": "t2", "name": "🥓 Бекон", "price": 70},
    {"id": "t3", "name": "🌶️ Халапеньо", "price": 40}
]

# КЛАВИАТУРЫ
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍔 Выбрать Еду", "🛒 Корзина")
    kb.add("📞 Контакты")
    return kb

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 **Добро пожаловать в Доставку Еды!**\nВыберите раздел в меню ниже:", reply_markup=main_kb(), parse_mode="Markdown")

@dp.message_handler(lambda m: m.text == "🍔 Выбрать Еду")
async def show_menu(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for cat in MENU.keys():
        kb.add(InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}"))
    await message.answer("Категории меню:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('cat_'))
async def show_items(call: types.CallbackQuery):
    cat_name = call.data.split('_')[1]
    items = MENU.get(cat_name, [])
    await call.answer()
    
    for item in items:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➕ В корзину", callback_data=f"add_{item['name']}_{item['price']}"))
        kb.add(InlineKeyboardButton("➕ Добавить соус/сыр", callback_data="show_tops"))
        await bot.send_message(call.from_user.id, f"**{item['name']}**\nЦена: {item['price']} сом", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == 'show_tops')
async def show_toppings(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup()
    for top in TOPPINGS:
        kb.add(InlineKeyboardButton(f"{top['name']} (+{top['price']} сом)", callback_data=f"add_{top['name']}_{top['price']}"))
    await bot.send_message(call.from_user.id, "Выберите добавку:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('add_'))
async def add_to_cart(call: types.CallbackQuery):
    _, name, price = call.data.split('_')
    uid = call.from_user.id
    if uid not in user_carts:
        user_carts[uid] = []
    user_carts[uid].append({"name": name, "price": int(price)})
    await call.answer(f"✅ Добавлено: {name}", show_alert=True)

@dp.message_handler(lambda m: m.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    uid = message.from_user.id
    cart = user_carts.get(uid, [])
    if not cart:
        await message.answer("Корзина пуста!")
        return
    
    total = sum(i['price'] for i in cart)
    text = "🛒 **Ваш заказ:**\n\n" + "\n".join([f"• {i['name']} — {i['price']} сом" for i in cart])
    text += f"\n\n**Итого: {total} сом**\n\nДля заказа напишите ваш адрес и телефон одним сообщением!"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Отправить заказ админу", callback_data="send_order"))
    kb.add(InlineKeyboardButton("🗑️ Очистить", callback_data="clear"))
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "clear")
async def clear_cart(call: types.CallbackQuery):
    user_carts[call.from_user.id] = []
    await call.answer("Корзина очищена!")
    await bot.send_message(call.from_user.id, "Корзина пуста.")

@dp.callback_query_handler(lambda c: c.data == "send_order")
async def send_order(call: types.CallbackQuery):
    uid = call.from_user.id
    cart = user_carts.get(uid, [])
    if not cart:
        await call.answer("Корзина пуста!")
        return
    
    total = sum(i['price'] for i in cart)
    items_text = "\n".join([f"• {i['name']} ({i['price']} сом)" for i in cart])
    
    admin_msg = (
        f"🚨 **НОВЫЙ ЗАКАЗ!**\n"
        f"👤 От: {call.from_user.full_name} (@{call.from_user.username})\n\n"
        f"Состав:\n{items_text}\n\n"
        f"💰 **Сумма: {total} сом**"
    )
    
    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    user_carts[uid] = []
    await call.answer("Заказ отправлен!", show_alert=True)
    await bot.send_message(uid, "🎉 Ваш заказ успешно отправлен администратору!")

@dp.message_handler(lambda m: m.text == "📞 Контакты")
async def contacts(message: types.Message):
    await message.answer("📞 Телефон: +996 555 12 34 56\n📍 Адрес: г. Талас")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
