import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# 1. Вставьте токен вашего бота
TOKEN = "8656586503:AAEt1DJvxcTkgpJXk5ovI385iLZZ6QQskFk"

# 2. Вставьте ваш Telegram ID (не username, а именно цифровой ID!)
# Чтобы узнать свой ID, напишите в Telegram боту @userinfobot
ADMIN_ID = 6311691133  # <- Замените на ваши цифры

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
