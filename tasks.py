import logging
from datetime import datetime
from aiogram import Bot
import database as db
import panel

logger = logging.getLogger(__name__)

async def check_expirations(bot: Bot):
    users = await db.get_all_users()
    now = datetime.now()
    for tg_id, email, expiry_str, notified_24h, notified_expired in users:
        try: expiry = datetime.fromisoformat(expiry_str)
        except Exception: continue
        delta = (expiry - now).total_seconds()

        if 0 < delta <= 86400 and not notified_24h:
            try:
                await bot.send_message(tg_id, f"⏳ Подписка закончится {expiry.strftime('%d.%m.%Y %H:%M')}. Продлите её.")
                await db.set_notified(tg_id, "notified_24h")
            except Exception as e: logger.warning(f"notify 24h {tg_id}: {e}")

        if delta <= 0 and not notified_expired:
            try:
                await panel.disable_client(email)
                await bot.send_message(tg_id, "❌ Подписка истекла. Доступ приостановлен.")
                await db.set_notified(tg_id, "notified_expired")
            except Exception as e: logger.error(f"disable {email}: {e}")
