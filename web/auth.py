import hashlib, hmac, time
from fastapi import Request, HTTPException
import itsdangerous
import config

signer = itsdangerous.TimestampSigner(config.WEB_SECRET_KEY)

def verify_telegram_auth(data: dict) -> bool:
    data = dict(data)
    received_hash = data.pop("hash", None)
    if not received_hash: return False
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(config.BOT_TOKEN.encode()).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash): return False
    try:
        if time.time() - int(data.get("auth_date", 0)) > 86400: return False
    except Exception: return False
    return True

def create_session(user_id: int) -> str:
    return signer.sign(str(user_id)).decode()

def get_session_user(request: Request):
    cookie = request.cookies.get("session")
    if not cookie: return None
    try: return int(signer.unsign(cookie, max_age=86400 * 7))
    except Exception: return None

async def require_admin(request: Request) -> int:
    user_id = get_session_user(request)
    if user_id is None or user_id != config.ADMIN_ID:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id
