import aiohttp, asyncio, json
import config

async def check():
    print(f"URL панели: {config.XUI_URL}")
    print(f"INBOUND_ID: {config.INBOUND_ID}")
    token_short = config.XUI_TOKEN[:10] + "..." if config.XUI_TOKEN else "НЕ ЗАДАН"
    print(f"Токен (начало): {token_short}")
    print("-" * 40)

    headers = {"Authorization": f"Bearer {config.XUI_TOKEN}"}
    base = config.XUI_URL.rstrip('/')

    # Вариант 1: Классический эндпоинт
    url1 = f"{base}/panel/api/inbounds/get/{config.INBOUND_ID}"
    print(f"1. Пробую: {url1}")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url1, headers=headers, ssl=False) as r:
                print(f"   Статус: {r.status}")
                text = await r.text()
                print(f"   Ответ: {text[:200]}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    print("-" * 40)

    # Вариант 2: Список всех inbounds (может работать, даже если get не работает)
    url2 = f"{base}/panel/api/inbounds/list"
    print(f"2. Пробую: {url2}")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url2, headers=headers, ssl=False) as r:
                print(f"   Статус: {r.status}")
                text = await r.text()
                print(f"   Ответ: {text[:200]}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    print("-" * 40)

    # Вариант 3: Проверка без токена (должна дать 404 или 401, чтобы понять, что эндпоинт существует)
    print(f"3. Проверка эндпоинта без токена: {url1}")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url1, ssl=False) as r:
                print(f"   Статус (без токена): {r.status}")
    except Exception as e:
        print(f"   Ошибка: {e}")

asyncio.run(check())