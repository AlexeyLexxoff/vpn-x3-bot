from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import database as db, panel, config
from .auth import create_session, get_session_user, require_admin

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_session_user(request) == config.ADMIN_ID: return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={})

@router.get("/auth/magic/{token}")
async def magic_login(token: str):
    tg_id = await db.verify_admin_token(token)
    if not tg_id or tg_id != config.ADMIN_ID:
        return HTMLResponse("<h3>❌ Ссылка недействительна или истекла. Запросите новую в боте.</h3>", status_code=401)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("session", create_session(tg_id), httponly=True, samesite="lax", max_age=86400 * 7)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session")
    return response

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, admin: int = Depends(require_admin)):
    users = await db.get_all_users()
    now = datetime.now()
    stats = {"total": 0, "active": 0, "expiring": 0, "expired": 0}
    rows = []
    for tg_id, email, expiry_str, _, _ in users:
        try: exp = datetime.fromisoformat(expiry_str)
        except: continue
        delta = (exp - now).total_seconds()
        stats["total"] += 1
        if delta <= 0: status = "expired"; stats["expired"] += 1
        elif delta <= 86400: status = "expiring"; stats["expiring"] += 1
        else: status = "active"; stats["active"] += 1
        rows.append({"tg_id": tg_id, "email": email, "expiry": exp.strftime("%d.%m.%Y %H:%M"), "status": status})
    rows.sort(key=lambda r: r["expiry"])
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"stats": stats, "users": rows})

@router.post("/api/extend/{tg_id}")
async def api_extend(tg_id: int, days: int = Form(...), admin: int = Depends(require_admin)):
    email = f"tg_{tg_id}"
    new_expiry = await panel.extend_client(email, days=days)
    if not new_expiry: return JSONResponse({"ok": False}, status_code=404)
    await db.add_or_update_user(tg_id, email, new_expiry)
    return {"ok": True}

@router.post("/api/disable/{tg_id}")
async def api_disable(tg_id: int, admin: int = Depends(require_admin)):
    await panel.disable_client(f"tg_{tg_id}")
    return {"ok": True}

@router.post("/api/enable/{tg_id}")
async def api_enable(tg_id: int, admin: int = Depends(require_admin)):
    await panel.enable_client(f"tg_{tg_id}")
    return {"ok": True}
