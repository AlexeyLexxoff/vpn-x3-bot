import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
XUI_URL = os.getenv("XUI_URL")
XUI_TOKEN = os.getenv("XUI_TOKEN")
INBOUND_ID = int(os.getenv("INBOUND_ID", "1"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "change-me-please")
PROXY_URL = os.getenv("PROXY_URL", "")
