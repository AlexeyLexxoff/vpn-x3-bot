from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import router

app = FastAPI(title="VPN Admin")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.include_router(router)
