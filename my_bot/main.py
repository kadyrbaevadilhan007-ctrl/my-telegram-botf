import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# -------------------------------------------------------------
# НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ)
# -------------------------------------------------------------
API_TOKEN = '8656586503:AAEt1DJvxcTkgpJXk5ovI385iLZZ6QQskFk'
ADMIN_ID = 6311691133  # Вставьте сюда ваш Telegram ID (куда придут заказы)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для оформления заказа
class OrderProcess(StatesGroup):
    waiting_for_address = State()
    waiting_for_phone = State()

# Временная корзина пользователей (в памяти)
user_carts = {}

# -------------------------------------------------------------
# МЕНЮ ТОВАРОВ И ИНГРЕДИЕНТОВ
# -------------------------------------------------------------
MENU = {
    "🍔 Бургеры": [
        {"id": "b1", "name": "Чизбургер XL", "price": 250, "desc": "Сочная говядина, сыр чеддер, маринованные огурчики, соус"},
        {"id": "b2", "name": "Двойной Двойной", "price": 380, "desc": "Две котлеты, двойной сыр, лук гриль, фирменный соус"},
        {"id": "b3", "name": "Острый Шеф-Бургер", "price": 300, "desc": "Куриное филе, халапеньо, острый соус спайси, салат"}
    ],
    "🍕 Пицца": [
        {"id": "p1", "name": "Пепперони (30 см)", "price": 500, "desc": "Пикантная пепперони, моцарелла, фирменный томатный соус"},
        {"id": "p2", "name": "4 Сыра (30 см)", "price": 550, "desc": "Моцарелла, пармезан, дор блю, чеддер"},
        {"id": "p3", "name": "Мясная Супер (35 см)", "price": 680, "desc": "Ветчина, пепперони, бекон, фарш, соус BBQ"}
    ],
    "🍟 Закуски и Соусы": [
        {"id": "z1", "name": "Картофель Фри XL", "price": 140, "desc": "Хрустящий картофель с солью"},
        {"id": "z2", "name": "Наггетсы (9 шт)", "price": 200, "desc": "Сочное куриное филе в панировке"},
        {"id": "z3", "name": "Сырный соус", "price": 40, "desc": "Классический сырный соус"}
    ],
    "🥤 Напитки": [
        {"id": "d1", "name": "Coca-Cola 0.5л", "price": 90, "desc": "Охлажденная"},
        {"id": "d2", "name": "Fanta 0.5л", "price": 90, "desc": "Охлажденная"},
        {"id": "d3", "name": "Сок Добрый 1л", "price": 160, "desc": "В ассортименте"}
    ]
}

# Добавки / Дополнительные ингредиенты
TOPPINGS = {
    "top_cheese": {"name": "🧀 Доп. сыр Чеддер", "price": 50},
    "top_bacon": {"name": "🥓 Доп. Бекон", "price": 70},
    "top_jalapeno": {"name": "🌶️ Халапеньо (острое)", "price": 40},
    "top_sauce": {"name": "🥫 Фирменный соус", "price": 30}
}

# -------------------------------------------------------------
# КЛАВИАТУРЫ
# -------------------------------------------------------------
def main_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🍔 Выбрать Еду", "🛒 Корзина")
    kb.add("ℹ️ О доставке", "📞 Контакты")
    return kb

def categories_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for category in MENU.keys():
        kb.insert(InlineKeyboardButton(text=category, callback_data=f"cat_{category}"))
    return kb

# -------------------------------------------------------------
# ОБРАБОТЧИКИ КОМАНД
# -------------------------------------------------------------
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в службу быстрой доставки Фастфуда!**\n\n"
        "Выбирайте вкуснейшие бургеры, пиццу и напитки. Мы доставим всё горячим!",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@dp.message_handler(lambda msg: msg.text in ["🍔 Выбрать Еду", "Каталог"])
async def show_categories(message: types.Message):
    await message.answer("Выберите категорию меню:", reply_markup=categories_keyboard())

@dp.message_handler(lambda msg: msg.text == "ℹ️ О доставке")
async def show_info(message: types.Message):
    await message.answer(
        "🚀 **Информация о доставке:**\n"
        "• Доставка по городу: от 100 сом\n"
        "• Время доставки: 30-45 минут\n"
        "• Бесплатная доставка при заказе от 1500 сом!",
        parse_mode="Markdown"
    )

@dp.message_handler(lambda msg: msg.text == "📞 Контакты")
async def show_contacts(message: types.Message):
    await message.answer("📞 Наш телефон: +996 555 12 34 56\n📍 Адрес: г. Талас, ул. Ленина 100")

