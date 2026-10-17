import aiohttp
import json
import uuid
from datetime import datetime, timedelta
import config

# Очищаем URL от пробелов и слэшей на конце
BASE_URL = config.XUI_URL.strip().rstrip('/')
HEADERS = {"Authorization": f"Bearer {config.XUI_TOKEN}"}

async def _req(method, path, json_data=None):
    url = f"{BASE_URL}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=json_data, headers=HEADERS, ssl=False) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {text}")
            return await resp.json()

async def create_client(tg_id: int, days: int) -> str:
    email = f"tg_{tg_id}"
    # Получаем инбаунд, чтобы узнать протокол (vless, vmess и т.д.)
    res = await _req("GET", f"/panel/api/inbounds/get/{config.INBOUND_ID}")
    if not res.get("success"):
        raise Exception(f"Failed to get inbound: {res}")
    
    inbound = res["obj"]
    protocol = inbound.get("protocol", "vless")
    
    # Формируем данные клиента
    client = {
        "email": email,
        "limitIp": 2,
        "totalGB": 0,  # 0 = безлимит (в гигабайтах)
        "expiryTime": int((datetime.now() + timedelta(days=days)).timestamp() * 1000),
        "enable": True,
        "tgId": tg_id, # ИСПРАВЛЕНИЕ: Панель ждет здесь число, а не строку
        "subId": str(uuid.uuid4()),
        "reset": 0
    }
    
    if protocol in ("vless", "vmess"):
        client["id"] = str(uuid.uuid4())
        if protocol == "vless":
            client["flow"] = "xtls-rprx-vision"
    elif protocol == "trojan":
        client["password"] = str(uuid.uuid4())

    # Используем Modern API для добавления клиента
    payload = {
        "inboundIds": [config.INBOUND_ID],
        "client": client
    }
    res = await _req("POST", "/panel/api/clients/add", json_data=payload)
    if not res.get("success"):
        raise Exception(f"Failed to add client: {res}")
    return email

class ClientObj:
    pass

async def get_client(email: str):
    try:
        # Modern API: получение клиента по email
        res = await _req("GET", f"/panel/api/clients/get/{email}")
        if not res.get("success") or not res.get("obj"):
            return None
        
        client_data = res["obj"]["client"]
        obj = ClientObj()
        obj.email = client_data.get("email")
        obj.enable = client_data.get("enable", False)
        obj.up = 0
        obj.down = 0
        obj.id = client_data.get("uuid") or client_data.get("password")
        exp_ms = client_data.get("expiryTime", 0)
        obj.expiry_time = datetime.fromtimestamp(exp_ms/1000).isoformat() if exp_ms > 0 else None
        return obj
    except Exception:
        return None

async def _update_client_field(email: str, update_dict: dict):
    try:
        # Modern API: обновление клиента по email
        res = await _req("POST", f"/panel/api/clients/update/{email}", json_data=update_dict)
        return res.get("success", False)
    except Exception:
        return False

async def extend_client(email: str, days: int):
    client = await get_client(email)
    if not client:
        return None
    if client.expiry_time:
        current = datetime.fromisoformat(client.expiry_time)
    else:
        current = datetime.now()
    base = max(current, datetime.now())
    new_expiry = base + timedelta(days=days)
    
    success = await _update_client_field(email, {
        "expiryTime": int(new_expiry.timestamp() * 1000),
        "enable": True
    })
    return new_expiry if success else None

async def disable_client(email: str):
    await _update_client_field(email, {"enable": False})

async def enable_client(email: str):
    await _update_client_field(email, {"enable": True})

async def get_links(email: str):
    try:
        # Modern API: получение ссылок для подключения
        res = await _req("GET", f"/panel/api/clients/links/{email}")
        if res.get("success") and res.get("obj"):
            return res["obj"]
        return []
    except Exception:
        return []