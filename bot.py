import asyncio, logging, secrets
from datetime import datetime, timedelta
from io import BytesIO
import qrcode
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, LabeledPrice, PreCheckoutQuery
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn
import config
import database as db
import panel
from tasks import check_expirations
from web.app import app as web_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
bot = Bot(token=config.BOT_TOKEN, session=AiohttpSession(proxy=config.PROXY_URL) if config.PROXY_URL else None)
dp = Dispatcher()

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Моя подписка", callback_data="status")],
        [InlineKeyboardButton(text="💳 Продлить", callback_data="buy")],
    ])

@dp.message(Command("start"))
async def start_handler(message: Message):
    tg_id = message.from_user.id
    email = f"tg_{tg_id}"
    client = await panel.get_client(email)
    if not client:
        await panel.create_client(tg_id, days=3)
        expiry = datetime.now() + timedelta(days=3)
        await db.add_or_update_user(tg_id, email, expiry)
        await message.answer("👋 Добро пожаловать! Активирован пробный доступ на 3 дня.", reply_markup=main_kb())
    else:
        await message.answer("👋 С возвращением!", reply_markup=main_kb())

@dp.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ У вас нет доступа.")
        return
    token = secrets.token_urlsafe(32)
    await db.create_admin_token(message.from_user.id, token, datetime.now() + timedelta(minutes=5))
    url = f"https://elburitozz.duckdns.org/auth/magic/{token}"
    await message.answer(f"🔑 <b>Ссылка для входа в админку (действует 5 минут):</b>\n\n{url}", parse_mode="HTML")

@dp.callback_query(F.data == "status")
async def status_handler(cb: CallbackQuery):
    tg_id = cb.from_user.id
    email = f"tg_{tg_id}"
    client = await panel.get_client(email)
    if not client:
        await cb.message.answer("Клиент не найден. Нажмите /start.")
        await cb.answer()
        return
    try: expiry_text = datetime.fromisoformat(client.expiry_time).strftime("%d.%m.%Y %H:%M")
    except: expiry_text = "—"
    status = "🟢 Активна" if client.enable else "🔴 Отключена"
    text = f"<b>Ваша подписка</b>\nСтатус: {status}\nДействует до: {expiry_text}"
    links = await panel.get_links(email)
    if links:
        text += f"\n\n🔗 <b>Ссылка:</b>\n<code>{links[0]}</code>"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(links[0]); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO(); img.save(bio, "PNG"); bio.seek(0)
        await cb.message.answer_photo(photo=BufferedInputFile(bio.read(), filename="qr.png"), caption=text)
    else:
        await cb.message.answer(text)
    await cb.answer()

@dp.callback_query(F.data == "buy")
async def buy_handler(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30 дней — 100 ⭐", callback_data="pay_30")],
        [InlineKeyboardButton(text="90 дней — 250 ⭐", callback_data="pay_90")],
    ])
    await cb.message.answer("Выберите тариф для оплаты звездами (⭐):", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def payment_handler(cb: CallbackQuery):
    days = int(cb.data.split("_")[1])
    prices = {30: 100, 90: 250}
    if days not in prices: return
    await bot.send_invoice(
        chat_id=cb.from_user.id, title=f"VPN на {days} дней", description="Продление подписки",
        payload=f"extend_{days}", provider_token="", currency="XTR",
        prices=[LabeledPrice(label="VPN", amount=prices[days])]
    )
    await cb.answer()

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("extend_"):
        days = int(payload.split("_")[1])
        tg_id = message.from_user.id
        email = f"tg_{tg_id}"
        new_expiry = await panel.extend_client(email, days=days)
        if new_expiry:
            await db.add_or_update_user(tg_id, email, new_expiry)
            await message.answer(f"✅ Оплата получена! Подписка продлена до {new_expiry.strftime('%d.%m.%Y %H:%M')}")
        else:
            await message.answer("❌ Ошибка при продлении.")

async def main():
    await db.init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expirations, "interval", minutes=15, args=(bot,))
    scheduler.start()
    asyncio.create_task(uvicorn.Server(uvicorn.Config(web_app, host="0.0.0.0", port=8000, log_level="info")).serve())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