# -------------------------------------------------------------
# ПОКАЗ ТОВАРОВ И ДОБАВОК
# -------------------------------------------------------------
@dp.callback_query_handler(lambda c: c.data.startswith('cat_'))
async def show_items(callback_query: types.CallbackQuery):
    cat_name = callback_query.data.split('_')[1]
    items = MENU.get(cat_name, [])
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"--- **{cat_name}** ---", parse_mode="Markdown")

    for item in items:
        caption = f"**{item['name']}**\n_{item['desc']}_\n\n💰 Цена: **{item['price']} сом**"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➕ В корзину", callback_data=f"add_{item['id']}"))
        kb.add(InlineKeyboardButton("🧀 Добавить ингредиенты", callback_data=f"top_{item['id']}"))
        
        await bot.send_message(callback_query.from_user.id, caption, reply_markup=kb, parse_mode="Markdown")

# Добавление ингредиентов
@dp.callback_query_handler(lambda c: c.data.startswith('top_'))
async def show_toppings(callback_query: types.CallbackQuery):
    item_id = callback_query.data.split('_')[1]
    
    kb = InlineKeyboardMarkup(row_width=1)
    for top_code, top_info in TOPPINGS.items():
        kb.add(InlineKeyboardButton(
            f"{top_info['name']} (+{top_info['price']} сом)", 
            callback_data=f"addtop_{item_id}_{top_code}"
        ))
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Выберите дополнительный ингредиент:", reply_markup=kb)

# Добавление товара / ингредиента в корзину
@dp.callback_query_handler(lambda c: c.data.startswith(('add_', 'addtop_')))
async def add_to_cart(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_carts:
        user_carts[user_id] = []

    data = callback_query.data.split('_')
    
    if data[0] == 'add':
        item_id = data[1]
        for cat in MENU.values():
            for item in cat:
                if item['id'] == item_id:
                    user_carts[user_id].append({"name": item['name'], "price": item['price']})
                    await bot.answer_callback_query(callback_query.id, f"✅ {item['name']} добавлен в корзину!")
                    return

    elif data[0] == 'addtop':
        top_code = data[2]
        top_info = TOPPINGS.get(top_code)
        if top_info:
            user_carts[user_id].append({"name": top_info['name'], "price": top_info['price']})
            await bot.answer_callback_query(callback_query.id, f"✅ Добавлено: {top_info['name']}")

# -------------------------------------------------------------
# КОРЗИНА И ОФОРМЛЕНИЕ ЗАКАЗА
# -------------------------------------------------------------
@dp.message_handler(lambda msg: msg.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])

    if not cart:
        await message.answer("🛒 Ваша корзина пуста. Выберите что-нибудь вкусное в меню!")
        return

    total = sum(item['price'] for item in cart)
    cart_text = "🛒 **Ваш заказ:**\n\n"
    for idx, item in enumerate(cart, 1):
        cart_text += f"{idx}. {item['name']} — **{item['price']} сом**\n"
    
    cart_text += f"\nИтого к оплате: **{total} сом**"

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Оформить доставку", callback_data="checkout"))
    kb.add(InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"))

    await message.answer(cart_text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "clear_cart")
async def clear_cart(callback_query: types.CallbackQuery):
    user_carts[callback_query.from_user.id] = []
    await bot.answer_callback_query(callback_query.id, "Корзина очищена!")
    await bot.send_message(callback_query.from_user.id, "Ваша корзина теперь пуста.")

# Оформление через FSM (запрос адреса и телефона)
@dp.callback_query_handler(lambda c: c.data == "checkout")
async def start_checkout(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await OrderProcess.waiting_for_address.set()
    await bot.send_message(callback_query.from_user.id, "📍 Укажите **адрес доставки** (улица, дом, квартира):", parse_mode="Markdown")

@dp.message_handler(state=OrderProcess.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await OrderProcess.next()
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Отправить номер", request_contact=True))
    
    await message.answer("📱 Напишите ваш **номер телефона** для связи (или нажмите кнопку внизу):", reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.CONTACT], state=OrderProcess.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    user_data = await state.get_data()
    address = user_data['address']
    
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    total = sum(item['price'] for item in cart)

    # Сообщение клиенту
    await message.answer("🎉 **Спасибо! Ваш заказ принят и передан на кухню.**\nМенеджер свяжется с вами для подтверждения.", reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    # Формируем заказ для АДМИНА
    order_items = "\n".join([f"• {item['name']} ({item['price']} сом)" for item in cart])
    admin_text = (
        f"🚨 **НОВЫЙ ЗАКАЗ!**\n\n"
        f"👤 Клиент: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"📞 Телефон: `{phone}`\n"
        f"📍 Адрес: `{address}`\n\n"
        f"🍔 **Состав заказа:**\n{order_items}\n\n"
        f"💰 **Сумма:** {total} сом"
    )

    # Отправляем сообщение администратору
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить заказ админу: {e}")

    # Очищаем корзину и сбрасываем состояние
    user_carts[user_id] = []
    await state.finish()

# -------------------------------------------------------------
# ЗАПУСК
# -------------------------------------------------------------
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
