import aiohttp, asyncio, json, uuid
from datetime import datetime, timedelta
import config

BASE_URL = config.XUI_URL.strip().rstrip('/')
HEADERS = {"Authorization": f"Bearer {config.XUI_TOKEN}"}

async def test_add():
    # Получаем инбаунд, чтобы узнать протокол
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{BASE_URL}/panel/api/inbounds/get/{config.INBOUND_ID}", headers=HEADERS, ssl=False) as r:
            res = await r.json()

    protocol = res["obj"].get("protocol", "vless")

    client = {
        "email": "test_diag_999",
        "limitIp": 2,
        "totalGB": 0,
        "expiryTime": int((datetime.now() + timedelta(days=3)).timestamp() * 1000),
        "enable": True,
        "tgId": "",
        "subId": str(uuid.uuid4()),
        "reset": 0
    }
    if protocol in ("vless", "vmess"):
        client["id"] = str(uuid.uuid4())
        if protocol == "vless":
            client["flow"] = "xtls-rprx-vision"

    payload = {
        "id": config.INBOUND_ID,
        "settings": json.dumps({"clients": [client]})
    }

    print("1. Пробуем отправить JSON (application/json):")
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{BASE_URL}/panel/api/inbounds/addClient", json=payload, headers=HEADERS, ssl=False) as r:
            print(f"   Статус: {r.status}")
            print(f"   Ответ: {await r.text()}")

    print("-" * 40)
    print("2. Пробуем отправить form-data (application/x-www-form-urlencoded):")
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{BASE_URL}/panel/api/inbounds/addClient", data=payload, headers=HEADERS, ssl=False) as r:
            print(f"   Статус: {r.status}")
            print(f"   Ответ: {await r.text()}")

asyncio.run(test_add())