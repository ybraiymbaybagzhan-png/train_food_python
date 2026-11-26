from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import re
from typing import Optional
from urllib.parse import quote, unquote
import uuid

import qrcode
import qrcode.image.svg
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import (
    Carriage,
    DeliveryAssignment,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    QRCodeContext,
    SystemSetting,
    Train,
    User,
    UserRole,
)
from .lunchbox_data import LUNCHBOXES_DATA, get_localized_lunchboxes
from .whatsapp import KZ_TZ, build_order_message, build_whatsapp_url, format_departure, is_valid_phone, normalize_phone, to_kz
from .seed_data import hash_password, upgrade_and_seed, verify_password
from .xlsx_export import build_xlsx

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_app: FastAPI):
    upgrade_and_seed()
    yield


app = FastAPI(
    title="DAR | RES group — Onboard Train Restaurant & Food Ordering System",
    description="Production-ready onboard train dining and delivery service platform",
    version="3.1.0",
    lifespan=lifespan,
)

# Ланчбокс — жеке бетте (/lunchboxes); жалпы мәзірде (/menu, /api/menu) көрсетілмейді.
LUNCHBOX_CATEGORY_CODE = "lunchboxes"

ROOT_DIR = BASE_DIR.parent

# Static files mount
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)
if (ROOT_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=ROOT_DIR / "assets"), name="assets")
if (ROOT_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=ROOT_DIR / "css"), name="css")
if (ROOT_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=ROOT_DIR / "js"), name="js")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def static_revalidate(request: Request, call_next):
    """Статикалық файлдар (сурет, CSS, JS) әр сұрауда ETag арқылы тексеріледі —
    сурет ауыстырылса, браузер ескі нұсқасын кэштен көрсетпейді."""
    response = await call_next(request)
    if request.url.path.startswith(("/static/", "/assets/", "/css/", "/js/")):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Серверде ішкі қате орын алды / Внутренняя ошибка сервера. Пожалуйста, попробуйте позже."}
        )
    return HTMLResponse(
        content="""
        <!DOCTYPE html><html><head><meta charset='utf-8'><title>DAR | RES group</title>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <style>body{font-family:'Montserrat',sans-serif;text-align:center;padding:50px 20px;background:#F7F7F5;color:#1C3155;}
        h2{font-size:1.8rem;margin-bottom:12px;}p{color:#666;font-size:1.05rem;line-height:1.6;}
        a{display:inline-block;margin-top:24px;padding:12px 24px;background:#1C3155;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;}</style>
        </head><body>
        <h2>Қызмет көрсетуде уақытша кідіріс</h2>
        <p>Временная заминка в работе сервиса. Пожалуйста, вернитесь в меню.</p>
        <a href='/'>← Менюге қайту / На главную</a>
        </body></html>
        """,
        status_code=500,
    )


# ==============================================================================
# REALTIME WEBSOCKET HUB
# ==============================================================================
class RealtimeHub:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.staff_connections: set[int] = set()  # id(ws) — тек кіру жасаған қызметкерлер (аспаз/жолсерік/админ)

    async def connect(self, websocket: WebSocket, staff: bool = False):
        await websocket.accept()
        self.active_connections.append(websocket)
        if staff:
            self.staff_connections.add(id(websocket))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.staff_connections.discard(id(websocket))

    async def broadcast(self, event_type: str, data: dict, staff_only: bool = False):
        """staff_only=True — жолаушылардың жеке деректері (аты, орны) қызметкерлерге ғана жіберіледі."""
        payload = {"event": event_type, "data": data, "timestamp": datetime.utcnow().isoformat()}
        dead = []
        for ws in list(self.active_connections):
            if staff_only and id(ws) not in self.staff_connections:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


hub = RealtimeHub()


def iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """Дерекқордан келген (UTC, tz-сыз) уақытты браузерге ISO 'Z' пішімінде береді."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def kz_today():
    return datetime.now(KZ_TZ).date()


def reset_expired_stoplist(db: Session) -> None:
    """Стоп-листке кеше (немесе одан бұрын) қойылған тағамдарды жаңа күні автоматты қайта қосады."""
    today = kz_today()
    rows = db.scalars(
        select(MenuItem).where(MenuItem.is_available.is_(False), MenuItem.sold_out_date.is_not(None), MenuItem.sold_out_date < today)
    ).all()
    if not rows:
        return
    for item in rows:
        item.is_available = True
        item.sold_out_date = None
    db.commit()


# ==============================================================================
# STARTUP EVENT
# ==============================================================================


# ==============================================================================
# AUTHENTICATION & SESSION HELPERS
# ==============================================================================
SESSION_SECRET = os.getenv("SESSION_SECRET", "dar_res_super_secret_session_key_2026")


def generate_session_token(user: User) -> str:
    msg = f"{user.id}:{user.username}:{user.password_hash}:{SESSION_SECRET}"
    return hashlib.sha256(msg.encode("utf-8")).hexdigest()[:32]


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    session_val = request.cookies.get("dar_res_session")
    if not session_val:
        return None
    try:
        user_id_str, token_hash = session_val.split(":", 1)
        user = db.get(User, int(user_id_str))
        if user and user.is_active:
            expected = generate_session_token(user)
            if token_hash == expected:
                return user
    except Exception:
        pass
    return None


def require_role(allowed_roles: list[UserRole]):
    def dependency(request: Request, db: Session = Depends(get_db)) -> User:
        user = get_current_user_optional(request, db)
        if not user:
            if request.url.path.startswith("/api/"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Требуется авторизация / Authentication required"
                )
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": f"/login?next={request.url.path}"}
            )
        if user.role not in allowed_roles and user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен / Access denied"
            )
        return user
    return dependency


def create_session_cookie(response: Response, user: User):
    token_hash = generate_session_token(user)
    cookie_value = f"{user.id}:{token_hash}"
    response.set_cookie(
        key="dar_res_session",
        value=cookie_value,
        httponly=True,
        max_age=86400 * 7,
        samesite="lax",
    )


# ==============================================================================
# WEBSOCKET ENDPOINT
# ==============================================================================
async def _ws_loop(websocket: WebSocket, staff: bool = False):
    await hub.connect(websocket, staff=staff)
    try:
        while True:
            # Keepalive listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        hub.disconnect(websocket)
    except Exception:
        hub.disconnect(websocket)


def _ws_staff_user(websocket: WebSocket) -> Optional[User]:
    """WebSocket cookie арқылы қызметкерді тексереді (аспаз/жолсерік/админ)."""
    session_val = websocket.cookies.get("dar_res_session")
    if not session_val:
        return None
    try:
        user_id_str, token_hash = session_val.split(":", 1)
        with SessionLocal() as db:
            user = db.get(User, int(user_id_str))
            if user and user.is_active and token_hash == generate_session_token(user):
                return user
    except Exception:
        pass
    return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await _ws_loop(websocket)


@app.websocket("/ws/order/{order_key}")
async def websocket_order(websocket: WebSocket, order_key: str):
    await _ws_loop(websocket)


@app.websocket("/ws/kitchen")
@app.websocket("/ws/staff")
async def websocket_staff(websocket: WebSocket):
    if _ws_staff_user(websocket) is None:
        await websocket.close(code=4401)
        return
    await _ws_loop(websocket, staff=True)


# ==============================================================================
# PASSENGER VIEWS
# ==============================================================================
@app.get("/manifest.json")
def get_manifest():
    return FileResponse(BASE_DIR / "static" / "manifest.json", media_type="application/manifest+json")


@app.get("/site", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
def landing_site():
    return FileResponse(ROOT_DIR / "index.html")


@app.get("/sw.js")
def get_sw():
    return FileResponse(BASE_DIR / "static" / "sw.js", media_type="application/javascript")


@app.get("/api/qr/{token}")
def get_qr_svg(token: str, request: Request, download: bool = False, db: Session = Depends(get_db)):
    """Generate crisp, scalable vector SVG QR code for table tents or stickers."""
    target_url = f"{str(request.base_url).rstrip('/')}/menu?q={token}"
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(target_url, image_factory=factory, box_size=10, border=2)
    svg_buf = io.BytesIO()
    img.save(svg_buf)
    svg_data = svg_buf.getvalue()
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="QR_{token}.svg"'
    return Response(content=svg_data, media_type="image/svg+xml", headers=headers)


PASSENGER_CTX_COOKIE = "dar_res_ctx"
PASSENGER_CTX_MAX_AGE = 60 * 60 * 24  # 24 сағат


def resolve_passenger_context(
    request: Request,
    db: Session,
    train: Optional[str],
    wagon: Optional[str],
    carriage: Optional[str],
    seat: Optional[str],
    q: Optional[str],
) -> dict:
    """Жолаушының пойыз/вагон/орын контексті.

    Басымдық: QR-токен (q) > URL параметрлері > cookie (алдыңғы бет) > әдепкі.
    Cookie керек: жолаушы /menu мен /lunchboxes арасында ауысқанда пойыз ұмытылмауы үшін
    (әйтпесе тапсырыс басқа пойыздың аспазына кетеді).
    """
    explicit = bool(q or train or wagon or carriage or seat)
    saved: dict = {}
    if not explicit:
        try:
            raw_cookie = request.cookies.get(PASSENGER_CTX_COOKIE, "")
            loaded = json.loads(unquote(raw_cookie)) if raw_cookie else {}
            saved = loaded if isinstance(loaded, dict) else {}
        except Exception:
            saved = {}

    train_explicit = bool(q or train or saved.get("train"))
    train_val = train or saved.get("train") or "071"
    wagon_val = carriage or wagon or saved.get("wagon") or "7"
    seat_val = seat or saved.get("seat") or "18"
    qr_invalid = False

    if q:
        qr = db.scalar(select(QRCodeContext).where(QRCodeContext.public_token == q, QRCodeContext.is_active.is_(True)))
        if qr:
            train_val = qr.train_number
            wagon_val = qr.carriage_number
            if qr.table_number:
                seat_val = qr.table_number
        else:
            qr_invalid = True

    carriage_obj = db.scalar(
        select(Carriage).join(Train).where(Train.train_number == train_val, Carriage.carriage_number == wagon_val)
    )
    ordering_mode_setting = db.scalar(select(SystemSetting).where(SystemSetting.key == "ordering_mode"))

    return {
        "train_no": train_val,
        "train_explicit": train_explicit,
        "wagon_no": wagon_val,
        "seat_no": seat_val,
        "carriage_type": carriage_obj.carriage_type if carriage_obj else "Купе",
        "ordering_mode": ordering_mode_setting.value if ordering_mode_setting else "OPEN",
        "qr_invalid": qr_invalid,
        "save_cookie": explicit and not qr_invalid,
    }


def remember_passenger_context(response: Response, ctx: dict) -> None:
    if ctx.get("save_cookie"):
        response.set_cookie(
            PASSENGER_CTX_COOKIE,
            quote(json.dumps({"train": ctx["train_no"], "wagon": ctx["wagon_no"], "seat": ctx["seat_no"]})),
            max_age=PASSENGER_CTX_MAX_AGE,
            samesite="lax",
        )


@app.get("/", response_class=HTMLResponse)
@app.get("/menu", response_class=HTMLResponse)
@app.get("/cart", response_class=HTMLResponse)
@app.get("/checkout", response_class=HTMLResponse)
@app.get("/about", response_class=HTMLResponse)
def passenger_home(
    request: Request,
    train: Optional[str] = None,
    wagon: Optional[str] = None,
    carriage: Optional[str] = None,
    seat: Optional[str] = None,
    q: Optional[str] = None,
    lang: str = "ru",
    db: Session = Depends(get_db),
):
    ctx = resolve_passenger_context(request, db, train, wagon, carriage, seat, q)
    lang = "kz" if lang in ("kk", "kz") else lang  # шаблондар 'kz' кодын күтеді

    # Жалпы мәзір: ланчбокс санаты жоқ (ол /lunchboxes бетінде)
    categories = db.scalars(
        select(MenuCategory)
        .where(MenuCategory.is_active.is_(True), MenuCategory.code != LUNCHBOX_CATEGORY_CODE)
        .order_by(MenuCategory.sort_order)
    ).all()

    response = templates.TemplateResponse(
        request=request,
        name="passenger.html",
        context={
            "train_no": ctx["train_no"],
            "wagon_no": ctx["wagon_no"],
            "seat_no": ctx["seat_no"],
            "carriage_type": ctx["carriage_type"],
            "categories": categories,
            "current_lang": lang,
            "ordering_mode": ctx["ordering_mode"],
            "qr_invalid": ctx["qr_invalid"],
        },
    )
    remember_passenger_context(response, ctx)
    return response


@app.get("/lunchboxes", response_class=HTMLResponse)
def lunchboxes_page(
    request: Request,
    train: Optional[str] = None,
    wagon: Optional[str] = None,
    carriage: Optional[str] = None,
    seat: Optional[str] = None,
    q: Optional[str] = None,
    lang: str = "ru",
    db: Session = Depends(get_db),
):
    ctx = resolve_passenger_context(request, db, train, wagon, carriage, seat, q)
    normalized_lang = "kk" if lang in ("kk", "kz") else ("en" if lang == "en" else "ru")
    localized_items = merge_lunchboxes_with_db(db, get_localized_lunchboxes(lang=normalized_lang))
    raw_lunchboxes = merge_lunchboxes_with_db(db, LUNCHBOXES_DATA)
    active_trains = db.scalars(select(Train).where(Train.is_active.is_(True)).order_by(Train.train_number)).all()
    trains_for_form = [{"number": t.train_number, "route": t.route_name} for t in active_trains]
    preselect_train = ctx["train_no"] if ctx["train_explicit"] and any(t["number"] == ctx["train_no"] for t in trains_for_form) else ""

    response = templates.TemplateResponse(
        request=request,
        name="lunchboxes.html",
        context={
            "train_no": ctx["train_no"],
            "wagon_no": ctx["wagon_no"],
            "seat_no": ctx["seat_no"],
            "carriage_type": ctx["carriage_type"],
            "current_lang": lang,
            "ordering_mode": ctx["ordering_mode"],
            "qr_invalid": ctx["qr_invalid"],
            "lunchboxes": localized_items,
            "raw_lunchboxes": raw_lunchboxes,
            "trains": trains_for_form,
            "preselect_train": preselect_train,
            "min_advance_hours": get_lunchbox_min_hours(db),
            "min_departure_local": (datetime.now(KZ_TZ) + timedelta(hours=get_lunchbox_min_hours(db))).strftime("%Y-%m-%dT%H:%M"),
        },
    )
    remember_passenger_context(response, ctx)
    return response


@app.get("/api/lunchboxes")
def get_lunchboxes_api(lang: str = "ru", db: Session = Depends(get_db)):
    normalized_lang = "kk" if lang in ("kk", "kz") else ("en" if lang == "en" else "ru")
    return JSONResponse(content={
        "lunchboxes": merge_lunchboxes_with_db(db, get_localized_lunchboxes(lang=normalized_lang)),
        "raw": merge_lunchboxes_with_db(db, LUNCHBOXES_DATA),
    })


# ==============================================================================
# PUBLIC MENU REST API (Mobile-First, Caching & Details)
# ==============================================================================
@app.get("/api/menu")
def get_menu_api(include_lunchboxes: bool = False, db: Session = Depends(get_db)):
    reset_expired_stoplist(db)
    stmt = select(MenuCategory).where(MenuCategory.is_active.is_(True))
    if not include_lunchboxes:
        stmt = stmt.where(MenuCategory.code != LUNCHBOX_CATEGORY_CODE)
    categories = db.scalars(stmt.order_by(MenuCategory.sort_order)).all()

    result = []
    for cat in categories:
        items_payload = []
        for item in cat.items:
            if not item.is_active:
                continue
            variants_payload = [
                {
                    "id": v.id,
                    "name_ru": v.name_ru,
                    "name_kz": v.name_kz,
                    "name_en": v.name_en,
                    "size": v.volume_or_weight,
                    "price": float(v.price),
                    "is_available": v.is_available,
                }
                for v in item.variants
                if v.is_available
            ]
            items_payload.append({
                "id": item.id,
                "sku": item.sku,
                "name_ru": item.name_ru,
                "name_kz": item.name_kz,
                "name_en": item.name_en,
                "description_ru": item.description_ru,
                "description_kz": item.description_kz,
                "description_en": item.description_en,
                "ingredients_ru": item.ingredients_ru,
                "ingredients_kz": item.ingredients_kz,
                "ingredients_en": item.ingredients_en,
                "weight": item.weight_value or item.volume_value or "",
                "price": float(item.price),
                "image_url": item.image_url,
                "is_available": item.is_available,
                "is_popular": item.is_popular,
                "variants": variants_payload,
            })
        result.append({
            "id": cat.id,
            "code": cat.code,
            "name_ru": cat.name_ru,
            "name_kz": cat.name_kz,
            "name_en": cat.name_en,
            "items": items_payload,
        })

    return JSONResponse(content={"categories": result})


@app.get("/api/menu/categories")
def get_categories_api(db: Session = Depends(get_db)):
    categories = db.scalars(
        select(MenuCategory)
        .where(MenuCategory.is_active.is_(True), MenuCategory.code != LUNCHBOX_CATEGORY_CODE)
        .order_by(MenuCategory.sort_order)
    ).all()
    return [
        {
            "id": c.id,
            "code": c.code,
            "name_ru": c.name_ru,
            "name_kz": c.name_kz,
            "name_en": c.name_en,
            "sort_order": c.sort_order,
            "is_active": c.is_active,
        }
        for c in categories
    ]


@app.get("/api/menu/items")
def get_items_api(category_id: Optional[int] = None, db: Session = Depends(get_db)):
    stmt = select(MenuItem).where(
        MenuItem.is_active.is_(True),
        MenuItem.category.has(MenuCategory.code != LUNCHBOX_CATEGORY_CODE),
    )
    if category_id:
        stmt = stmt.where(MenuItem.category_id == category_id)
    items = db.scalars(stmt.order_by(MenuItem.category_id, MenuItem.name_ru)).all()
    return [
        {
            "id": item.id,
            "category_id": item.category_id,
            "sku": item.sku,
            "name_ru": item.name_ru,
            "name_kz": item.name_kz,
            "name_en": item.name_en,
            "weight": item.weight_value or item.volume_value,
            "price": float(item.price),
            "is_available": item.is_available,
            "image_url": item.image_url,
            "variants": [
                {
                    "id": v.id,
                    "name_ru": v.name_ru,
                    "size": v.volume_or_weight,
                    "price": float(v.price),
                }
                for v in item.variants
                if v.is_available
            ],
        }
        for item in items
    ]


@app.get("/api/menu/items/{item_id}")
def get_item_api(item_id: int, db: Session = Depends(get_db)):
    item = db.get(MenuItem, item_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": item.id,
        "category_id": item.category_id,
        "sku": item.sku,
        "name_ru": item.name_ru,
        "name_kz": item.name_kz,
        "name_en": item.name_en,
        "ingredients_ru": item.ingredients_ru,
        "ingredients_kz": item.ingredients_kz,
        "ingredients_en": item.ingredients_en,
        "weight": item.weight_value or item.volume_value,
        "price": float(item.price),
        "is_available": item.is_available,
        "image_url": item.image_url,
        "variants": [
            {
                "id": v.id,
                "name_ru": v.name_ru,
                "size": v.volume_or_weight,
                "price": float(v.price),
                "is_available": v.is_available,
            }
            for v in item.variants
        ],
    }


# ==============================================================================
# WHATSAPP: әр пойыздың өз аспазына тапсырыс жіберу
# ==============================================================================
# Тапсырыс түсетін ортақ WhatsApp нөмірі (87772141601). Пойызға жеке нөмір берілмесе, барлық тапсырыс осыған барады.
DEFAULT_WHATSAPP_PHONE = "77772141601"


def resolve_whatsapp_phone(db: Session, train_no: str) -> str:
    """Пойыздың аспаз нөмірін қайтарады; жоқ болса — ортақ (әдепкі) нөмір."""
    train = db.scalar(select(Train).where(Train.train_number == (train_no or "").strip()))
    phone = normalize_phone(train.whatsapp_phone) if train else ""
    if not phone:
        default_phone = db.scalar(select(SystemSetting.value).where(SystemSetting.key == "whatsapp_default_phone"))
        phone = normalize_phone(default_phone or os.getenv("WHATSAPP_DEFAULT_PHONE", "") or DEFAULT_WHATSAPP_PHONE)
    return phone


def order_whatsapp_url(db: Session, order: Order) -> str:
    phone = resolve_whatsapp_phone(db, order.train_no)
    if not phone:
        return ""
    return build_whatsapp_url(phone, build_order_message(order))


def get_lunchbox_min_hours(db: Session) -> int:
    """Ланчбокс тапсырысы жүрерден неше сағат бұрын берілуі керек (әдепкі 24)."""
    raw = db.scalar(select(SystemSetting.value).where(SystemSetting.key == "lunchbox_min_advance_hours"))
    try:
        value = int(raw) if raw not in (None, "") else 24
    except ValueError:
        value = 24
    return max(value, 1)


def parse_departure(raw: Optional[str]) -> datetime:
    """'2026-12-01T14:30' (KZ жергілікті уақыты) -> UTC datetime."""
    if not raw or not raw.strip():
        raise HTTPException(status_code=400, detail="Укажите дату и время отправления поезда / Пойыздың жүру күні мен уақытын көрсетіңіз.")
    try:
        dt = datetime.fromisoformat(raw.strip())
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректная дата отправления / Жүру күні дұрыс емес.")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KZ_TZ)
    return dt.astimezone(timezone.utc)


def merge_lunchboxes_with_db(db: Session, lunchboxes: list[dict]) -> list[dict]:
    """Ланчбокстың бағасын, қолжетімділігін және нақты menu_item_id-ін дерекқордан (SKU бойынша) қосады."""
    skus = [lb["sku"] for lb in lunchboxes]
    rows = db.scalars(
        select(MenuItem).where(MenuItem.sku.in_(skus), MenuItem.is_active.is_(True))
    ).all()
    by_sku = {row.sku: row for row in rows}
    merged = []
    for lb in lunchboxes:
        row = by_sku.get(lb["sku"])
        price = float(row.price) if row else 0.0
        merged.append({
            **lb,
            "menu_item_id": row.id if row else None,
            "price": price,
            "is_available": bool(row and row.is_available and price > 0),
        })
    return merged


# ==============================================================================
# ORDER CREATION WITH SERVER-SIDE FINANCIAL VALIDATION & IDEMPOTENCY
# ==============================================================================
class OrderItemIn(BaseModel):
    menu_item_id: int
    variant_id: Optional[int] = None
    quantity: int = 1


class OrderCreateIn(BaseModel):
    passenger_name: str
    phone: str
    train_no: str
    wagon_no: str = ""
    seat_no: str = ""
    compartment_no: Optional[str] = ""
    departure_at: Optional[str] = None  # тек ланчбокс алдын ала тапсырысы үшін (KZ жергілікті уақыты)
    table_no: Optional[str] = ""
    comment: Optional[str] = ""
    items: list[OrderItemIn]
    idempotency_key: Optional[str] = None


@app.post("/api/orders")
async def create_order(
    payload: OrderCreateIn,
    x_idempotency_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    # Тапсырыс түрін анықтау: ланчбокс -> алдын ала тапсырыс (PREORDER), қалғаны -> пойыздағы (ONBOARD)
    requested_ids = [i.menu_item_id for i in payload.items if i.quantity > 0]
    requested_rows = db.scalars(select(MenuItem).where(MenuItem.id.in_(requested_ids))).all() if requested_ids else []
    lunch_count = sum(1 for m in requested_rows if m.category.code == LUNCHBOX_CATEGORY_CODE)
    is_preorder = lunch_count > 0
    if is_preorder and lunch_count != len(requested_rows):
        raise HTTPException(
            status_code=400,
            detail="Ланчбоксы заказываются отдельно (предзаказ при покупке билета) и не могут быть в одном заказе с блюдами меню / Ланчбокстарға жеке алдын ала тапсырыс беріледі, мәзір тағамдарымен бір тапсырыста болмайды.",
        )

    # Check system ordering mode (пойыздағы тапсырыстарға ғана; ланчбокс предзаказы бұған тәуелсіз)
    ordering_mode = db.scalar(select(SystemSetting.value).where(SystemSetting.key == "ordering_mode"))
    if ordering_mode == "CLOSED" and not is_preorder:
        raise HTTPException(
            status_code=400,
            detail="Ordering is temporarily closed / Тапсырыс қабылдау уақытша тоқтатылды / Прием заказов временно приостановлен."
        )

    reset_expired_stoplist(db)

    # Idempotency check: header or body
    idempotency_key = payload.idempotency_key or x_idempotency_key
    if idempotency_key:
        existing_order = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
        if existing_order:
            return {
                "success": True,
                "is_duplicate": True,
                "order_number": existing_order.order_number,
                "public_uuid": existing_order.public_uuid,
                "redirect_url": f"/order/{existing_order.public_uuid}",
                "whatsapp_url": order_whatsapp_url(db, existing_order),
            }

    departure_utc: Optional[datetime] = None
    if is_preorder:
        # Ланчбокс тек билетпен бірге, жүрерден кемінде N сағат (әдепкі 24) бұрын тапсырылады
        departure_utc = parse_departure(payload.departure_at)
        min_hours = get_lunchbox_min_hours(db)
        now_utc = datetime.now(timezone.utc)
        if departure_utc - now_utc < timedelta(hours=min_hours):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Ланчбоксы можно заказать не позднее чем за {min_hours} ч до отправления поезда. "
                    f"/ Ланчбокс тапсырысын пойыз жүруіне кемінде {min_hours} сағат қалғанда ғана беруге болады. "
                    f"/ Lunchboxes must be pre-ordered at least {min_hours} hours before departure."
                ),
            )
        if departure_utc - now_utc > timedelta(days=120):
            raise HTTPException(status_code=400, detail="Слишком далёкая дата отправления / Жүру күні тым алыс.")
        if not payload.passenger_name or not payload.passenger_name.strip():
            raise HTTPException(status_code=400, detail="Укажите имя пассажира / Жолаушының атын көрсетіңіз.")
        if not is_valid_phone(payload.phone):
            raise HTTPException(status_code=400, detail="Укажите корректный номер телефона для связи / Байланыс телефонын дұрыс көрсетіңіз.")
    else:
        if not payload.wagon_no or not payload.wagon_no.strip():
            raise HTTPException(status_code=400, detail="Укажите номер вагона.")
        if not payload.seat_no or not payload.seat_no.strip():
            raise HTTPException(status_code=400, detail="Укажите номер места или столика в вагоне.")

    if not payload.phone or not payload.phone.strip():
        raise HTTPException(status_code=400, detail="Укажите номер телефона для связи.")

    # Пойыз тіркелген және белсенді болуы керек (тапсырыс сол пойыздың аспазына жіберіледі)
    train_obj = db.scalar(select(Train).where(Train.train_number == payload.train_no.strip()))
    if not train_obj or not train_obj.is_active:
        raise HTTPException(status_code=400, detail="Поезд не найден или не обслуживается. Отсканируйте QR-код в вагоне заново.")

    # Check carriage delivery enabled if carriage exists
    carriage_obj = db.scalar(
        select(Carriage).join(Train).where(
            Train.train_number == payload.train_no.strip(),
            Carriage.carriage_number == payload.wagon_no.strip()
        )
    )
    if carriage_obj and not carriage_obj.delivery_enabled and not is_preorder:
        raise HTTPException(
            status_code=400,
            detail="В данный вагон доставка заказов временно недоступна."
        )

    if not payload.items:
        raise HTTPException(status_code=400, detail="Корзина пуста. Добавьте блюда для заказа.")

    # Validate items and calculate prices strictly on the server
    subtotal = Decimal("0.00")
    order_items_to_create = []

    for item_in in payload.items:
        if item_in.quantity <= 0:
            continue

        menu_item = db.get(MenuItem, item_in.menu_item_id)
        if not menu_item or not menu_item.is_active:
            raise HTTPException(status_code=400, detail=f"Блюдо с ID {item_in.menu_item_id} не найдено.")

        if not menu_item.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"Блюдо «{menu_item.name_ru}» закончилось (стоп-лист) / «{menu_item.name_kz}» таусылды (стоп-лист) / «{menu_item.name_en}» is sold out today."
            )

        item_name = menu_item.name_ru
        variant_desc = ""
        unit_price = menu_item.price

        if item_in.variant_id:
            variant = db.get(MenuItemVariant, item_in.variant_id)
            if not variant or variant.menu_item_id != menu_item.id or not variant.is_available:
                raise HTTPException(status_code=400, detail=f"Выбранный размер/вариант блюда недоступен.")
            unit_price = variant.price
            variant_desc = f"{variant.name_ru} ({variant.volume_or_weight})"

        if Decimal(str(unit_price)) <= 0:
            raise HTTPException(status_code=400, detail=f"Для позиции '{menu_item.name_ru}' ещё не установлена цена.")

        line_total = Decimal(str(unit_price)) * Decimal(str(item_in.quantity))
        subtotal += line_total

        order_items_to_create.append({
            "menu_item_id": menu_item.id,
            "menu_variant_id": item_in.variant_id,
            "item_name_snapshot": item_name,
            "variant_snapshot": variant_desc,
            "price_snapshot": unit_price,
            "quantity": item_in.quantity,
            "line_total": line_total,
        })

    if not order_items_to_create:
        raise HTTPException(status_code=400, detail="В заказе нет доступных позиций с положительным количеством.")

    # Strict 10% service charge calculation
    service_charge_rate = Decimal("0.10")
    service_charge = (subtotal * service_charge_rate).quantize(Decimal("1.00"))
    total = subtotal + service_charge

    # Human-readable order number: DAR-Train-(1000+id). Уақытша нөмір flush-тан кейін id бойынша ауыстырылады
    public_uuid = uuid.uuid4().hex
    order_number = f"TMP-{public_uuid}"

    new_order = Order(
        public_uuid=public_uuid,
        order_number=order_number,
        passenger_name=payload.passenger_name.strip() or "Жолаушы / Пассажир",
        phone=payload.phone.strip(),
        train_no=payload.train_no.strip(),
        wagon_no=(payload.wagon_no or "").strip(),
        seat_no=(payload.seat_no or "").strip(),
        compartment_no=payload.compartment_no.strip() if payload.compartment_no else "",
        table_no=payload.table_no.strip() if payload.table_no else "",
        subtotal=subtotal,
        service_charge_rate=service_charge_rate,
        service_charge=service_charge,
        total=total,
        status=OrderStatus.NEW,
        comment=payload.comment.strip() if payload.comment else "",
        order_type="PREORDER" if is_preorder else "ONBOARD",
        departure_at=departure_utc,
        idempotency_key=idempotency_key,
    )
    db.add(new_order)
    db.flush()
    new_order.order_number = f"DAR-{new_order.train_no}-{1000 + new_order.id}"

    for oi_data in order_items_to_create:
        db.add(OrderItem(order_id=new_order.id, **oi_data))

    db.add(OrderStatusHistory(
        order_id=new_order.id,
        old_status="NONE",
        new_status=OrderStatus.NEW.value,
        changed_by="passenger",
    ))

    try:
        db.commit()
        db.refresh(new_order)
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing_order = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
            if existing_order:
                return {
                    "success": True,
                    "is_duplicate": True,
                    "order_number": existing_order.order_number,
                    "public_uuid": existing_order.public_uuid,
                    "redirect_url": f"/order/{existing_order.public_uuid}",
                    "whatsapp_url": order_whatsapp_url(db, existing_order),
                }
        raise HTTPException(status_code=400, detail="Ошибка при оформлении заказа (дубликат или конфликт данных).")

    # Real-time WebSocket broadcast to kitchen
    await hub.broadcast("new_order", {
        "id": new_order.id,
        "order_number": new_order.order_number,
        "train_no": new_order.train_no,
        "wagon_no": new_order.wagon_no,
        "seat_no": new_order.seat_no,
        "passenger_name": new_order.passenger_name,
        "total": float(new_order.total),
        "comment": new_order.comment,
        "status": new_order.status.value,
        "created_at": new_order.created_at.strftime("%H:%M"),
        "order_type": new_order.order_type,
        "departure_at": format_departure(new_order.departure_at),
        "items": [
            {
                "name": oi.item_name_snapshot,
                "variant": oi.variant_snapshot,
                "quantity": oi.quantity,
                "price": float(oi.price_snapshot),
            }
            for oi in new_order.items
        ],
        "group_key": order_group_key(new_order),
    }, staff_only=True)

    return {
        "success": True,
        "id": new_order.id,
        "order_number": new_order.order_number,
        "public_uuid": new_order.public_uuid,
        "status": new_order.status.value,
        "subtotal": float(new_order.subtotal),
        "service_charge": float(new_order.service_charge),
        "total": float(new_order.total),
        "redirect_url": f"/order/{new_order.public_uuid}",
        "whatsapp_url": order_whatsapp_url(db, new_order),
    }


# ==============================================================================
# PASSENGER ORDER TRACKING PAGE
# ==============================================================================
def get_status_step_index(status: OrderStatus) -> int:
    mapping = {
        OrderStatus.NEW: 1,
        OrderStatus.ACCEPTED: 2,
        OrderStatus.PREPARING: 3,
        OrderStatus.READY: 4,
        OrderStatus.OUT_FOR_DELIVERY: 5,
        OrderStatus.DELIVERED: 6,
        OrderStatus.CANCELLED: 0,
    }
    return mapping.get(status, 1)


@app.get("/order/{public_uuid}", response_class=HTMLResponse)
def passenger_order_status(
    request: Request,
    public_uuid: str,
    lang: str = "ru",
    db: Session = Depends(get_db),
):
    order = db.scalar(select(Order).where((Order.public_uuid == public_uuid) | (Order.order_number == public_uuid)))
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден / Order not found")

    step_idx = get_status_step_index(order.status)
    related = related_orders(db, order)

    return templates.TemplateResponse(
        request=request,
        name="order_status.html",
        context={
            "order": order,
            "step_index": step_idx,
            "eta_iso": iso_utc(order.ready_eta_at),
            "can_cancel": order.status in PASSENGER_CANCELLABLE,
            "related": related,
            "related_total": (sum(float(r.total) for r in related) + float(order.total)) if related else 0,
            "current_lang": lang,
            "whatsapp_url": order_whatsapp_url(db, order),
            "departure_str": format_departure(order.departure_at),
            "auto_whatsapp": request.query_params.get("wa") == "1",
        },
    )


@app.get("/api/orders/{public_uuid}")
def get_order_api(public_uuid: str, db: Session = Depends(get_db)):
    order = db.scalar(select(Order).where((Order.public_uuid == public_uuid) | (Order.order_number == public_uuid)))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_number": order.order_number,
        "public_uuid": order.public_uuid,
        "status": order.status.value,
        "step_index": get_status_step_index(order.status),
        "train_no": order.train_no,
        "wagon_no": order.wagon_no,
        "seat_no": order.seat_no,
        "order_type": order.order_type,
        "departure_at": format_departure(order.departure_at),
        "subtotal": float(order.subtotal),
        "service_charge": float(order.service_charge),
        "total": float(order.total),
        "cancel_reason": order.cancel_reason,
        "cancelled_by": order.cancelled_by,
        "ready_eta_at": iso_utc(order.ready_eta_at),
        "can_cancel": order.status in PASSENGER_CANCELLABLE,
        "rating": order.rating,
        "created_at": iso_utc(order.created_at),
        "whatsapp_url": order_whatsapp_url(db, order),
        "related": [_order_brief(r) for r in related_orders(db, order)],
        "items": [
            {
                "menu_item_id": oi.menu_item_id,
                "variant_id": oi.menu_variant_id,
                "name": oi.item_name_snapshot,
                "variant": oi.variant_snapshot,
                "quantity": oi.quantity,
                "price": float(oi.price_snapshot),
                "line_total": float(oi.line_total),
            }
            for oi in order.items
        ]
    }


# ------------------------------------------------------------------------------
# Жолаушының өз тапсырысын басқаруы: бас тарту, қайта тапсыру, баға, байланысты тапсырыстар
# ------------------------------------------------------------------------------
PASSENGER_CANCELLABLE = (OrderStatus.NEW, OrderStatus.ACCEPTED)  # аспаз әзірлей бастағанға дейін


def _digits(raw: Optional[str]) -> str:
    return re.sub(r"\D", "", raw or "")


def order_group_key(order: Order) -> str:
    """Бір жолаушының тапсырыстарын топтау кілті: пойыз + вагон + орын (болмаса — телефон)."""
    place = f"{order.wagon_no}|{order.seat_no}|{order.compartment_no}".strip("|").lower()
    if order.wagon_no or order.seat_no:
        return f"{order.train_no}|{place}"
    return f"{order.train_no}|tel:{normalize_phone(order.phone)}"


def related_orders(db: Session, order: Order) -> list[Order]:
    """Сол жолаушының (телефон бойынша, сол пойыз) соңғы 24 сағаттағы басқа тапсырыстары."""
    phone = normalize_phone(order.phone)
    if not phone:
        return []
    since = datetime.utcnow() - timedelta(hours=24)
    rows = db.scalars(
        select(Order)
        .where(Order.train_no == order.train_no, Order.id != order.id, Order.created_at >= since)
        .order_by(Order.id)
    ).all()
    return [r for r in rows if normalize_phone(r.phone) == phone]


def _order_brief(o: Order) -> dict:
    return {
        "order_number": o.order_number,
        "public_uuid": o.public_uuid,
        "status": o.status.value,
        "total": float(o.total),
        "items_count": sum(i.quantity for i in o.items),
        "ready_eta_at": iso_utc(o.ready_eta_at),
    }


def _find_order_by_uuid(db: Session, public_uuid: str) -> Order:
    order = db.scalar(select(Order).where(Order.public_uuid == public_uuid))
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден / Тапсырыс табылмады")
    return order


class PassengerCancelIn(BaseModel):
    phone_tail: str = ""


@app.post("/api/orders/{public_uuid}/cancel")
async def passenger_cancel_order(public_uuid: str, payload: PassengerCancelIn, db: Session = Depends(get_db)):
    order = _find_order_by_uuid(db, public_uuid)
    # Басқа адам (тапсырыс нөмірін болжап) бас тарта алмауы үшін — тапсырыс берген телефонның соңғы 4 саны
    tail = _digits(payload.phone_tail)
    if len(tail) != 4 or not _digits(order.phone).endswith(tail):
        raise HTTPException(status_code=403, detail="Телефон нөмірінің соңғы 4 саны сәйкес емес / Последние 4 цифры телефона не совпадают.")
    if order.status not in PASSENGER_CANCELLABLE:
        raise HTTPException(
            status_code=400,
            detail="Заказ уже готовится, отменить нельзя. Свяжитесь с проводником / Тапсырыс әзірленуде, бас тартуға болмайды. Жолсерікке хабарласыңыз.",
        )
    old_status = order.status
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.utcnow()
    order.cancelled_by = "passenger"
    order.cancel_reason = "Отменено пассажиром / Жолаушы бас тартты"
    order.ready_eta_at = None
    db.add(OrderStatusHistory(order_id=order.id, old_status=old_status.value, new_status=OrderStatus.CANCELLED.value, changed_by="passenger"))
    db.commit()

    await hub.broadcast("order_status_update", {
        "order_id": order.id,
        "public_uuid": order.public_uuid,
        "order_number": order.order_number,
        "old_status": old_status.value,
        "new_status": OrderStatus.CANCELLED.value,
        "step_index": get_status_step_index(OrderStatus.CANCELLED),
        "cancel_reason": order.cancel_reason,
        "cancelled_by": "passenger",
        "ready_eta_at": None,
    })
    return {"success": True, "status": order.status.value}


@app.get("/api/orders/{public_uuid}/reorder")
def passenger_reorder_lines(public_uuid: str, db: Session = Depends(get_db)):
    """Бұрынғы тапсырыстан себетке дайын жолдар (қазіргі бағамен). Таусылған тағамдар `skipped` тізімінде."""
    order = _find_order_by_uuid(db, public_uuid)
    reset_expired_stoplist(db)
    lines, skipped = [], []
    for oi in order.items:
        item = db.get(MenuItem, oi.menu_item_id) if oi.menu_item_id else None
        if not item or not item.is_active or not item.is_available or item.category.code == LUNCHBOX_CATEGORY_CODE:
            skipped.append(oi.item_name_snapshot)
            continue
        variant = None
        unit_price = float(item.price)
        if oi.menu_variant_id:
            variant = db.get(MenuItemVariant, oi.menu_variant_id)
            if not variant or variant.menu_item_id != item.id or not variant.is_available:
                skipped.append(oi.item_name_snapshot)
                continue
            unit_price = float(variant.price)
        if unit_price <= 0:
            skipped.append(oi.item_name_snapshot)
            continue
        lines.append({
            "menu_item_id": item.id,
            "name_ru": item.name_ru, "name_kz": item.name_kz or item.name_ru, "name_en": item.name_en or item.name_ru,
            "variant_id": variant.id if variant else None,
            "variant_name_ru": variant.name_ru if variant else "",
            "variant_name_kz": (variant.name_kz or variant.name_ru) if variant else "",
            "variant_name_en": (variant.name_en or variant.name_ru) if variant else "",
            "unit_price": unit_price,
            "quantity": oi.quantity,
        })
    return {"lines": lines, "skipped": skipped}


class RatingIn(BaseModel):
    rating: int
    comment: Optional[str] = ""


@app.post("/api/orders/{public_uuid}/rating")
def passenger_rate_order(public_uuid: str, payload: RatingIn, db: Session = Depends(get_db)):
    order = _find_order_by_uuid(db, public_uuid)
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Баға тапсырыс жеткізілгеннен кейін қойылады / Оценить можно после доставки.")
    if not 1 <= payload.rating <= 5:
        raise HTTPException(status_code=400, detail="Баға 1-ден 5-ке дейін / Оценка от 1 до 5.")
    if order.rating is not None:
        raise HTTPException(status_code=400, detail="Сіз бұл тапсырысқа баға қойғансыз / Вы уже оценили этот заказ.")
    order.rating = payload.rating
    order.rating_comment = (payload.comment or "").strip()[:500]
    order.rated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "rating": order.rating}


# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================
def _safe_next(next_url: Optional[str], default: str) -> str:
    """Тек сайт ішіндегі жолға рұқсат (open-redirect болмауы үшін)."""
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return default


def _role_home(user: User) -> str:
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return "/admin"
    if user.role == UserRole.DELIVERY_STAFF:
        return "/staff"
    return "/kitchen"


def _role_can_open(user: User, path: str) -> bool:
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return True
    if path.startswith("/admin"):
        return False
    if path.startswith("/kitchen"):
        return user.role == UserRole.KITCHEN
    if path.startswith("/staff"):
        return user.role == UserRole.DELIVERY_STAFF
    return True


@app.get("/login", response_class=HTMLResponse)
@app.get("/kitchen/login", response_class=HTMLResponse)
@app.get("/staff/login", response_class=HTMLResponse)
@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request, next: Optional[str] = None):
    # /admin/login -> /admin, /staff/login -> /staff, /kitchen/login -> /kitchen; /login -> рөл бойынша
    default_next = {"/admin/login": "/admin", "/staff/login": "/staff", "/kitchen/login": "/kitchen"}.get(request.url.path, "/login")
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"next_url": _safe_next(next, default_next)},
    )


@app.post("/api/auth/login")
def login_api(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/login"),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.username == username.strip()))
    if not user or not verify_password(password.strip(), user.password_hash):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    create_session_cookie(response, user)

    # Рөлге сай бетке бағыттаймыз: әкімші /admin-ге, аспаз /kitchen-ге, жолсерік /staff-қа
    redirect_target = _safe_next(next, "/login")
    if redirect_target.startswith("/login") or not _role_can_open(user, redirect_target):
        redirect_target = _role_home(user)

    return {"success": True, "redirect_url": redirect_target, "role": user.role.value}


@app.get("/logout")
@app.post("/api/auth/logout")
def logout_api(response: Response):
    response.delete_cookie("dar_res_session")
    return RedirectResponse(url="/", status_code=303)


# ==============================================================================
# KITCHEN DASHBOARD (KANBAN)
# ==============================================================================
@app.get("/kitchen", response_class=HTMLResponse)
def kitchen_dashboard(
    request: Request,
    user: User = Depends(require_role([UserRole.KITCHEN, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    reset_expired_stoplist(db)
    active_orders = db.scalars(
        select(Order)
        .where(Order.status != OrderStatus.DELIVERED, Order.status != OrderStatus.CANCELLED)
        .order_by(desc(Order.id))
    ).all()

    completed_today = db.scalars(
        select(Order)
        .where(Order.status.in_([OrderStatus.DELIVERED, OrderStatus.CANCELLED]))
        .order_by(desc(Order.id))
        .limit(15)
    ).all()

    menu_items = db.scalars(
        select(MenuItem).where(MenuItem.is_active.is_(True)).order_by(MenuItem.category_id, MenuItem.name_ru)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="kitchen.html",
        context={
            "user": user,
            "active_orders": active_orders,
            "completed_orders": completed_today,
            "menu_items": menu_items,
            "departure_fmt": lambda o: format_departure(o.departure_at),
            "eta_fmt": lambda o: iso_utc(o.ready_eta_at) or "",
            "group_key_fmt": order_group_key,
        },
    )


class StatusUpdateIn(BaseModel):
    new_status: OrderStatus
    cancel_reason: Optional[str] = ""
    eta_minutes: Optional[int] = None  # «N минутта дайын болады» — қабылдау/әзірлеу кезінде аспаз көрсетеді


VALID_STATUS_TRANSITIONS = {
    OrderStatus.NEW: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
    OrderStatus.ACCEPTED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
    OrderStatus.READY: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
    OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


@app.patch("/api/kitchen/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    payload: StatusUpdateIn,
    user: User = Depends(require_role([UserRole.KITCHEN, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status
    target_status = payload.new_status

    # Validate transition
    allowed = VALID_STATUS_TRANSITIONS.get(old_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый переход статуса из {old_status.value} в {target_status.value}."
        )

    order.status = target_status
    now = datetime.utcnow()

    if payload.eta_minutes is not None and target_status in (OrderStatus.ACCEPTED, OrderStatus.PREPARING):
        order.ready_eta_at = now + timedelta(minutes=max(1, min(int(payload.eta_minutes), 240)))

    if target_status == OrderStatus.ACCEPTED:
        order.accepted_at = now
    elif target_status == OrderStatus.PREPARING:
        order.preparing_at = now
    elif target_status == OrderStatus.READY:
        order.ready_at = now
        order.ready_eta_at = None
    elif target_status == OrderStatus.OUT_FOR_DELIVERY:
        order.out_for_delivery_at = now
    elif target_status == OrderStatus.DELIVERED:
        order.delivered_at = now
    elif target_status == OrderStatus.CANCELLED:
        order.cancelled_at = now
        order.cancelled_by = "kitchen"
        order.ready_eta_at = None
        order.cancel_reason = payload.cancel_reason or "Отменено кухней/администратором"

    db.add(OrderStatusHistory(
        order_id=order.id,
        old_status=old_status.value,
        new_status=target_status.value,
        changed_by=f"{user.role.value}:{user.username}",
    ))
    db.commit()

    # Real-time broadcast
    await hub.broadcast("order_status_update", {
        "order_id": order.id,
        "public_uuid": order.public_uuid,
        "order_number": order.order_number,
        "old_status": old_status.value,
        "new_status": target_status.value,
        "step_index": get_status_step_index(target_status),
        "cancel_reason": order.cancel_reason,
        "cancelled_by": order.cancelled_by,
        "ready_eta_at": iso_utc(order.ready_eta_at),
    })

    return {"success": True, "order_id": order.id, "new_status": target_status.value, "ready_eta_at": iso_utc(order.ready_eta_at)}


class EtaUpdateIn(BaseModel):
    eta_minutes: int


@app.patch("/api/kitchen/orders/{order_id}/eta")
async def update_order_eta(
    order_id: int,
    payload: EtaUpdateIn,
    user: User = Depends(require_role([UserRole.KITCHEN, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in (OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.PREPARING):
        raise HTTPException(status_code=400, detail="Уақытты тек дайын болмаған тапсырысқа қоюға болады.")
    order.ready_eta_at = datetime.utcnow() + timedelta(minutes=max(1, min(payload.eta_minutes, 240)))
    db.commit()
    await hub.broadcast("order_status_update", {
        "order_id": order.id,
        "public_uuid": order.public_uuid,
        "order_number": order.order_number,
        "old_status": order.status.value,
        "new_status": order.status.value,
        "step_index": get_status_step_index(order.status),
        "cancel_reason": order.cancel_reason,
        "cancelled_by": order.cancelled_by,
        "ready_eta_at": iso_utc(order.ready_eta_at),
    })
    return {"success": True, "ready_eta_at": iso_utc(order.ready_eta_at)}


class AvailabilityUpdateIn(BaseModel):
    is_available: bool


@app.patch("/api/kitchen/menu-items/{item_id}/availability")
async def update_item_availability(
    item_id: int,
    payload: AvailabilityUpdateIn,
    user: User = Depends(require_role([UserRole.KITCHEN, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_available = payload.is_available
    item.sold_out_date = None if payload.is_available else kz_today()
    db.commit()

    # Broadcast availability to all passenger apps live
    await hub.broadcast("item_availability_update", {
        "item_id": item.id,
        "name_ru": item.name_ru,
        "is_available": item.is_available,
    })

    return {"success": True, "item_id": item.id, "is_available": item.is_available}


# ==============================================================================
# DELIVERY STAFF PORTAL
# ==============================================================================
@app.get("/staff", response_class=HTMLResponse)
def staff_dashboard(
    request: Request,
    user: User = Depends(require_role([UserRole.DELIVERY_STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    ready_orders = db.scalars(
        select(Order).where(Order.status == OrderStatus.READY).order_by(Order.id)
    ).all()

    delivering_orders = db.scalars(
        select(Order).where(Order.status == OrderStatus.OUT_FOR_DELIVERY).order_by(Order.id)
    ).all()

    delivered_today = db.scalars(
        select(Order).where(Order.status == OrderStatus.DELIVERED).order_by(desc(Order.id)).limit(10)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="staff.html",
        context={
            "user": user,
            "ready_orders": ready_orders,
            "delivering_orders": delivering_orders,
            "delivered_orders": delivered_today,
            # Бір орынға (жолаушыға) бірнеше тапсырыс болса — жолсерікке бірге жеткізу үшін белгі
            "group_counts": _group_counts(list(ready_orders) + list(delivering_orders)),
            "group_key_fmt": order_group_key,
        },
    )


def _group_counts(orders: list[Order]) -> dict:
    counts: dict[str, int] = {}
    for o in orders:
        k = order_group_key(o)
        counts[k] = counts.get(k, 0) + 1
    return counts


@app.post("/api/staff/orders/{order_id}/take")
@app.patch("/api/staff/orders/{order_id}/take")
async def staff_take_order(
    order_id: int,
    user: User = Depends(require_role([UserRole.DELIVERY_STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    # Atomic conditional update prevents concurrent staff take race conditions
    result = db.execute(
        update(Order)
        .where(Order.id == order_id, Order.status == OrderStatus.READY)
        .values(status=OrderStatus.OUT_FOR_DELIVERY, out_for_delivery_at=now)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail="Заказ уже взят другим сотрудником или не готов.")

    order = db.get(Order, order_id)

    assignment = DeliveryAssignment(
        order_id=order.id,
        staff_user_id=user.id,
        staff_name=user.full_name or user.username,
        taken_at=now,
    )
    db.add(assignment)
    db.add(OrderStatusHistory(
        order_id=order.id,
        old_status=OrderStatus.READY.value,
        new_status=OrderStatus.OUT_FOR_DELIVERY.value,
        changed_by=f"staff:{user.username}",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Заказ уже взят другим сотрудником.")

    await hub.broadcast("order_status_update", {
        "order_id": order.id,
        "public_uuid": order.public_uuid,
        "order_number": order.order_number,
        "new_status": OrderStatus.OUT_FOR_DELIVERY.value,
        "step_index": get_status_step_index(OrderStatus.OUT_FOR_DELIVERY),
        "staff_name": assignment.staff_name,
    })

    return {"success": True, "order_id": order.id, "status": "OUT_FOR_DELIVERY"}


@app.post("/api/staff/orders/{order_id}/delivered")
@app.patch("/api/staff/orders/{order_id}/delivered")
async def staff_mark_delivered(
    order_id: int,
    user: User = Depends(require_role([UserRole.DELIVERY_STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.OUT_FOR_DELIVERY and user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=400, detail="Заказ должен быть в статусе 'OUT_FOR_DELIVERY'.")

    order.status = OrderStatus.DELIVERED
    order.delivered_at = datetime.utcnow()

    assignment = db.scalar(select(DeliveryAssignment).where(DeliveryAssignment.order_id == order.id))
    if assignment:
        assignment.delivered_at = datetime.utcnow()

    db.add(OrderStatusHistory(
        order_id=order.id,
        old_status=OrderStatus.OUT_FOR_DELIVERY.value,
        new_status=OrderStatus.DELIVERED.value,
        changed_by=f"staff:{user.username}",
    ))
    db.commit()

    await hub.broadcast("order_status_update", {
        "order_id": order.id,
        "public_uuid": order.public_uuid,
        "order_number": order.order_number,
        "new_status": OrderStatus.DELIVERED.value,
        "step_index": get_status_step_index(OrderStatus.DELIVERED),
    })

    return {"success": True, "order_id": order.id, "status": "DELIVERED"}


# ==============================================================================
# ADMIN OPERATIONS & MANAGEMENT
# ==============================================================================
# ==============================================================================
# CURRENT AUTH USER API
# ==============================================================================
@app.get("/api/auth/me")
def get_current_user_api(user: Optional[User] = Depends(get_current_user_optional)):
    if not user:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
        }
    }


# ==============================================================================
# KITCHEN & STAFF REST APIS
# ==============================================================================
@app.get("/api/kitchen/orders")
def get_kitchen_orders_api(
    user: User = Depends(require_role([UserRole.KITCHEN, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    orders = db.scalars(
        select(Order)
        .where(Order.status != OrderStatus.DELIVERED)
        .order_by(desc(Order.id))
        .limit(50)
    ).all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "public_uuid": o.public_uuid,
            "train_no": o.train_no,
            "wagon_no": o.wagon_no,
            "seat_no": o.seat_no,
            "compartment_no": o.compartment_no,
            "passenger_name": o.passenger_name,
            "phone": o.phone,
            "status": o.status.value,
            "total": float(o.total),
            "comment": o.comment,
            "created_at": o.created_at.strftime("%H:%M"),
            "order_type": o.order_type,
            "departure_at": format_departure(o.departure_at),
            "ready_eta_at": iso_utc(o.ready_eta_at),
            "group_key": order_group_key(o),
            "rating": o.rating,
            "items": [
                {
                    "name": oi.item_name_snapshot,
                    "variant": oi.variant_snapshot,
                    "quantity": oi.quantity,
                    "price": float(oi.price_snapshot),
                }
                for oi in o.items
            ]
        }
        for o in orders
    ]


@app.get("/api/staff/orders")
def get_staff_orders_api(
    user: User = Depends(require_role([UserRole.DELIVERY_STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    ready_orders = db.scalars(select(Order).where(Order.status == OrderStatus.READY).order_by(Order.id)).all()
    delivering_orders = db.scalars(select(Order).where(Order.status == OrderStatus.OUT_FOR_DELIVERY).order_by(Order.id)).all()
    def serialize_order(o):
        return {
            "id": o.id,
            "order_number": o.order_number,
            "public_uuid": o.public_uuid,
            "train_no": o.train_no,
            "wagon_no": o.wagon_no,
            "seat_no": o.seat_no,
            "compartment_no": o.compartment_no,
            "passenger_name": o.passenger_name,
            "phone": o.phone,
            "status": o.status.value,
            "total": float(o.total),
            "items": [
                {"name": oi.item_name_snapshot, "variant": oi.variant_snapshot, "quantity": oi.quantity}
                for oi in o.items
            ]
        }
    return {
        "ready": [serialize_order(o) for o in ready_orders],
        "delivering": [serialize_order(o) for o in delivering_orders],
    }


# ==============================================================================
# ADMIN OPERATIONS, VIEWS & REST ENDPOINTS
# ==============================================================================
def get_operations_kpis(db: Session):
    total_orders = db.scalar(select(func.count(Order.id))) or 0
    total_sales = db.scalar(select(func.sum(Order.total)).where(Order.status == OrderStatus.DELIVERED)) or 0
    active_count = db.scalar(
        select(func.count(Order.id)).where(Order.status.notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED]))
    ) or 0
    delivered_count = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)) or 0
    cancelled_count = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED)) or 0

    # Average Prep Time & Delivery Time
    prep_times = []
    delivery_times = []
    finished_orders = db.scalars(select(Order).where(Order.status == OrderStatus.DELIVERED).limit(100)).all()
    for o in finished_orders:
        if o.accepted_at and o.ready_at:
            diff = (o.ready_at - o.accepted_at).total_seconds() / 60.0
            if 0 < diff < 240:
                prep_times.append(diff)
        if o.out_for_delivery_at and o.delivered_at:
            diff = (o.delivered_at - o.out_for_delivery_at).total_seconds() / 60.0
            if 0 < diff < 120:
                delivery_times.append(diff)

    avg_prep = round(sum(prep_times) / len(prep_times), 1) if prep_times else 14.5
    avg_deliv = round(sum(delivery_times) / len(delivery_times), 1) if delivery_times else 5.2

    # Popular items ranking
    rows = db.execute(
        select(
            OrderItem.item_name_snapshot,
            func.sum(OrderItem.quantity).label("total_qty"),
            func.sum(OrderItem.line_total).label("total_revenue"),
        )
        .group_by(OrderItem.item_name_snapshot)
        .order_by(desc("total_qty"))
        .limit(10)
    ).all()
    popular_items = [
        {"name": r[0], "count": int(r[1] or 0), "revenue": float(r[2] or 0)}
        for r in rows
    ]

    delivery_rate = 100.0
    if delivered_count + cancelled_count > 0:
        delivery_rate = (delivered_count / (delivered_count + cancelled_count)) * 100.0

    avg_order_val = (total_sales / delivered_count) if delivered_count > 0 else 0

    rating_row = db.execute(select(func.avg(Order.rating), func.count(Order.rating)).where(Order.rating.is_not(None))).one()
    avg_rating = round(float(rating_row[0]), 2) if rating_row[0] is not None else None
    rating_count = int(rating_row[1] or 0)

    return {
        "avg_rating": avg_rating,
        "rating_count": rating_count,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "active_count": active_count,
        "delivered_count": delivered_count,
        "cancelled_count": cancelled_count,
        "avg_prep_time": avg_prep,
        "avg_delivery_time": avg_deliv,
        "popular_items": popular_items,
        "delivery_success_rate": delivery_rate,
        "avg_order_value": avg_order_val,
    }


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/settings", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    kpis = get_operations_kpis(db)
    recent_orders = db.scalars(select(Order).order_by(desc(Order.id)).limit(15)).all()
    trains = db.scalars(select(Train).order_by(Train.train_number)).all()
    categories = db.scalars(select(MenuCategory).order_by(MenuCategory.sort_order)).all()
    ordering_mode = db.scalar(select(SystemSetting.value).where(SystemSetting.key == "ordering_mode")) or "OPEN"

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "recent_orders": recent_orders,
            "trains": trains,
            "categories": categories,
            "ordering_mode": ordering_mode,
            **kpis,
        },
    )


@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders_page(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    orders = db.scalars(select(Order).order_by(desc(Order.id)).limit(100)).all()
    trains = db.scalars(select(Train).order_by(Train.train_number)).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_orders.html",
        context={"user": user, "orders": orders, "trains": trains},
    )


@app.get("/api/admin/orders")
def get_admin_orders_api(
    status: Optional[str] = None,
    train: Optional[str] = None,
    q: Optional[str] = None,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    stmt = select(Order).order_by(desc(Order.id))
    if status and status != "ALL":
        stmt = stmt.where(Order.status == status)
    if train and train != "ALL":
        stmt = stmt.where(Order.train_no == train)
    if q:
        term = f"%{q.lower()}%"
        stmt = stmt.where(
            (Order.order_number.ilike(term))
            | (Order.passenger_name.ilike(term))
            | (Order.phone.ilike(term))
            | (Order.seat_no.ilike(term))
        )
    orders = db.scalars(stmt.limit(100)).all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "public_uuid": o.public_uuid,
            "train_no": o.train_no,
            "wagon_no": o.wagon_no,
            "seat_no": o.seat_no,
            "passenger_name": o.passenger_name,
            "phone": o.phone,
            "subtotal": float(o.subtotal),
            "service_charge": float(o.service_charge),
            "total": float(o.total),
            "status": o.status.value,
            "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
        }
        for o in orders
    ]


@app.get("/admin/menu", response_class=HTMLResponse)
@app.get("/admin/categories", response_class=HTMLResponse)
def admin_menu_page(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    categories = db.scalars(select(MenuCategory).order_by(MenuCategory.sort_order)).all()
    items = db.scalars(select(MenuItem).order_by(MenuItem.category_id, MenuItem.name_ru)).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_menu.html",
        context={
            "user": user,
            "categories": categories,
            "items": items,
            "lunchbox_code": LUNCHBOX_CATEGORY_CODE,
            "open_categories": request.url.path == "/admin/categories",
        },
    )


@app.get("/api/admin/menu")
def get_admin_menu_api(
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    categories = db.scalars(select(MenuCategory).order_by(MenuCategory.sort_order)).all()
    return [
        {
            "id": c.id,
            "code": c.code,
            "name_ru": c.name_ru,
            "items": [
                {
                    "id": item.id,
                    "name_ru": item.name_ru,
                    "price": float(item.price),
                    "is_available": item.is_available,
                }
                for item in c.items
                if item.is_active
            ]
        }
        for c in categories
    ]


# ==============================================================================
# ADMIN MENU MANAGEMENT: тағам қосу/өңдеу/баға/сурет/өлшем нұсқалары/санаттар
# ==============================================================================
MENU_UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "menu"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PRICE = Decimal("10000000")


def _price_or_400(value: float) -> Decimal:
    try:
        price = Decimal(str(value))
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректная цена.")
    if price < 0 or price > MAX_PRICE:
        raise HTTPException(status_code=400, detail="Цена должна быть от 0 до 10 000 000 ₸.")
    return price


def _is_lunchbox_category(db: Session, category_id: int) -> bool:
    code = db.scalar(select(MenuCategory.code).where(MenuCategory.id == category_id))
    return code == LUNCHBOX_CATEGORY_CODE


def _admin_item_dict(item: MenuItem) -> dict:
    return {
        "id": item.id,
        "sku": item.sku,
        "category_id": item.category_id,
        "name_ru": item.name_ru,
        "name_kz": item.name_kz,
        "name_en": item.name_en,
        "description_ru": item.description_ru,
        "description_kz": item.description_kz,
        "description_en": item.description_en,
        "ingredients_ru": item.ingredients_ru,
        "ingredients_kz": item.ingredients_kz,
        "ingredients_en": item.ingredients_en,
        "weight_value": item.weight_value,
        "volume_value": item.volume_value,
        "price": float(item.price),
        "image_url": item.image_url,
        "is_available": item.is_available,
        "is_active": item.is_active,
        "is_popular": item.is_popular,
        "variants": [
            {
                "id": v.id,
                "name_ru": v.name_ru,
                "name_kz": v.name_kz,
                "name_en": v.name_en,
                "volume_or_weight": v.volume_or_weight,
                "price": float(v.price),
                "is_available": v.is_available,
            }
            for v in item.variants
        ],
    }


def _detect_image_ext(data: bytes) -> Optional[str]:
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


@app.get("/api/admin/menu/items/{item_id}")
def admin_get_menu_item(
    item_id: int,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return _admin_item_dict(item)


@app.post("/api/admin/menu/upload-image")
def upload_menu_image(
    file: UploadFile = File(...),
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Файл слишком большой (максимум 5 МБ).")
    ext = _detect_image_ext(data)
    if not ext:
        raise HTTPException(status_code=400, detail="Допускаются только изображения JPG, PNG или WEBP.")
    MENU_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    (MENU_UPLOAD_DIR / filename).write_bytes(data)
    return {"success": True, "url": f"/static/uploads/menu/{filename}"}


class CreateMenuItemIn(BaseModel):
    category_id: int
    name_ru: str
    name_kz: Optional[str] = ""
    name_en: Optional[str] = ""
    price: float
    weight_value: Optional[str] = ""
    volume_value: Optional[str] = ""
    image_url: Optional[str] = ""
    description_ru: Optional[str] = ""
    description_kz: Optional[str] = ""
    description_en: Optional[str] = ""
    ingredients_ru: Optional[str] = ""
    ingredients_kz: Optional[str] = ""
    ingredients_en: Optional[str] = ""
    is_popular: Optional[bool] = False
    is_available: Optional[bool] = True


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


@app.post("/api/admin/menu/items")
async def create_menu_item(
    payload: CreateMenuItemIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    category = db.get(MenuCategory, payload.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Категория не найдена.")
    if category.code == LUNCHBOX_CATEGORY_CODE:
        raise HTTPException(
            status_code=400,
            detail="Новые ланчбоксы добавляются в app/lunchbox_data.py; здесь можно менять только цену существующих.",
        )
    name_ru = _clean(payload.name_ru)
    if not name_ru:
        raise HTTPException(status_code=400, detail="Укажите название блюда (RU).")
    price = _price_or_400(payload.price)

    item = MenuItem(
        category_id=category.id,
        name_ru=name_ru,
        name_kz=_clean(payload.name_kz) or name_ru,
        name_en=_clean(payload.name_en) or name_ru,
        description_ru=_clean(payload.description_ru),
        description_kz=_clean(payload.description_kz),
        description_en=_clean(payload.description_en),
        ingredients_ru=_clean(payload.ingredients_ru),
        ingredients_kz=_clean(payload.ingredients_kz),
        ingredients_en=_clean(payload.ingredients_en),
        weight_value=_clean(payload.weight_value),
        volume_value=_clean(payload.volume_value),
        price=price,
        image_url=_clean(payload.image_url),
        is_available=bool(payload.is_available),
        is_popular=bool(payload.is_popular),
        is_active=True,
    )
    db.add(item)
    db.flush()
    prefix = re.sub(r"[^A-Z0-9]", "", category.code.upper())[:3] or "ITM"
    item.sku = f"{prefix}-{item.id:03d}"
    db.commit()
    db.refresh(item)
    await hub.broadcast("menu_updated", {"item_id": item.id})
    return {"success": True, "item_id": item.id, "sku": item.sku}


class UpdateMenuItemIn(BaseModel):
    category_id: Optional[int] = None
    name_ru: Optional[str] = None
    name_kz: Optional[str] = None
    name_en: Optional[str] = None
    price: Optional[float] = None
    weight_value: Optional[str] = None
    volume_value: Optional[str] = None
    image_url: Optional[str] = None
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    description_en: Optional[str] = None
    ingredients_ru: Optional[str] = None
    ingredients_kz: Optional[str] = None
    ingredients_en: Optional[str] = None
    is_popular: Optional[bool] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None


@app.patch("/api/admin/menu/items/{item_id}")
async def update_menu_item(
    item_id: int,
    payload: UpdateMenuItemIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.category_id is not None and payload.category_id != item.category_id:
        new_cat = db.get(MenuCategory, payload.category_id)
        if not new_cat:
            raise HTTPException(status_code=400, detail="Категория не найдена.")
        if new_cat.code == LUNCHBOX_CATEGORY_CODE or _is_lunchbox_category(db, item.category_id):
            raise HTTPException(status_code=400, detail="Ланчбоксы нельзя переносить в другие категории и обратно.")
        item.category_id = new_cat.id

    if payload.name_ru is not None:
        if not payload.name_ru.strip():
            raise HTTPException(status_code=400, detail="Название (RU) не может быть пустым.")
        item.name_ru = payload.name_ru.strip()
    for field in (
        "name_kz", "name_en", "weight_value", "volume_value", "image_url",
        "description_ru", "description_kz", "description_en",
        "ingredients_ru", "ingredients_kz", "ingredients_en",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value.strip())
    if payload.price is not None:
        item.price = _price_or_400(payload.price)
    if payload.is_popular is not None:
        item.is_popular = payload.is_popular
    if payload.is_available is not None:
        item.is_available = payload.is_available
        item.sold_out_date = None  # админ формасы — тұрақты күй (стоп-лист авто-тазалауына жатпайды)
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.commit()
    await hub.broadcast("menu_updated", {"item_id": item.id})
    return {"success": True, "item_id": item.id}


@app.delete("/api/admin/menu/items/{item_id}")
async def archive_menu_item(
    item_id: int,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_active = False  # preserve order snapshots
    db.commit()
    await hub.broadcast("menu_updated", {"item_id": item.id})
    return {"success": True, "item_id": item.id, "archived": True}


# --- Өлшем / көлем нұсқалары (мысалы: Шай 200 мл / 400 мл — әрқайсысының өз бағасы) ---
class VariantCreateIn(BaseModel):
    name_ru: str
    name_kz: Optional[str] = ""
    name_en: Optional[str] = ""
    volume_or_weight: str
    price: float
    is_available: Optional[bool] = True


class VariantUpdateIn(BaseModel):
    name_ru: Optional[str] = None
    name_kz: Optional[str] = None
    name_en: Optional[str] = None
    volume_or_weight: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None


@app.post("/api/admin/menu/items/{item_id}/variants")
async def create_item_variant(
    item_id: int,
    payload: VariantCreateIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    name_ru = _clean(payload.name_ru)
    if not name_ru or not _clean(payload.volume_or_weight):
        raise HTTPException(status_code=400, detail="Укажите название и объём/вес варианта.")
    variant = MenuItemVariant(
        menu_item_id=item.id,
        name_ru=name_ru,
        name_kz=_clean(payload.name_kz) or name_ru,
        name_en=_clean(payload.name_en) or name_ru,
        volume_or_weight=_clean(payload.volume_or_weight),
        price=_price_or_400(payload.price),
        is_available=bool(payload.is_available),
    )
    db.add(variant)
    db.commit()
    await hub.broadcast("menu_updated", {"item_id": item.id})
    return {"success": True, "variant_id": variant.id}


@app.patch("/api/admin/menu/variants/{variant_id}")
async def update_item_variant(
    variant_id: int,
    payload: VariantUpdateIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    variant = db.get(MenuItemVariant, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    if payload.name_ru is not None:
        if not payload.name_ru.strip():
            raise HTTPException(status_code=400, detail="Название варианта не может быть пустым.")
        variant.name_ru = payload.name_ru.strip()
    if payload.name_kz is not None:
        variant.name_kz = payload.name_kz.strip()
    if payload.name_en is not None:
        variant.name_en = payload.name_en.strip()
    if payload.volume_or_weight is not None:
        variant.volume_or_weight = payload.volume_or_weight.strip()
    if payload.price is not None:
        variant.price = _price_or_400(payload.price)
    if payload.is_available is not None:
        variant.is_available = payload.is_available
    db.commit()
    await hub.broadcast("menu_updated", {"item_id": variant.menu_item_id})
    return {"success": True, "variant_id": variant.id}


@app.delete("/api/admin/menu/variants/{variant_id}")
async def delete_item_variant(
    variant_id: int,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    variant = db.get(MenuItemVariant, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    item_id = variant.menu_item_id
    db.delete(variant)
    db.commit()
    await hub.broadcast("menu_updated", {"item_id": item_id})
    return {"success": True}


# --- Санаттар ---
class CreateCategoryIn(BaseModel):
    code: str
    name_ru: str
    name_kz: str
    name_en: str
    sort_order: Optional[int] = None


@app.post("/api/admin/menu/categories")
async def create_category(
    payload: CreateCategoryIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", code):
        raise HTTPException(status_code=400, detail="Код: только латиница, цифры и дефис (например: desserts).")
    if db.scalar(select(MenuCategory).where(MenuCategory.code == code)):
        raise HTTPException(status_code=400, detail="Категория с таким кодом уже существует.")
    if not payload.name_ru.strip():
        raise HTTPException(status_code=400, detail="Укажите название категории (RU).")
    sort_order = payload.sort_order
    if sort_order is None:
        sort_order = (db.scalar(select(func.max(MenuCategory.sort_order))) or 0) + 1
    cat = MenuCategory(
        code=code,
        name_ru=payload.name_ru.strip(),
        name_kz=payload.name_kz.strip() or payload.name_ru.strip(),
        name_en=payload.name_en.strip() or payload.name_ru.strip(),
        sort_order=sort_order,
        is_active=True,
    )
    db.add(cat)
    db.commit()
    await hub.broadcast("menu_updated", {"category_id": cat.id})
    return {"success": True, "category_id": cat.id}


class UpdateCategoryIn(BaseModel):
    name_ru: Optional[str] = None
    name_kz: Optional[str] = None
    name_en: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


@app.patch("/api/admin/menu/categories/{category_id}")
async def update_category(
    category_id: int,
    payload: UpdateCategoryIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    cat = db.get(MenuCategory, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if payload.name_ru is not None:
        if not payload.name_ru.strip():
            raise HTTPException(status_code=400, detail="Название (RU) не может быть пустым.")
        cat.name_ru = payload.name_ru.strip()
    if payload.name_kz is not None:
        cat.name_kz = payload.name_kz.strip() or cat.name_ru
    if payload.name_en is not None:
        cat.name_en = payload.name_en.strip() or cat.name_ru
    if payload.sort_order is not None:
        cat.sort_order = payload.sort_order
    if payload.is_active is not None:
        cat.is_active = payload.is_active
    db.commit()
    await hub.broadcast("menu_updated", {"category_id": cat.id})
    return {"success": True, "category_id": cat.id}


@app.get("/admin/trains", response_class=HTMLResponse)
@app.get("/admin/carriages", response_class=HTMLResponse)
def admin_trains_page(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    trains = db.scalars(select(Train).order_by(Train.train_number)).all()
    host = request.base_url
    return templates.TemplateResponse(
        request=request,
        name="admin_trains.html",
        context={
            "user": user,
            "trains": trains,
            "base_url": str(host).rstrip("/"),
            "open_carriages": request.url.path == "/admin/carriages",
        },
    )


@app.get("/api/admin/trains")
def get_admin_trains_api(
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    trains = db.scalars(select(Train).order_by(Train.train_number)).all()
    return [
        {
            "id": t.id,
            "train_number": t.train_number,
            "route_name": t.route_name,
            "is_active": t.is_active,
            "cook_name": t.cook_name,
            "whatsapp_phone": t.whatsapp_phone,
            "carriages": [
                {
                    "id": c.id,
                    "carriage_number": c.carriage_number,
                    "carriage_type": c.carriage_type,
                    "qr_token": c.qr_token,
                    "delivery_enabled": c.delivery_enabled,
                }
                for c in t.carriages
            ]
        }
        for t in trains
    ]


class CreateTrainIn(BaseModel):
    train_number: str
    route_name: str
    cook_name: Optional[str] = ""
    whatsapp_phone: Optional[str] = ""


def _validated_whatsapp(raw: Optional[str]) -> str:
    """Бос болса — бос жол; болмаса дұрыс нөмір болуы керек (мысалы +7 707 123 45 67)."""
    if not raw or not raw.strip():
        return ""
    if not is_valid_phone(raw):
        raise HTTPException(status_code=400, detail="WhatsApp нөмірі қате. Мысалы: +7 707 123 45 67")
    return normalize_phone(raw)


@app.post("/api/admin/trains")
def create_train(
    payload: CreateTrainIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Train).where(Train.train_number == payload.train_number.strip()))
    if existing:
        raise HTTPException(status_code=400, detail="Поезд с таким номером уже существует")

    train = Train(
        train_number=payload.train_number.strip(),
        route_name=payload.route_name.strip(),
        cook_name=(payload.cook_name or "").strip(),
        whatsapp_phone=_validated_whatsapp(payload.whatsapp_phone),
        is_active=True,
    )
    db.add(train)
    db.commit()
    return {"success": True, "train_id": train.id}


class UpdateTrainIn(BaseModel):
    route_name: Optional[str] = None
    cook_name: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    is_active: Optional[bool] = None


@app.patch("/api/admin/trains/{train_id}")
def update_train(
    train_id: int,
    payload: UpdateTrainIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    train = db.get(Train, train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    if payload.route_name is not None:
        train.route_name = payload.route_name.strip()
    if payload.cook_name is not None:
        train.cook_name = payload.cook_name.strip()
    if payload.whatsapp_phone is not None:
        train.whatsapp_phone = _validated_whatsapp(payload.whatsapp_phone)
    if payload.is_active is not None:
        train.is_active = payload.is_active
    db.commit()
    return {"success": True, "train_id": train.id, "whatsapp_phone": train.whatsapp_phone}


class CreateCarriageIn(BaseModel):
    train_id: int
    carriage_number: str
    carriage_type: Optional[str] = "Купе"


@app.post("/api/admin/carriages")
def create_carriage(
    payload: CreateCarriageIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    train = db.get(Train, payload.train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    token = uuid.uuid4().hex[:12]
    carriage = Carriage(
        train_id=train.id,
        carriage_number=payload.carriage_number.strip(),
        carriage_type=payload.carriage_type or "Купе",
        qr_token=token,
        delivery_enabled=True,
        is_active=True,
    )
    db.add(carriage)
    db.flush()
    db.add(QRCodeContext(
        public_token=token,
        train_number=train.train_number,
        carriage_number=carriage.carriage_number,
        is_active=True,
    ))
    db.commit()
    return {"success": True, "carriage_id": carriage.id, "qr_token": token}


# --- QR CODES MANAGEMENT ---
@app.get("/admin/qr", response_class=HTMLResponse)
def admin_qr_page(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    qr_codes = db.scalars(select(QRCodeContext).order_by(desc(QRCodeContext.id))).all()
    host = request.base_url
    return templates.TemplateResponse(
        request=request,
        name="admin_qr.html",
        context={"user": user, "qr_codes": qr_codes, "base_url": str(host).rstrip("/")},
    )


class GenerateQrIn(BaseModel):
    train_number: str
    carriage_number: str
    table_number: Optional[str] = ""


@app.post("/api/admin/qr/generate")
def generate_qr_api(
    payload: GenerateQrIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    token = uuid.uuid4().hex[:12]
    qr = QRCodeContext(
        public_token=token,
        train_number=payload.train_number.strip(),
        carriage_number=payload.carriage_number.strip(),
        table_number=payload.table_number.strip() if payload.table_number else None,
        is_active=True,
    )
    db.add(qr)
    db.commit()
    return {"success": True, "token": token, "qr_id": qr.id}


class ToggleQrIn(BaseModel):
    is_active: bool


@app.patch("/api/admin/qr/{qr_id}/toggle")
def toggle_qr_api(
    qr_id: int,
    payload: ToggleQrIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    qr = db.get(QRCodeContext, qr_id)
    if not qr:
        raise HTTPException(status_code=404, detail="QR context not found")
    qr.is_active = payload.is_active
    db.commit()
    return {"success": True, "is_active": qr.is_active}


# --- USERS MANAGEMENT ---
@app.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User).order_by(User.id)).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={"user": user, "users": users},
    )


@app.get("/api/admin/users")
def get_admin_users_api(
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
        }
        for u in users
    ]


class CreateUserIn(BaseModel):
    username: str
    password: str
    role: UserRole
    full_name: Optional[str] = ""


@app.post("/api/admin/users")
def create_user_api(
    payload: CreateUserIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(User).where(User.username == payload.username.strip()))
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    new_user = User(
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        full_name=payload.full_name.strip() if payload.full_name else "",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    return {"success": True, "user_id": new_user.id}


class UpdateUserIn(BaseModel):
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@app.patch("/api/admin/users/{user_id}")
def update_user_api(
    user_id: int,
    payload: UpdateUserIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.password:
        target_user.password_hash = hash_password(payload.password)
    if payload.role:
        target_user.role = payload.role
    if payload.is_active is not None:
        target_user.is_active = payload.is_active

    db.commit()
    return {"success": True, "user_id": target_user.id}


# --- REPORTS & ANALYTICS ---
@app.get("/admin/reports", response_class=HTMLResponse)
def admin_reports_page(
    request: Request,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    kpis = get_operations_kpis(db)
    ordering_mode = db.scalar(select(SystemSetting.value).where(SystemSetting.key == "ordering_mode")) or "OPEN"

    # Status counts map
    status_counts_raw = db.execute(select(Order.status, func.count(Order.id)).group_by(Order.status)).all()
    status_counts = {r[0].value: r[1] for r in status_counts_raw}

    return templates.TemplateResponse(
        request=request,
        name="admin_reports.html",
        context={
            "user": user,
            "ordering_mode": ordering_mode,
            "status_counts": status_counts,
            **kpis,
        },
    )


def _parse_report_date(raw: Optional[str], end: bool = False) -> Optional[datetime]:
    """YYYY-MM-DD (KZ күні) -> UTC naive datetime (дерекқор UTC-те сақтайды)."""
    if not raw:
        return None
    try:
        d = datetime.strptime(raw.strip(), "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Дата форматы: ЖЖЖЖ-АА-КК / YYYY-MM-DD")
    if end:
        d = d + timedelta(days=1)
    return (d.replace(tzinfo=KZ_TZ)).astimezone(timezone.utc).replace(tzinfo=None)


STATUS_LABELS = {
    "NEW": "Жаңа / Новый", "ACCEPTED": "Қабылданды / Принят", "PREPARING": "Әзірленуде / Готовится",
    "READY": "Дайын / Готов", "OUT_FOR_DELIVERY": "Жолда / В доставке",
    "DELIVERED": "Жеткізілді / Доставлен", "CANCELLED": "Бас тартылды / Отменён",
}


@app.get("/api/admin/reports/export.xlsx")
def export_reports_xlsx(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    stmt = select(Order).order_by(Order.id)
    start = _parse_report_date(date_from)
    end = _parse_report_date(date_to, end=True)
    if start:
        stmt = stmt.where(Order.created_at >= start)
    if end:
        stmt = stmt.where(Order.created_at < end)
    orders = db.scalars(stmt).all()

    def kz(dt):
        local = to_kz(dt)
        return local.strftime("%d.%m.%Y %H:%M") if local else ""

    order_rows = [["№ тапсырыс", "Күні (KZ)", "Түрі", "Пойыз", "Вагон", "Орын", "Купе", "Жолаушы", "Телефон",
                   "Күйі", "Тағамдар", "Қосымша ақы 10%", "Жиыны ₸", "Қабылдау→дайын (мин)", "Бағасы (1-5)", "Пікір", "Бас тартты", "Себебі"]]
    item_rows = [["№ тапсырыс", "Күні (KZ)", "Күйі", "Тағам", "Нұсқа", "Саны", "Бағасы ₸", "Сомасы ₸"]]
    dish_stats: dict[str, list[float]] = {}
    delivered_total = 0.0
    delivered_cnt = cancelled_cnt = 0
    ratings = []
    for o in orders:
        prep = ""
        if o.accepted_at and o.ready_at:
            prep = round((o.ready_at - o.accepted_at).total_seconds() / 60.0, 1)
        order_rows.append([
            o.order_number, kz(o.created_at), "Алдын ала (ланчбокс)" if o.order_type == "PREORDER" else "Пойызда",
            o.train_no, o.wagon_no, o.seat_no, o.compartment_no, o.passenger_name, o.phone,
            STATUS_LABELS.get(o.status.value, o.status.value),
            "; ".join(f"{i.item_name_snapshot} ×{i.quantity}" for i in o.items),
            float(o.service_charge), float(o.total), prep, o.rating, o.rating_comment or "",
            {"passenger": "Жолаушы", "kitchen": "Аспаз/админ"}.get(o.cancelled_by, ""), o.cancel_reason or "",
        ])
        for i in o.items:
            item_rows.append([o.order_number, kz(o.created_at), STATUS_LABELS.get(o.status.value, o.status.value),
                              i.item_name_snapshot, i.variant_snapshot, i.quantity, float(i.price_snapshot), float(i.line_total)])
            if o.status == OrderStatus.DELIVERED:
                st = dish_stats.setdefault(i.item_name_snapshot, [0, 0.0])
                st[0] += i.quantity
                st[1] += float(i.line_total)
        if o.status == OrderStatus.DELIVERED:
            delivered_total += float(o.total)
            delivered_cnt += 1
        elif o.status == OrderStatus.CANCELLED:
            cancelled_cnt += 1
        if o.rating is not None:
            ratings.append(o.rating)

    dish_rows = [["Тағам", "Сатылған саны (жеткізілген)", "Сомасы ₸"]] + [
        [name, int(v[0]), round(v[1], 2)] for name, v in sorted(dish_stats.items(), key=lambda kv: -kv[1][0])
    ]
    period = f"{date_from or 'басынан'} — {date_to or 'бүгінге дейін'}"
    summary_rows = [
        ["Көрсеткіш", "Мәні"],
        ["Кезең", period],
        ["Барлық тапсырыс", len(orders)],
        ["Жеткізілген", delivered_cnt],
        ["Бас тартылған", cancelled_cnt],
        ["Түсім (жеткізілген, 10% қоса) ₸", round(delivered_total, 2)],
        ["Орташа чек ₸", round(delivered_total / delivered_cnt, 2) if delivered_cnt else 0],
        ["Орташа баға (1-5)", round(sum(ratings) / len(ratings), 2) if ratings else "—"],
        ["Баға қойғандар саны", len(ratings)],
    ]
    data = build_xlsx([("Қорытынды", summary_rows), ("Тапсырыстар", order_rows), ("Позициялар", item_rows), ("Тағамдар рейтингі", dish_rows)])
    fname = f"dar_res_report_{datetime.now(KZ_TZ).strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/admin/reports")
def get_admin_reports_api(
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    return get_operations_kpis(db)


class OrderingModeIn(BaseModel):
    mode: str  # "OPEN" or "CLOSED"


@app.post("/api/admin/settings/ordering-mode")
async def set_ordering_mode(
    payload: OrderingModeIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    mode = payload.mode.upper()
    if mode not in ("OPEN", "CLOSED"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    setting = db.scalar(select(SystemSetting).where(SystemSetting.key == "ordering_mode"))
    if not setting:
        setting = SystemSetting(key="ordering_mode", value=mode)
        db.add(setting)
    else:
        setting.value = mode
    db.commit()

    await hub.broadcast("ordering_mode_update", {"ordering_mode": mode})
    return {"success": True, "ordering_mode": mode}


class ItemPriceUpdateIn(BaseModel):
    price: float


@app.patch("/api/admin/menu-items/{item_id}/price")
async def update_item_price(
    item_id: int,
    payload: ItemPriceUpdateIn,
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    old_price = Decimal(str(item.price))
    new_price = _price_or_400(payload.price)
    item.price = new_price

    # Ланчбокс бағасы алғаш қойылғанда (0 -> >0) ол автоматты түрде қолжетімді болады
    just_enabled = False
    if (item.sku or "").startswith("LB-") and old_price <= 0 < new_price and not item.is_available:
        item.is_available = True
        just_enabled = True

    db.commit()
    await hub.broadcast("menu_updated", {"item_id": item.id})
    return {
        "success": True,
        "item_id": item.id,
        "new_price": float(item.price),
        "is_available": item.is_available,
        "lunchbox_enabled": just_enabled,
    }

