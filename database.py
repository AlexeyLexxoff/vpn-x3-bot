import aiosqlite
from datetime import datetime
DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, expiry TEXT NOT NULL,
                notified_24h INTEGER DEFAULT 0, notified_expired INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_tokens (
                token TEXT PRIMARY KEY, tg_id INTEGER NOT NULL, expires_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def add_or_update_user(tg_id: int, email: str, expiry: datetime):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (tg_id, email, expiry, notified_24h, notified_expired)
            VALUES (?, ?, ?, 0, 0) ON CONFLICT(tg_id) DO UPDATE SET
            email = excluded.email, expiry = excluded.expiry, notified_24h = 0, notified_expired = 0
        """, (tg_id, email, expiry.isoformat()))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT tg_id, email, expiry, notified_24h, notified_expired FROM users") as cur:
            return await cur.fetchall()

async def set_notified(tg_id: int, field: str):
    if field not in ("notified_24h", "notified_expired"): return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field} = 1 WHERE tg_id = ?", (tg_id,))
        await db.commit()

async def create_admin_token(tg_id: int, token: str, expires_at: datetime):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO admin_tokens (token, tg_id, expires_at) VALUES (?, ?, ?)", (token, tg_id, expires_at.isoformat()))
        await db.commit()

async def verify_admin_token(token: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT tg_id, expires_at FROM admin_tokens WHERE token = ?", (token,)) as cursor:
            row = await cursor.fetchone()
            if not row: return None
            tg_id, expires_at_str = row
            if datetime.now() > datetime.fromisoformat(expires_at_str):
                await db.execute("DELETE FROM admin_tokens WHERE token = ?", (token,))
                await db.commit()
                return None
            return tg_id
