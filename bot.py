import asyncio
import random
import asyncpg
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# ================= CONFIG =================

TOKEN = "8567616083:AAEMxupDrVRtBISJ-oRqouYDlLVh6t9fjJ8"
ADMIN_ID = 8465432674

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не найден в Railway Variables")

bot = Bot(token=TOKEN)
dp = Dispatcher()

db = None

EVENT_MULTIPLIER = 1

# ================= VIP SYSTEM =================

VIP_NAMES = {
    0: "Нет",
    1: "VIP x2",
    2: "VIP x5",
    3: "VIP x10",
    4: "SECRET VIP x25"
}

def vip_multiplier(vip):

    if vip == 1:
        return 2

    elif vip == 2:
        return 5

    elif vip == 3:
        return 10

    elif vip == 4:
        return 25

    return 1

# ================= DATABASE =================

async def db_start():
    global db

    db = await asyncpg.connect(DATABASE_URL)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        money BIGINT DEFAULT 0,
        power BIGINT DEFAULT 1,
        autoclick BIGINT DEFAULT 0,
        vip BIGINT DEFAULT 0
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY,
        reward BIGINT,
        activations BIGINT
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS promo_uses (
        user_id BIGINT,
        code TEXT
    )
    """)

# ================= USER =================

async def create_user(user_id):

    user = await db.fetchrow("""
    SELECT * FROM users
    WHERE user_id = $1
    """, user_id)

    if user is None:

        await db.execute("""
        INSERT INTO users (user_id)
        VALUES ($1)
        """, user_id)

async def get_user(user_id):

    await create_user(user_id)

    user = await db.fetchrow("""
    SELECT *
    FROM users
    WHERE user_id = $1
    """, user_id)

    return user

# ================= MENU =================

def menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💰 Клик",
                    callback_data="click"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🛒 Улучшить",
                    callback_data="upgrade"
                ),

                InlineKeyboardButton(
                    text="🤖 Автоклик",
                    callback_data="autoclick"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎰 Казино",
                    callback_data="casino"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎁 Промокод",
                    callback_data="promo_menu"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 Профиль",
                    callback_data="profile"
                ),

                InlineKeyboardButton(
                    text="🏆 Топ",
                    callback_data="top"
                )
            ]
        ]
    )

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):

    await create_user(message.from_user.id)

    await message.answer(
        "🎮 CLICKER BOT\n\nДобро пожаловать!",
        reply_markup=menu()
    )

# ================= CLICK =================

@dp.callback_query(F.data == "click")
async def click(callback: CallbackQuery):

    global EVENT_MULTIPLIER

    user_id = callback.from_user.id

    user = await get_user(user_id)

    money = user["money"]
    power = user["power"]
    vip = user["vip"]

    vip_bonus = vip_multiplier(vip)

    earn = power * vip_bonus * EVENT_MULTIPLIER

    money += earn

    await db.execute("""
    UPDATE users
    SET money = $1
    WHERE user_id = $2
    """, money, user_id)

    await callback.message.edit_text(
        f"💰 +{earn} монет\n\n"
        f"💵 Баланс: {money}\n"
        f"⚡ Сила: {power}\n"
        f"💎 {VIP_NAMES[vip]}\n"
        f"🎉 EVENT x{EVENT_MULTIPLIER}",
        reply_markup=menu()
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    await callback.message.edit_text(
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Монеты: {user['money']}\n"
        f"⚡ Сила: {user['power']}\n"
        f"🤖 Автоклик: {user['autoclick']}\n"
        f"💎 VIP: {VIP_NAMES[user['vip']]}",
        reply_markup=menu()
    )

# ================= UPGRADE =================

@dp.callback_query(F.data == "upgrade")
async def upgrade(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = await get_user(user_id)

    money = user["money"]
    power = user["power"]

    price = power * 50

    if money < price:

        await callback.answer(
            f"Нужно {price} монет",
            show_alert=True
        )
        return

    money -= price
    power += 1

    await db.execute("""
    UPDATE users
    SET money = $1, power = $2
    WHERE user_id = $3
    """, money, power, user_id)

    await callback.message.edit_text(
        f"🚀 Улучшение куплено!\n\n"
        f"⚡ Сила: {power}\n"
        f"💰 Баланс: {money}",
        reply_markup=menu()
    )

# ================= AUTOCLICK =================

@dp.callback_query(F.data == "autoclick")
async def autoclick(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = await get_user(user_id)

    money = user["money"]
    autoclick = user["autoclick"]

    price = (autoclick + 1) * 200

    if money < price:

        await callback.answer(
            f"Нужно {price} монет",
            show_alert=True
        )
        return

    money -= price
    autoclick += 1

    await db.execute("""
    UPDATE users
    SET money = $1, autoclick = $2
    WHERE user_id = $3
    """, money, autoclick, user_id)

    await callback.message.edit_text(
        f"🤖 Автоклик улучшен!\n\n"
        f"🤖 Уровень: {autoclick}\n"
        f"💰 Баланс: {money}",
        reply_markup=menu()
    )

# ================= AUTOCLICK LOOP =================

async def autoclick_loop():

    while True:

        users = await db.fetch("""
        SELECT user_id, autoclick, vip
        FROM users
        """)

        for user in users:

            if user["autoclick"] > 0:

                earn = (
                    user["autoclick"]
                    * vip_multiplier(user["vip"])
                    * EVENT_MULTIPLIER
                )

                await db.execute("""
                UPDATE users
                SET money = money + $1
                WHERE user_id = $2
                """, earn, user["user_id"])

        await asyncio.sleep(5)

# ================= TOP =================

@dp.callback_query(F.data == "top")
async def top(callback: CallbackQuery):

    users = await db.fetch("""
    SELECT user_id, money
    FROM users
    ORDER BY money DESC
    LIMIT 10
    """)

    text = "🏆 ТОП ИГРОКОВ\n\n"

    place = 1

    for user in users:

        text += (
            f"{place}. "
            f"<code>{user['user_id']}</code> — "
            f"{user['money']} монет\n"
        )

        place += 1

    await callback.message.edit_text(
        text,
        reply_markup=menu()
    )

# ================= EVENT =================

@dp.message(Command("event"))
async def event(message: Message):

    global EVENT_MULTIPLIER

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 2:
        await message.answer(
            "/event множитель"
        )
        return

    EVENT_MULTIPLIER = int(args[1])

    # Сообщение админу
    await message.answer(
        f"🎉 EVENT x{EVENT_MULTIPLIER} включен"
    )

    # Рассылка игрокам
    users = await db.fetch("""
    SELECT user_id
    FROM users
    """)

    success = 0

    for user in users:

        try:

            await bot.send_message(
                user["user_id"],
                f"🎉 НАЧАЛСЯ EVENT!\n\n"
                f"🔥 Множитель: x{EVENT_MULTIPLIER}\n\n"
                f"💰 Зарабатывайте больше монет!"
            )

            success += 1

        except:
            pass

    await message.answer(
        f"✅ Уведомление отправлено {success} игрокам"
    )

# ================= STOP EVENT =================

@dp.message(Command("stopevent"))
async def stopevent(message: Message):

    global EVENT_MULTIPLIER

    if message.from_user.id != ADMIN_ID:
        return

    EVENT_MULTIPLIER = 1

    # Сообщение админу
    await message.answer(
        "❌ EVENT остановлен"
    )

    # Рассылка игрокам
    users = await db.fetch("""
    SELECT user_id
    FROM users
    """)

    success = 0

    for user in users:

        try:

            await bot.send_message(
                user["user_id"],
                "❌ EVENT завершен\n\n"
                "💰 Множитель снова x1"
            )

            success += 1

        except:
            pass

    await message.answer(
        f"✅ Уведомление отправлено {success} игрокам"
    )

# ================= GIVE MONEY =================

@dp.message(Command("givemoney"))
async def givemoney(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "/givemoney user_id amount"
        )
        return

    user_id = int(args[1])
    amount = int(args[2])

    await db.execute("""
    UPDATE users
    SET money = money + $1
    WHERE user_id = $2
    """, amount, user_id)

    # Сообщение админу
    await message.answer(
        f"✅ Выдано {amount} монет"
    )

    # Сообщение игроку
    try:

        await bot.send_message(
            user_id,
            f"💰 Вам выдано {amount} монет!"
        )

    except:
        pass

# ================= TAKE MONEY =================

@dp.message(Command("takemoney"))
async def takemoney(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "/takemoney user_id amount"
        )
        return

    user_id = int(args[1])
    amount = int(args[2])

    await db.execute("""
    UPDATE users
    SET money = GREATEST(money - $1, 0)
    WHERE user_id = $2
    """, amount, user_id)

    # Сообщение админу
    await message.answer(
        f"❌ Забрано {amount} монет"
    )

    # Сообщение игроку
    try:

        await bot.send_message(
            user_id,
            f"❌ У вас забрали {amount} монет"
        )

    except:
        pass

# ================= GIVE VIP =================

@dp.message(Command("givevip"))
async def givevip(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "/givevip user_id vip"
        )
        return

    user_id = int(args[1])
    vip = int(args[2])

    await db.execute("""
    UPDATE users
    SET vip = $1
    WHERE user_id = $2
    """, vip, user_id)

    # Сообщение админу
    await message.answer(
        f"✅ Выдан {VIP_NAMES.get(vip, 'VIP')}"
    )

    # Сообщение игроку
    try:

        multiplier = vip_multiplier(vip)

        await bot.send_message(
            user_id,
            f"💎 Вам выдан {VIP_NAMES.get(vip)}!\n\n"
            f"🔥 Множитель: x{multiplier}"
        )

    except:
        pass

# ================= BROADCAST =================

@dp.message(Command("broadcast"))
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/broadcast ", "")

    if text == "":
        await message.answer(
            "Использование:\n/broadcast текст"
        )
        return

    users = await db.fetch("""
    SELECT user_id
    FROM users
    """)

    success = 0
    failed = 0

    for user in users:

        try:

            await bot.send_message(
                user["user_id"],
                f"📢 ОБЪЯВЛЕНИЕ\n\n{text}"
            )

            success += 1

        except:

            failed += 1

    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"📨 Отправлено: {success}\n"
        f"❌ Ошибок: {failed}"
    )

# ================= ADMIN MENU =================

def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💎 Выдать VIP",
                    callback_data="admin_givevip"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Снять VIP",
                    callback_data="admin_removevip"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💰 Выдать деньги",
                    callback_data="admin_givemoney"
                ),

                InlineKeyboardButton(
                    text="💸 Забрать деньги",
                    callback_data="admin_takemoney"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎉 Запустить EVENT",
                    callback_data="admin_event"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Остановить EVENT",
                    callback_data="admin_stopevent"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 Рассылка",
                    callback_data="admin_broadcast"
                )
            ]
        ]
    )

# ================= ADMIN COMMAND =================

@dp.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙️ АДМИН ПАНЕЛЬ\n\n"
        "Выберите действие:",
        reply_markup=admin_menu()
    )

# ================= ADMIN BUTTONS =================

@dp.callback_query(F.data == "admin_givevip")
async def admin_givevip(callback: CallbackQuery):

    await callback.message.edit_text(
        "💎 ВЫДАЧА VIP\n\n"
        "Команда:\n"
        "/givevip user_id vip\n\n"
        "VIP:\n"
        "1 = x2\n"
        "2 = x5\n"
        "3 = x10\n"
        "4 = x25",
        reply_markup=admin_menu()
    )

@dp.callback_query(F.data == "admin_removevip")
async def admin_removevip(callback: CallbackQuery):

    await callback.message.edit_text(
        "❌ СНЯТИЕ VIP\n\n"
        "Команда:\n"
        "/removevip user_id",
        reply_markup=admin_menu()
    )

@dp.callback_query(F.data == "admin_givemoney")
async def admin_givemoney(callback: CallbackQuery):

    await callback.message.edit_text(
        "💰 ВЫДАЧА ДЕНЕГ\n\n"
        "Команда:\n"
        "/givemoney user_id amount",
        reply_markup=admin_menu()
    )

@dp.callback_query(F.data == "admin_takemoney")
async def admin_takemoney(callback: CallbackQuery):

    await callback.message.edit_text(
        "💸 ЗАБРАТЬ ДЕНЬГИ\n\n"
        "Команда:\n"
        "/takemoney user_id amount",
        reply_markup=admin_menu()
    )

@dp.callback_query(F.data == "admin_event")
async def admin_event(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎉 ЗАПУСК EVENT\n\n"
        "Команда:\n"
        "/event множитель\n\n"
        "Пример:\n"
        "/event 5",
        reply_markup=admin_menu()
    )

@dp.callback_query(F.data == "admin_stopevent")
async def admin_stopevent(callback: CallbackQuery):

    await callback.message.edit_text(
        "❌ ОСТАНОВКА EVENT\n\n"
        "Команда:\n"
        "/stopevent",
        reply_markup=admin_menu()
    )

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery):

    await callback.message.edit_text(
        "📢 РАССЫЛКА\n\n"
        "Команда:\n"
        "/broadcast текст",
        reply_markup=admin_menu()
    )

# ================= MAIN =================

async def main():

    await db_start()

    asyncio.create_task(
        autoclick_loop()
    )

    print("Бот запущен")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())