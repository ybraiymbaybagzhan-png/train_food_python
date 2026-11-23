import hashlib
import hmac
import os
import secrets
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from .database import engine, SessionLocal, Base
from .models import (
    Carriage,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    QRCodeContext,
    SystemSetting,
    Train,
    User,
    UserRole,
)


def hash_password(password: str, salt: Optional[str] = None, iterations: int = 600000) -> str:
    """PBKDF2 HMAC SHA-256 secure password hashing with per-user salt and 600,000 iterations."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2${iterations}${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password using hmac.compare_digest.
    Supports new pbkdf2$iterations$salt$hash format as well as legacy dar_res_salt_2026 100k format.
    """
    if not hashed_password:
        return False
    if hashed_password.startswith("pbkdf2$"):
        parts = hashed_password.split("$")
        if len(parts) == 4:
            _, iter_str, salt, expected_hash = parts
            try:
                iterations = int(iter_str)
                dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
                return hmac.compare_digest(dk.hex(), expected_hash)
            except Exception:
                return False
    # Fallback for legacy format
    legacy_dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), b"dar_res_salt_2026", 100000)
    return hmac.compare_digest(legacy_dk.hex(), hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Returns True if the stored hash is legacy or not using 600k iterations."""
    if not hashed_password or not hashed_password.startswith("pbkdf2$"):
        return True
    parts = hashed_password.split("$")
    if len(parts) != 4 or int(parts[1]) < 600000:
        return True
    return False


MENU_CATEGORIES = [
    {"code": "breakfast", "name_ru": "Завтраки", "name_kz": "Таңғы ас", "name_en": "Breakfast", "sort": 1},
    {"code": "appetizers", "name_ru": "Холодные закуски", "name_kz": "Салқын тағамдар", "name_en": "Appetizers", "sort": 2},
    {"code": "first-courses", "name_ru": "Первые блюда", "name_kz": "Бірінші тамақ", "name_en": "First Courses / Soups", "sort": 3},
    {"code": "salads", "name_ru": "Салаты", "name_kz": "Салаттар", "name_en": "Salads", "sort": 4},
    {"code": "main-courses", "name_ru": "Вторые блюда", "name_kz": "Негізгі тағамдар", "name_en": "Second Courses / Main Courses", "sort": 5},
    {"code": "side-dishes", "name_ru": "Гарниры", "name_kz": "Гарнирлер", "name_en": "Garnishes / Side Dishes", "sort": 6},
    {"code": "hot-drinks", "name_ru": "Горячие напитки", "name_kz": "Ыстық сусындар", "name_en": "Hot Drinks", "sort": 7},
    {"code": "for-tea", "name_ru": "К чаю", "name_kz": "Шайға", "name_en": "For Tea", "sort": 8},
    {"code": "bakery", "name_ru": "Выпечка", "name_kz": "Нан өнімдері", "name_en": "Bakery Products", "sort": 9},
    {"code": "drinks", "name_ru": "Напитки", "name_kz": "Сусындар", "name_en": "Soft Drinks", "sort": 10},
    {"code": "beer", "name_ru": "Пиво", "name_kz": "Сыра", "name_en": "Beer", "sort": 11},
    {"code": "beer-snacks", "name_ru": "К пиву", "name_kz": "Сыраға", "name_en": "Beer Snacks", "sort": 12},
    {"code": "vodka", "name_ru": "Водка", "name_kz": "Арақ", "name_en": "Vodka", "sort": 13},
    {"code": "spirits", "name_ru": "Коньяк / Вино / Виски", "name_kz": "Коньяк / Шарап / Виски", "name_en": "Cognac / Wine / Whisky", "sort": 14},
    {"code": "lunchboxes", "name_ru": "Ланчбоксы", "name_kz": "Ланчбокстар", "name_en": "Lunchboxes", "sort": 15},
]


def ensure_schema_columns():
    """Бар дерекқорға жаңа бағандарды қосады (create_all бар кестені өзгертпейді).

    SQLite және PostgreSQL екеуінде де жұмыс істейді.
    """
    wanted = {
        "trains": [
            ("cook_name", "VARCHAR(120) DEFAULT ''"),
            ("whatsapp_phone", "VARCHAR(32) DEFAULT ''"),
        ],
        "orders": [
            ("order_type", "VARCHAR(16) DEFAULT 'ONBOARD'"),
            ("departure_at", "DATETIME"),
        ],
    }
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, columns in wanted.items():
            if table not in existing_tables:
                continue
            have = {c["name"] for c in insp.get_columns(table)}
            for col_name, col_ddl in columns:
                if col_name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_ddl}"))


def upgrade_and_seed():
    Base.metadata.create_all(bind=engine)
    ensure_schema_columns()

    with SessionLocal() as db:
        # 1. System Settings
        for key, val in [("ordering_mode", "OPEN"), ("service_charge_rate", "0.10"), ("brand_name", "DAR | RES group"), ("whatsapp_default_phone", "77772141601"), ("lunchbox_min_advance_hours", "24")]:
            existing = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
            if not existing:
                db.add(SystemSetting(key=key, value=val))

        # 2. Staff & Admin Accounts (seeded from env vars if provided)
        admin_pwd = os.getenv("ADMIN_PASSWORD", "admin2026")
        kitchen_pwd = os.getenv("KITCHEN_PASSWORD", "kitchen2026")
        staff_pwd = os.getenv("STAFF_PASSWORD", "staff2026")

        users_seed = [
            ("admin", admin_pwd, UserRole.ADMIN, "Бас Әкімші / Главный Администратор"),
            ("kitchen", kitchen_pwd, UserRole.KITCHEN, "Асхана Аспазы / Шеф-повар поезда"),
            ("staff", staff_pwd, UserRole.DELIVERY_STAFF, "Жолсерік / Проводник-курьер"),
        ]
        for uname, pwd, role, fname in users_seed:
            u = db.scalar(select(User).where(User.username == uname))
            if not u:
                db.add(User(username=uname, password_hash=hash_password(pwd), role=role, full_name=fname, is_active=True))
            elif needs_rehash(u.password_hash) and verify_password(pwd, u.password_hash):
                u.password_hash = hash_password(pwd)
                db.add(u)

        # 3. Trains & Carriages
        trains_seed = [
            ("071", "Астана → Алматы-2", [("1", "Купе"), ("2", "Купе"), ("3", "Плацкарт"), ("4", "Плацкарт"), ("5", "СВ"), ("6", "Вагон-ресторан")]),
            ("015", "Алматы-2 → Петропавловск", [("1", "Купе"), ("2", "Купе"), ("3", "Плацкарт"), ("4", "Плацкарт"), ("5", "Купе")]),
        ]
        for tno, rname, cars in trains_seed:
            train = db.scalar(select(Train).where(Train.train_number == tno))
            if not train:
                train = Train(train_number=tno, route_name=rname, is_active=True)
                db.add(train)
                db.flush()
                for cno, ctype in cars:
                    token = uuid.uuid4().hex[:12]
                    c = Carriage(train_id=train.id, carriage_number=cno, carriage_type=ctype, qr_token=token, delivery_enabled=True, is_active=True)
                    db.add(c)
                    db.flush()
                    db.add(QRCodeContext(public_token=token, train_number=tno, carriage_number=cno, is_active=True))

        # 4. Categories
        cat_map = {}
        for c in MENU_CATEGORIES:
            existing_cat = db.scalar(select(MenuCategory).where(MenuCategory.code == c["code"]))
            if not existing_cat:
                existing_cat = MenuCategory(code=c["code"], name_ru=c["name_ru"], name_kz=c["name_kz"], name_en=c["name_en"], sort_order=c["sort"], is_active=True)
                db.add(existing_cat)
                db.flush()
            cat_map[c["code"]] = existing_cat.id

        # 4.1. Lunchboxes in DB (single source of truth; default price 3500 KZT; admin can change it later)
        lb_category_id = cat_map.get("lunchboxes")
        if lb_category_id:
            lb_defs = [
                {
                    "sku": "LB-01",
                    "name_ru": "Ланчбокс №1",
                    "name_kz": "Ланчбокс №1",
                    "name_en": "Lunchbox #1",
                    "desc_ru": "Сбалансированный сытный обед с тушеной говядиной, пикантной морковью по-корейски, свежей выпечкой и мини-пирожным.",
                    "desc_kz": "Бұқтырылған сиыр еті, корейше сәбіз салаты, балғын тоқаш пен шағын тортшадан тұратын дәмді әрі теңгерімді тойымды жиынтық.",
                    "desc_en": "Balanced hearty lunchbox featuring braised beef with vegetables and rice, Korean-style carrot salad, pastry, and mini cake.",
                    "ingredients_ru": "Говядина тушеная с овощами с рисом (200г), Морковь по-корейски (100г), Выпечка (30г), Мини-пирожное (60г)",
                    "ingredients_kz": "Күріш қосылған көкөністі бұқтырылған сиыр еті (200г), Корейше сәбіз салаты (100г), Тоқаш (30г), Шағын тортша (60г)",
                    "ingredients_en": "Braised beef with vegetables and rice (200g), Korean-style carrot salad (100g), Pastry (30g), Mini cake (60g)",
                    "weight": "390 g",
                    "price": Decimal("3500.00"),
                    "is_available": True,
                },
                {
                    "sku": "LB-02",
                    "name_ru": "Ланчбокс №2",
                    "name_kz": "Ланчбокс №2",
                    "name_en": "Lunchbox #2",
                    "desc_ru": "Ароматное чахохбили из нежного куриного мяса с рисом, хрустящий свежий салат, аппетитная выпечка и сладкий десерт.",
                    "desc_kz": "Күріш қосылған тауық етінен чахохбили, балғын салат, тіл үйірер тоқаш пен шағын тортша қосылған теңгерімді ланчбокс.",
                    "desc_en": "Flavorful chicken chakhokhbili with rice, fresh garden salad, soft pastry, and a mini cake.",
                    "ingredients_ru": "Чахохбили из курицы с рисом (200г), Свежий салат (100г), Выпечка (30г), Мини-пирожное (60г)",
                    "ingredients_kz": "Күріш қосылған тауық етінен чахохбили (200г), Балғын салат (100г), Тоқаш (30г), Шағын тортша (60г)",
                    "ingredients_en": "Chicken chakhokhbili with rice (200g), Fresh salad (100g), Pastry (30g), Mini cake (60g)",
                    "weight": "390 g",
                    "price": Decimal("3500.00"),
                    "is_available": True,
                },
                {
                    "sku": "LB-03",
                    "name_ru": "Ланчбокс №3",
                    "name_kz": "Ланчбокс №3",
                    "name_en": "Lunchbox #3",
                    "desc_ru": "Классические макароны по-флотски с мясным фаршем, легкий салат из свежей капусты с огурцом, домашняя выпечка и мини-пирожное.",
                    "desc_kz": "Классикалық флотша макарон, қырыққабат пен қиярдан жасалған жеңіл салат, дәмді тоқаш және нәзік шағын тортшадан тұратын теңгерімді ланчбокс.",
                    "desc_en": "Classic navy-style pasta with minced meat, fresh cabbage and cucumber salad, homemade pastry, and a mini cake.",
                    "ingredients_ru": "Макароны по-флотски (200г), Салат из капусты с огурцом (100г), Выпечка (30г), Мини-пирожное (60г)",
                    "ingredients_kz": "Флотша макарон (200г), Қырыққабат пен қияр салаты (100г), Тоқаш (30г), Шағын тортша (60г)",
                    "ingredients_en": "Navy-style pasta (200g), Cabbage and cucumber salad (100g), Pastry (30g), Mini cake (60g)",
                    "weight": "390 g",
                    "price": Decimal("3500.00"),
                    "is_available": True,
                },
            ]
            for lb_def in lb_defs:
                mi = db.scalar(select(MenuItem).where(MenuItem.sku == lb_def["sku"]))
                if not mi:
                    db.add(MenuItem(
                        category_id=lb_category_id,
                        sku=lb_def["sku"],
                        name_ru=lb_def["name_ru"],
                        name_kz=lb_def["name_kz"],
                        name_en=lb_def["name_en"],
                        description_ru=lb_def["desc_ru"],
                        description_kz=lb_def["desc_kz"],
                        description_en=lb_def["desc_en"],
                        ingredients_ru=lb_def["ingredients_ru"],
                        ingredients_kz=lb_def["ingredients_kz"],
                        ingredients_en=lb_def["ingredients_en"],
                        weight_value=lb_def["weight"],
                        price=lb_def["price"],
                        is_available=lb_def["is_available"],
                        is_active=True,
                        is_popular=False,
                        image_url="",
                    ))
                else:
                    # Update names/descriptions/ingredients in case they were updated
                    mi.category_id = lb_category_id
                    mi.name_ru = lb_def["name_ru"]
                    mi.name_kz = lb_def["name_kz"]
                    mi.name_en = lb_def["name_en"]
                    mi.description_ru = lb_def["desc_ru"]
                    mi.description_kz = lb_def["desc_kz"]
                    mi.description_en = lb_def["desc_en"]
                    mi.ingredients_ru = lb_def["ingredients_ru"]
                    mi.ingredients_kz = lb_def["ingredients_kz"]
                    mi.ingredients_en = lb_def["ingredients_en"]
                    mi.weight_value = lb_def["weight"]
                    # Баға әлі қойылмаған (0) болса ғана әдепкі бағаны береміз; админ қойған баға сақталады
                    if not mi.price or float(mi.price) <= 0:
                        mi.price = lb_def["price"]
                        mi.is_available = lb_def["is_available"]
                    db.add(mi)
            db.flush()


        # 5. Full 100% Seed Menu Items from PDF
        if db.scalar(select(MenuItem).limit(1)) is None:
            items_to_seed = [
                # --- BREAKFAST ---
                {
                    "cat": "breakfast", "sku": "BF-01", "name_ru": "Каша рисовая", "name_kz": "Күріш ботқасы", "name_en": "Rice porridge", "desc_ru": "Традиционная нежная рисовая каша на молоке со сливочным маслом.", "desc_kz": "Сүт пен сары май қосылып пісірілген дәстүрлі дәмді күріш ботқасы.", "desc_en": "Traditional tender rice porridge cooked with fresh milk and butter.",
                    "weight": "250 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bf-01.jpg"
                },
                {
                    "cat": "breakfast", "sku": "BF-02", "name_ru": "Каша пшенная", "name_kz": "Тары ботқасы", "name_en": "Millet porridge", "desc_ru": "Ароматная рассыпчатая пшенная каша на молоке со сливочным маслом.", "desc_kz": "Сүт пен сары май қосылған хош иісті, үлпілдек тары ботқасы.", "desc_en": "Fragrant wholesome millet porridge cooked with milk and butter.",
                    "weight": "250 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bf-02.jpg"
                },
                {
                    "cat": "breakfast", "sku": "BF-03", "name_ru": "Каша овсяная", "name_kz": "Сұлы жармасы", "name_en": "Oatmeal porridge", "desc_ru": "Полезная классическая овсяная каша на молоке для сытного утра в пути.", "desc_kz": "Жолдағы таңертеңгі пайдалы әрі тойымды сүтке пісірілген сұлы ботқасы.", "desc_en": "Nutritious classic rolled oats cooked with milk for a healthy train breakfast.",
                    "weight": "250 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bf-03.jpg"
                },
                {
                    "cat": "breakfast", "sku": "BF-04", "name_ru": "Яичница", "name_kz": "Қуырылған жұмыртқа", "name_en": "Fried sunny-side eggs", "desc_ru": "Классическая яичница-глазунья из свежих яиц, обжаренная до золотистого края.", "desc_kz": "Балғын жұмыртқалардан қуырылған классикалық көзді жұмыртқа.", "desc_en": "Classic sunny-side up fried farm eggs with golden yolks.",
                    "weight": "150 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bf-04.jpg"
                },
                {
                    "cat": "breakfast", "sku": "BF-05", "name_ru": "Яичница с сосиской или колбасой", "name_kz": "Шұжық қосылған жұмыртқа", "name_en": "Fried eggs with sausage", "desc_ru": "Сытная горячая яичница с обжаренными сочными сосисками или колбасой.", "desc_kz": "Қызартып қуырылған дәмді шұжықпен дайындалған тойымды жұмыртқа.", "desc_en": "Hearty pan-fried eggs served with browned savory sausage.",
                    "weight": "180 g", "price": 1300, "is_popular": True, "img": "/static/assets/menu/bf-05.jpg"
                },
                {
                    "cat": "breakfast", "sku": "BF-06", "name_ru": "Блины (порция 3 шт.)", "name_kz": "Құймақ (3 дана)", "name_en": "Pancakes (3 pcs)", "desc_ru": "Домашние кружевные блинчики со сливочным маслом или джемом.", "desc_kz": "Сары май немесе балғын джеммен ұсынылатын үйдегідей жұмсақ құймақтар.", "desc_en": "Three golden homestyle crepe pancakes served warm with butter or jam.",
                    "weight": "150 g", "price": 900, "is_popular": True, "img": "/static/assets/menu/bf-06.jpg"
                },
                {
                    "cat": "breakfast", "sku": "BF-07", "name_ru": "Вареное яйцо (1 шт.)", "name_kz": "Піскен жұмыртқа (1 дана)", "name_en": "Boiled egg (1 pc)", "desc_ru": "Свежесваренное яйцо к сытному дорожному завтраку.", "desc_kz": "Сапардағы таңғы асқа арналған жаңа пісірілген жұмыртқа.", "desc_en": "Fresh boiled farm egg served warm as a breakfast classic.",
                    "weight": "60 g", "price": 300, "is_popular": False, "img": "/static/assets/menu/bf-07.jpg"
                },

                # --- APPETIZERS ---
                {
                    "cat": "appetizers", "sku": "APP-01", "name_ru": "Кавказская закуска", "name_kz": "Кавказ закускасы", "name_en": "Caucasian snack platter", "desc_ru": "Свежие спелые помидоры, хрустящие огурцы, маслины, нежная брынза и зелень.", "desc_kz": "Балғын қызанақтар, қытырлақ қиярлар, зәйтүн, нәзік брынза ірімшігі мен аскөк.", "desc_en": "Ripe tomatoes, crunchy cucumbers, olives, rich brynza cheese, and fresh garden herbs.",
                    "ingredients_ru": "огурцы, помидоры, оливки, брынза, зелень",
                    "ingredients_kz": "қияр, қызанақ, зәйтүн, брынза, аскөк",
                    "ingredients_en": "cucumbers, tomatoes, olives, brynza cheese, greens",
                    "weight": "300 g", "price": 2100, "is_popular": False, "img": "/static/assets/menu/app-01.jpg"
                },
                {
                    "cat": "appetizers", "sku": "APP-02", "name_ru": "Домашние разносолы", "name_kz": "Маринадталған көкөністер", "name_en": "Homemade pickled vegetables", "desc_ru": "Ассорти из хрустящих соленых огурчиков, маринованных черри и квашеной капусты.", "desc_kz": "Қытырлақ тұздалған қиярлар, маринадталған черри және ашытылған қырыққабат ассортиі.", "desc_en": "Crispy barrel pickles, marinated cherry tomatoes, and seasoned sauerkraut.",
                    "weight": "250 g", "price": 2000, "is_popular": False, "img": "/static/assets/menu/app-02.jpg"
                },
                {
                    "cat": "appetizers", "sku": "APP-03", "name_ru": "Мясное ассорти", "name_kz": "Ассорти ет (қазы мен ет тілімі)", "name_en": "Assorted gourmet meat platter", "desc_ru": "Изысканная нарезка из традиционного казы, сыровяленого мяса и деликатесных колбас.", "desc_kz": "Дәстүрлі жылқы еті қазысы, қақталған сиыр еті және таңдаулы шұжық тілімдері.", "desc_en": "Fine selection of traditional kazy, cured beef, and cold sliced meats.",
                    "weight": "300 g", "price": 3800, "is_popular": True, "img": "/static/assets/menu/app-03.jpg"
                },

                # --- FIRST COURSES / SOUPS ---
                {
                    "cat": "first-courses", "sku": "FC-01", "name_ru": "Суп с мясом (Сорпа)", "name_kz": "Сорпа (етпен)", "name_en": "Traditional beef soup (Sorpa)", "desc_ru": "Наваристый прозрачный бульон из отборной говядины с овощами и душистой зеленью.", "desc_kz": "Таңдаулы сиыр етінен баяу қайнатылған хош иісті, құнарлы мөлдір сорпа.", "desc_en": "Rich, slow-simmered beef broth with tender meat cuts and herbs.",
                    "weight": "350 g", "price": 2200, "is_popular": True, "img": "/static/assets/menu/fc-01.jpg"
                },
                {
                    "cat": "first-courses", "sku": "FC-02", "name_ru": "Лагман по-домашнему", "name_kz": "Сұйық үй лағманы", "name_en": "Homestyle liquid lagman", "desc_ru": "Тянутая вручную лапша в ароматном бульоне с кусочками говядины и сладким перцем.", "desc_kz": "Қолдан созылған ұзын кеспе, сиыр еті мен көкөністер қосылған шырынды лағман.", "desc_en": "Hand-pulled noodles served in rich broth with beef chunks, bell peppers, and spices.",
                    "weight": "400 g", "price": 2500, "is_popular": True, "img": "/static/assets/menu/fc-02.jpg"
                },
                {
                    "cat": "first-courses", "sku": "FC-03", "name_ru": "Борщ со сметаной", "name_kz": "Дәстүрлі борщ сорпасы", "name_en": "Classic Borsch with sour cream", "desc_ru": "Классический наваристый борщ на мясном бульоне с сочной свеклой и ложкой сметаны.", "desc_kz": "Қызылша, қырыққабат пен жұмсақ еттен дайындалған, қаймақпен ұсынылатын классикалық борщ.", "desc_en": "Rich beetroot soup cooked on savory meat broth, served with fresh sour cream.",
                    "weight": "350 g", "price": 2000, "is_popular": True, "img": "/static/assets/menu/fc-03.jpg"
                },
                {
                    "cat": "first-courses", "sku": "FC-04", "name_ru": "Лапша по-домашнему (Кеспе)", "name_kz": "Үй кеспесі", "name_en": "Homemade chicken noodle soup", "desc_ru": "Легкий золотистый бульон с нежной курицей и домашней тонко нарезанной лапшой.", "desc_kz": "Тауық етінің алтын түстес сорпасында дайындалған жұмсақ үй кеспесі.", "desc_en": "Tender chicken and thin hand-cut noodles in golden savory broth.",
                    "weight": "350 g", "price": 2000, "is_popular": False, "img": "/static/assets/menu/fc-04.jpg"
                },
                {
                    "cat": "first-courses", "sku": "FC-05", "name_ru": "Пельмени с бульоном", "name_kz": "Тұшпара сорпасымен", "name_en": "Dumplings in broth", "desc_ru": "Горячие мясные пельмени ручной лепки в согревающем наваристом бульоне с зеленью.", "desc_kz": "Қолдан түйілген дәмді ет тұшпарасы, хош иісті сорпа және жаңа аскөкпен.", "desc_en": "Handcrafted minced meat dumplings served in steaming seasoned broth.",
                    "weight": "350 g", "price": 2200, "is_popular": True, "img": "/static/assets/menu/fc-05.jpg"
                },
                {
                    "cat": "first-courses", "sku": "FC-06", "name_ru": "Рассольник", "name_kz": "Рассольник сорпасы", "name_en": "Rassolnik barley soup", "desc_ru": "Ароматный традиционный суп с перловой крупой, солеными огурчиками и нежным мясом.", "desc_kz": "Арпа жармасы, тұздалған қияр мен сиыр етінен әзірленген дәстүрлі дәмді сорпа.", "desc_en": "Traditional hearty soup with pearl barley, pickles, and tender beef.",
                    "weight": "350 g", "price": 2000, "is_popular": False, "img": "/static/assets/menu/fc-06.jpg"
                },
                {
                    "cat": "first-courses", "sku": "FC-07", "name_ru": "Солянка мясная", "name_kz": "Құрама ет солянкасы", "name_en": "Meat Solyanka soup", "desc_ru": "Густой пряный суп из нескольких сортов копченостей, маслин, каперсов и дольки лимона.", "desc_kz": "Қақталған түрлі еттер, зәйтүн және лимон қосылған қышқылтым-ащы қою сорпа.", "desc_en": "Rich, spicy-sour soup featuring assorted smoked meats, olives, and fresh lemon.",
                    "weight": "350 g", "price": 2200, "is_popular": True, "img": "/static/assets/menu/fc-07.jpg"
                },

                # --- SALADS ---
                {
                    "cat": "salads", "sku": "SL-01", "name_ru": "Цезарь с курицей", "name_kz": "Тауық еті қосылған цезарь салаты", "name_en": "Chicken Caesar salad", "desc_ru": "Хрустящие листья романо, сочное куриное филе, томаты черри, пармезан и соус цезарь.", "desc_kz": "Қытырлақ айсберг жапырақтары, нәзік тауық еті, черри қызанақтары және пармезан.", "desc_en": "Crisp romaine, grilled chicken breast, cherry tomatoes, shaved parmesan, and croutons.",
                    "ingredients_ru": "куриное филе, салат айсберг, сухарики, перепелиное яйцо, черри, соус цезарь",
                    "ingredients_kz": "тауық еті, айсберг, сухари, бөдене жұмыртқасы, черри, соус",
                    "ingredients_en": "chicken fillet, iceberg lettuce, croutons, quail egg, cherry tomatoes, Caesar sauce",
                    "weight": "200 g", "price": 2200, "is_popular": True, "img": "/static/assets/menu/sl-01.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-02", "name_ru": "Оливье классический", "name_kz": "Оливье дәстүрлі салаты", "name_en": "Classic Olivier salad", "desc_ru": "Любимый праздничный салат из отварного картофеля, моркови, зеленого горошка и соуса.", "desc_kz": "Пісірілген картоп, сәбіз, жасыл бұршақ және шұжық қосылған классикалық салат.", "desc_en": "Traditional recipe with diced potatoes, tender carrots, peas, and creamy dressing.",
                    "ingredients_ru": "колбаса, картофель, морковь, яйца, марин. огурцы, горох, майонез",
                    "weight": "250 g", "price": 2200, "is_popular": False, "img": "/static/assets/menu/sl-02.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-03", "name_ru": "Свежий овощной салат", "name_kz": "Балғын көкөніс салаты", "name_en": "Fresh garden salad", "desc_ru": "Летний хрустящий салат из сладких помидоров, огурцов, репчатого лука и зелени.", "desc_kz": "Балғын қызанақ, қияр, пияз және жаңа үзілген аскөк қосылған дәруменді салат.", "desc_en": "Crisp cucumbers, sweet ripe tomatoes, red onions, and fresh parsley dressing.",
                    "ingredients_ru": "помидоры, огурцы, зелень",
                    "weight": "200 g", "price": 1700, "is_popular": False, "img": "/static/assets/menu/sl-03.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-04", "name_ru": "Греческий салат", "name_kz": "Грек салаты", "name_en": "Authentic Greek salad", "desc_ru": "Крупно нарезанные сочные овощи с кубиками соленой брынзы, маслинами и орегано.", "desc_kz": "Балғын көкөністер, майлы брынза ірімшігі, зәйтүн және зәйтүн майы.", "desc_en": "Crisp cucumbers, sweet peppers, tomatoes, black olives, and rich feta cheese.",
                    "ingredients_ru": "помидоры, огурцы, брынза, оливки",
                    "weight": "250 g", "price": 2200, "is_popular": False, "img": "/static/assets/menu/sl-04.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-05", "name_ru": "Морковь по-корейски", "name_kz": "Корейше сәбіз салаты", "name_en": "Spicy Korean-style carrots", "desc_ru": "Пикантная тонко натертая морковь с чесноком, кориандром и пряным маслом.", "desc_kz": "Дәмдеуіштер, сарымсақ және хош иісті маймен дайындалған ащылау сәбіз салаты.", "desc_en": "Julienned fresh carrots marinated with aromatic coriander, garlic, and hot oil.",
                    "ingredients_ru": "морковь, специи",
                    "weight": "250 g", "price": 1000, "is_popular": False, "img": "/static/assets/menu/sl-05.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-06", "name_ru": "Пекинский салат", "name_kz": "Пекин салаты", "name_en": "Beijing beef salad", "desc_ru": "Хрустящая пекинская капуста, нежная говядина, сладкий перец и кунжутная заправка.", "desc_kz": "Қытырлақ пекин қырыққабаты, сиыр еті, тәтті бұрыш және күнжіт майы тұздығы.", "desc_en": "Crispy napa cabbage, sauteed beef strips, bell peppers, and sesame dressing.",
                    "ingredients_ru": "говядина, морковь, соевый соус, лук, полугорький перец, болгарский перец",
                    "weight": "180 g", "price": 2200, "is_popular": True, "img": "/static/assets/menu/sl-06.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-07", "name_ru": "Малибу фирменный салат", "name_kz": "Малибу фирмалық салаты", "name_en": "Malibu signature salad", "desc_ru": "Копченая курочка, сладкая кукуруза, твердый сыр, свежие огурцы и сухарики.", "desc_kz": "Қақталған тауық еті, тәтті жүгері, қатты ірімшік, қияр және қытырлақ сухарилер.", "desc_en": "Smoked chicken breast, sweet corn, melted cheese notes, cucumber, and crisp croutons.",
                    "ingredients_ru": "сыр, огурцы, помидоры, сухарики, майонез",
                    "weight": "250 g", "price": 2200, "is_popular": False, "img": "/static/assets/menu/sl-07.jpg"
                },
                {
                    "cat": "salads", "sku": "SL-08", "name_ru": "Ачичук салат", "name_kz": "Ащышық қызанақ салаты", "name_en": "Achichuk tomato salad", "desc_ru": "Тончайше нарезанные спелые сладкие томаты со сладким фиолетовым луком и базиликом.", "desc_kz": "Жұқалап туралған балғын қызанақтар, қызыл пияз және райхан қосылған дәстүрлі салат.", "desc_en": "Paper-thin sweet vine tomatoes, purple onions, and herbs, perfect for pilaf.",
                    "ingredients_ru": "помидоры, лук, острый перец",
                    "weight": "200 g", "price": 1500, "is_popular": False, "img": "/static/assets/menu/sl-08.jpg"
                },

                # --- SECOND COURSES / MAIN COURSES ---
                {
                    "cat": "main-courses", "sku": "MC-01", "name_ru": "Бифштекс с яйцом", "name_kz": "Жұмыртқа қосылған бифштекс", "name_en": "Beefsteak with fried egg", "desc_ru": "Сочный бифштекс из рубленой говядины, увенчанный аппетитным жареным яйцом.", "desc_kz": "Таңдаулы сиыр етінен пісірілген шырынды бифштекс және үстіндегі көзді жұмыртқа.", "desc_en": "Juicy minced beef patty grilled to perfection and topped with a sunny fried egg.",
                    "weight": "170 g", "price": 2200, "is_popular": True, "img": "/static/assets/menu/mc-01.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-02", "name_ru": "Котлеты домашние", "name_kz": "Үйдегідей сиыр еті котлеттері", "name_en": "Homestyle beef cutlets", "desc_ru": "Золотистые сочные котлеты из отборной говядины по проверенному домашнему рецепту.", "desc_kz": "Құнарлы сиыр етінен қуырылған, шырынды әрі жұмсақ үй котлеттері.", "desc_en": "Golden pan-seared ground beef cutlets made with fresh onion and herbs.",
                    "weight": "140 g", "price": 2000, "is_popular": False, "img": "/static/assets/menu/mc-02.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-03", "name_ru": "Куырдак по-казахски", "name_kz": "Дәстүрлі қазақша қуырдақ", "name_en": "Traditional Kazakh Kuyrdak", "desc_ru": "Традиционное сытное жаркое из нежного мяса с картофелем, луком и специями.", "desc_kz": "Ет, картоп және пиязбен қазанда шыжғырылып қуырылған дәстүрлі қазақ тағамы.", "desc_en": "Tender meat braised in a skillet with golden potatoes, sweet onions, and spices.",
                    "weight": "250 g", "price": 3500, "is_popular": True, "img": "/static/assets/menu/mc-03.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-04", "name_ru": "Плов праздничный", "name_kz": "Мерекелік палау", "name_en": "Festive meat pilaf (Plov)", "desc_ru": "Ароматный восточный плов с отборным мясом, сладкой желтой морковью и барбарисом.", "desc_kz": "Таңдаулы ет, сары сәбіз, зире және мейізбен бұқтырылған хош иісті мерекелік палау.", "desc_en": "Fragrant long-grain rice pilaf simmered with tender meat, yellow carrots, and spices.",
                    "weight": "300 g", "price": 2300, "is_popular": True, "img": "/static/assets/menu/mc-04.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-05", "name_ru": "Чахохбили из курицы", "name_kz": "Тауықтан дайындалған чахохбили", "name_en": "Chicken Chakhohbili stew", "desc_ru": "Ароматное рагу из кусочков курицы, тушенных в густом томатном соусе с чесноком и кинзой.", "desc_kz": "Қызанақ, сарымсақ және күнзе тұздығында бұқтырылған шырынды тауық еті.", "desc_en": "Tender chicken simmered in rich tomato, garlic, and fragrant cilantro sauce.",
                    "weight": "200 g", "price": 2600, "is_popular": False, "img": "/static/assets/menu/mc-05.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-06", "name_ru": "Манты с мясом (паровые)", "name_kz": "Буда піскен етті мәнті", "name_en": "Steamed meat manti", "desc_ru": "Сочные манты ручной лепки с рубленым мясом и луком, приготовленные на пару.", "desc_kz": "Қолдан жайылған қамыр, туралған ет пен пиязбен толтырылған будағы ыстық мәнті.", "desc_en": "Steamed delicate dough pockets generously filled with seasoned minced meat and onions.",
                    "weight": "250 g", "price": 2500, "is_popular": True, "img": "/static/assets/menu/mc-06.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-07", "name_ru": "Мясо по-тайски", "name_kz": "Тай стиліндегі сиыр еті", "name_en": "Thai-style wok beef", "desc_ru": "Нежные полоски говядины, обжаренные в воке со сладким перцем и соусом терияки.", "desc_kz": "Тәтті бұрыш, соя тұздығы және күнжітпен вокта қуырылған жұмсақ сиыр еті.", "desc_en": "Stir-fried beef strips with crisp bell peppers, sweet soy sauce, and scallions.",
                    "weight": "250 g", "price": 3100, "is_popular": True, "img": "/static/assets/menu/mc-07.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-08", "name_ru": "Гуйру лагман", "name_kz": "Гуйру қуырылған лағман", "name_en": "Guiru stir-fried lagman", "desc_ru": "Тянутая вручную лапша с крупно обжаренной говядиной, сельдереем и сочными овощами.", "desc_kz": "Қолмен созылған кеспе, қуырылған сиыр еті және шырынды көкөністер подливімен.", "desc_en": "Hand-pulled noodles topped with wok-seared beef chunks, celery, and peppers.",
                    "weight": "300 g", "price": 2800, "is_popular": True, "img": "/static/assets/menu/mc-08.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-09", "name_ru": "Цомян лагман", "name_kz": "Цомян қуырылған лағман", "name_en": "Tsomyan pan-fried lagman", "desc_ru": "Лапша, обжаренная вместе с мясом и хрустящими овощами в ароматном воке.", "desc_kz": "Ет, бұрыш және дәмдеуіштермен бірге табада қуырылған қытырлақ кеспе лағманы.", "desc_en": "Handmade noodles pan-fried together with tender beef slices and crunchy vegetables.",
                    "weight": "300 g", "price": 2800, "is_popular": True, "img": "/static/assets/menu/mc-09.jpg"
                },
                {
                    "cat": "main-courses", "sku": "MC-10", "name_ru": "Окорочок запеченный", "name_kz": "Пеште пісірілген тауық сирағы", "name_en": "Roasted golden chicken leg", "desc_ru": "Сочный куриный окорочок, запеченный в духовке до хрустящей румяной корочки.", "desc_kz": "Қызарып піскен қытырлақ қабығы бар, пеште дәмделген шырынды тауық еті.", "desc_en": "Oven-roasted chicken quarter with crispy seasoned skin and juicy tender meat.",
                    "weight": "200 g", "price": 2100, "is_popular": False, "img": "/static/assets/menu/mc-10.jpg"
                },

                # --- GARNISHES / SIDE DISHES ---
                {
                    "cat": "side-dishes", "sku": "SD-01", "name_ru": "Картофельное пюре", "name_kz": "Үлпілдек картоп езбесі", "name_en": "Creamy mashed potatoes", "desc_ru": "Воздушное домашнее картофельное пюре со сливочным маслом и молоком.", "desc_kz": "Сүт пен сары май қосылып езілген нәзік, ауызда еритін картоп пюресі.", "desc_en": "Velvety whipped mashed potatoes prepared with fresh cream and butter.",
                    "weight": "150 g", "price": 650, "is_popular": False, "img": "/static/assets/menu/sd-01.jpg"
                },
                {
                    "cat": "side-dishes", "sku": "SD-02", "name_ru": "Картофель фри", "name_kz": "Қытырлақ фри картобы", "name_en": "Crisp French fries", "desc_ru": "Горячие хрустящие золотистые брусочки картофеля с мелкой морской солью.", "desc_kz": "Алтын түске дейін қуырылған қытырлақ әрі ыстық фри картобы.", "desc_en": "Hot golden-fried potato sticks with a crunchy exterior and fluffy interior.",
                    "weight": "150 g", "price": 1500, "is_popular": True, "img": "/static/assets/menu/sd-02.jpg"
                },
                {
                    "cat": "side-dishes", "sku": "SD-03", "name_ru": "Рис отварной", "name_kz": "Буда піскен күріш", "name_en": "Steamed white rice", "desc_ru": "Рассыпчатый длиннозерный белый рис, приготовленный на пару.", "desc_kz": "Буда пісірілген үгілмелі, майдаланбайтын ақ ұзын күріш.", "desc_en": "Fluffy, tender steamed long-grain white rice.",
                    "weight": "150 g", "price": 650, "is_popular": False, "img": "/static/assets/menu/sd-03.jpg"
                },
                {
                    "cat": "side-dishes", "sku": "SD-04", "name_ru": "Гречка отварная", "name_kz": "Қарақұмық ботқасы", "name_en": "Buttered buckwheat", "desc_ru": "Ароматная рассыпчатая гречневая каша со сливочным маслом.", "desc_kz": "Сары май қосылып пісірілген үгілмелі әрі дәмді қарақұмық гарнирі.", "desc_en": "Wholesome, fluffy buckwheat kasha tossed with savory butter.",
                    "weight": "150 g", "price": 650, "is_popular": False, "img": "/static/assets/menu/sd-04.jpg"
                },
                {
                    "cat": "side-dishes", "sku": "SD-05", "name_ru": "Макароны отварные", "name_kz": "Пісірілген макарон", "name_en": "Buttered pasta", "desc_ru": "Классические макароны твердых сортов со сливочным маслом.", "desc_kz": "Сары маймен ұсынылатын классикалық жұмсақ әрі дәмді макарон.", "desc_en": "Al dente durum wheat pasta lightly tossed with melting butter.",
                    "weight": "150 g", "price": 650, "is_popular": False, "img": "/static/assets/menu/sd-05.jpg"
                },

                # --- HOT DRINKS ---
                {
                    "cat": "hot-drinks", "sku": "HD-01", "name_ru": "Чай (черный или зеленый)", "name_kz": "Шай (қара немесе көк)", "name_en": "Tea (black or green cup)", "desc_ru": "Классический листовой горячий чай на выбор: крепкий черный или освежающий зеленый.", "desc_kz": "Сапарда жанға қуат беретін ыстық қара немесе көк шай шынысы.", "desc_en": "Freshly brewed hot black or soothing green tea in a cup.",
                    "volume": "1 чашка", "price": 300, "is_popular": False, "img": "/static/assets/menu/hd-01.jpg"
                },
                {
                    "cat": "hot-drinks", "sku": "HD-02", "name_ru": "Чай с молоком или лимоном", "name_kz": "Сүт қосқан немесе лимонды шай", "name_en": "Tea with milk or lemon", "desc_ru": "Бодрящий чай со свежим молоком по-казахски или с ароматной долькой лимона.", "desc_kz": "Қазақы сүтпен немесе қышқылтым лимон тілімімен ұсынылатын хош иісті шай.", "desc_en": "Hot brewed tea served with rich fresh milk or tangy lemon slice.",
                    "volume": "1 чашка", "price": 400, "is_popular": False, "img": "/static/assets/menu/hd-02.jpg"
                },
                {
                    "cat": "hot-drinks", "sku": "HD-03", "name_ru": "Чайник чая листового", "name_kz": "Шәйнек қара/көк шай", "name_en": "Teapot of freshly brewed tea", "desc_ru": "Большой согревающий чайник свежезаваренного листового чая для долгой беседы в купе.", "desc_kz": "Купедегі жайлы әңгімеге арналған үлкен шәйнекпен ұсынылатын ыстық шай.", "desc_en": "Full teapot of loose-leaf black or green tea for a cozy train journey.",
                    "volume": "Чайник", "price": 900, "is_popular": True, "img": "/static/assets/menu/hd-03.jpg"
                },
                {
                    "cat": "hot-drinks", "sku": "HD-04", "name_ru": "Чайник чая с молоком", "name_kz": "Сүт қосқан шәйнек шай", "name_en": "Teapot of milk tea", "desc_ru": "Традиционный чайник чая с натуральным деревенским молоком по казахским традициям.", "desc_kz": "Дәстүрлі қазақы үлгіде дайындалған мол сүтті ыстық шай шәйнегі.", "desc_en": "Traditional pot of rich black tea brewed with fresh milk.",
                    "volume": "Чайник", "price": 1000, "is_popular": False, "img": "/static/assets/menu/hd-04.jpg"
                },
                {
                    "cat": "hot-drinks", "sku": "HD-05", "name_ru": "Ташкентский чай фирменный", "name_kz": "Ташкент шайы (фирмалық)", "name_en": "Tashkent signature tea", "desc_ru": "Знаменитый чайник зеленого и черного чая со свежей мятой, дольками лимона и наватом.", "desc_kz": "Жалбыз, лимон және нават қосылған әйгілі хош иісті ташкенттік шай шәйнегі.", "desc_en": "Famous blend of black and green tea with fresh mint leaves, lemon slices, and sugar crystals.",
                    "volume": "Чайник", "price": 1800, "is_popular": True, "img": "/static/assets/menu/hd-05.jpg"
                },
                {
                    "cat": "hot-drinks", "sku": "HD-06", "name_ru": "Кофе с молоком", "name_kz": "Сүт қосқан кофе", "name_en": "Coffee with milk", "desc_ru": "Ароматный согревающий кофе с нежным вспененным молоком.", "desc_kz": "Таңертеңгі сергектік сыйлайтын сүт қосылған хош иісті ыстық кофе.", "desc_en": "Hot aromatic brewed coffee with smooth steamed milk.",
                    "volume": "1 чашка", "price": 700, "is_popular": True, "img": "/static/assets/menu/hd-06.jpg"
                },
                {
                    "cat": "hot-drinks", "sku": "HD-07", "name_ru": "MacTea / MacCoffee 3 в 1", "name_kz": "MacTea / MacCoffee 3 в 1", "name_en": "MacTea / MacCoffee 3-in-1", "desc_ru": "Популярный растворимый горячий напиток 3 в 1 для быстрого согревания в пути.", "desc_kz": "Жол үстінде тез дайындалатын тәтті әрі сергіткіш 3-і 1-де ыстық сусын.", "desc_en": "Quick hot instant coffee or tea beverage with sweet creamer.",
                    "volume": "1 чашка", "price": 400, "is_popular": False, "img": "/static/assets/menu/hd-07.jpg"
                },

                # --- FOR TEA ---
                {
                    "cat": "for-tea", "sku": "TEA-01", "name_ru": "Вафли и печенье к чаю", "name_kz": "Қытырлақ вафли мен печенье", "name_en": "Crispy wafers and cookies", "desc_ru": "Хрустящие сладкие вафли со сливочной начинкой и рассыпчатое сахарное печенье.", "desc_kz": "Шай ішуге арналған тәтті сүзбе вафлилері мен үгілмелі печеньелер.", "desc_en": "Crunchy cream-filled wafers and golden butter cookies for tea time.",
                    "price": 700, "is_popular": False, "img": "/static/assets/menu/tea-01.jpg"
                },
                {
                    "cat": "for-tea", "sku": "TEA-02", "name_ru": "Печенье Альбени (Albeni)", "name_kz": "Альбени шоколадты печеньесі", "name_en": "Albeni caramel chocolate cookies", "desc_ru": "Популярное печенье в молочном шоколаде с тягучей карамелью внутри.", "desc_kz": "Сүтті шоколадпен қапталған, ішінде созылмалы карамелі бар танымал печенье.", "desc_en": "Crisp biscuit bars coated with milk chocolate and chewy caramel.",
                    "price": 800, "is_popular": False, "img": "/static/assets/menu/tea-02.jpg"
                },
                {
                    "cat": "for-tea", "sku": "TEA-03", "name_ru": "Шоколад Казахстанский / Alpen Gold", "name_kz": "Қазақстандық шоколад / Alpen Gold", "name_en": "Kazakhstan chocolate bar", "desc_ru": "Плитка отборного молочного или темного шоколада к приятному чаепитию.", "desc_kz": "Шайға арналған нағыз қазақстандық сүтті немесе қара шоколад тақтасы.", "desc_en": "Classic Kazakhstan iconic premium chocolate bar or Alpen Gold.",
                    "price": 1400, "is_popular": True, "img": "/static/assets/menu/tea-03.jpg"
                },
                {
                    "cat": "for-tea", "sku": "TEA-04", "name_ru": "Батончики Сникерс / Твикс", "name_kz": "Сникерс / Твикс батончиктері", "name_en": "Snickers / Twix candy bars", "desc_ru": "Любимые питательные шоколадные батончики с арахисом, карамелью или печеньем.", "desc_kz": "Жержаңғақ, карамель және қытырлақ печенье қосылған тәтті батончиктер.", "desc_en": "Classic chocolate candy bars packed with roasted peanuts, caramel, or biscuit.",
                    "price": 600, "is_popular": False, "img": "",
                    "variants": [
                        {"name_ru": "Стандартный", "name_kz": "Стандартты", "name_en": "Standard", "size": "1 шт", "price": 600},
                        {"name_ru": "Большой", "name_kz": "Үлкен", "name_en": "Large", "size": "Super", "price": 900},
                    ]
                },
                {
                    "cat": "for-tea", "sku": "TEA-05", "name_ru": "Пирожное десертное", "name_kz": "Тәтті бәліш (десерттік пирожное)", "name_en": "Gourmet pastry cake", "desc_ru": "Нежное слоеное или бисквитное пирожное с кремовой прослойкой к горячему чаю.", "desc_kz": "Ыстық шайға арналған кремді нәзік бисквитті тәтті пирожное.", "desc_en": "Delicate layered sponge pastry cake with rich sweet cream.",
                    "price": 1000, "is_popular": False, "img": "/static/assets/menu/tea-05.jpg"
                },
                {
                    "cat": "for-tea", "sku": "TEA-06", "name_ru": "Круассаны Яшкино", "name_kz": "Яшкино дәмді круассандары", "name_en": "Yashkino flaky croissants", "desc_ru": "Воздушные слоеные мини-круассаны с нежной кремовой или шоколадной начинкой.", "desc_kz": "Шоколадты немесе кремді салмасы бар үлпілдек мини-круассандар.", "desc_en": "Flaky golden miniature croissants filled with creamy chocolate filling.",
                    "price": 1200, "is_popular": False, "img": "/static/assets/menu/tea-06.jpg"
                },

                # --- BAKERY PRODUCTS ---
                {
                    "cat": "bakery", "sku": "BK-01", "name_ru": "Хлебная корзина", "name_kz": "Нан себеті", "name_en": "Fresh bread basket", "desc_ru": "Свежий нарезной белый и ржаной хлеб к горячим блюдам и супам.", "desc_kz": "Ыстық тағамдар мен сорпаларға арналған жаңа піскен ақ және қара нан тілімдері.", "desc_en": "Assortment of freshly sliced white and wheat table breads.",
                    "price": 400, "is_popular": False, "img": "/static/assets/menu/bk-01.jpg"
                },
                {
                    "cat": "bakery", "sku": "BK-02", "name_ru": "Пирожки с картошкой или капустой", "name_kz": "Картоп немесе қырыққабат бәліштері", "name_en": "Pirozhki with potato or cabbage", "desc_ru": "Теплые домашние пирожки из нежного дрожжевого теста с сытной начинкой.", "desc_kz": "Дәмді ашыған қамырдан пеште пісірілген ыстық үй пирожкилері.", "desc_en": "Warm oven-baked soft yeast pastries stuffed with seasoned potato or cabbage.",
                    "price": 400, "is_popular": True, "img": "/static/assets/menu/bk-02.jpg"
                },
                {
                    "cat": "bakery", "sku": "BK-03", "name_ru": "Сосиски в тесте", "name_kz": "Қамырда пісірілген шұжық", "name_en": "Sausage baked in dough", "desc_ru": "Аппетитная сочная сосиска, запеченная в мягком золотистом тесте.", "desc_kz": "Алтын түстес үлпілдек қамырға оралып пісірілген шырынды шұжық.", "desc_en": "Juicy hot dog sausage wrapped in golden, soft baked dough.",
                    "price": 500, "is_popular": True, "img": "/static/assets/menu/bk-03.jpg"
                },
                {
                    "cat": "bakery", "sku": "BK-04", "name_ru": "Булочка сдобная", "name_kz": "Тәтті пісірілген тоқаш", "name_en": "Sweet bakery bun", "desc_ru": "Свежевыпеченная сладкая сдобная булочка с румяной сахарной корочкой.", "desc_kz": "Пештен жаңа шыққан хош иісті, жұмсақ әрі тәтті сүзбе тоқаш.", "desc_en": "Soft, golden-baked sweet breakfast bun with a light glaze.",
                    "price": 400, "is_popular": False, "img": "/static/assets/menu/bk-04.jpg"
                },
                {
                    "cat": "bakery", "sku": "BK-05", "name_ru": "Пицца порционная", "name_kz": "Ыстық ірімшікті пицца", "name_en": "Personal cheese pizza", "desc_ru": "Горячая сытная пицца с сыром моцарелла, колбасками и томатным соусом.", "desc_kz": "Моцарелла ірімшігі, шұжық пен қызанақ соусы қосылған ыстық порциялық пицца.", "desc_en": "Hot baked pizza slice with melted mozzarella, savory sausage, and tomato sauce.",
                    "price": 2600, "is_popular": True, "img": "/static/assets/menu/bk-05.jpg"
                },

                # --- SOFT DRINKS (with variants) ---
                {
                    "cat": "drinks", "sku": "DR-01", "name_ru": "Лимонады в ассортименте", "name_kz": "Түрлі жемісті лимонадтар", "name_en": "Assorted fruit lemonades", "desc_ru": "Освежающий газированный фруктовый лимонад со льдом и ярким вкусом.", "desc_kz": "Жол бойында шөл басатын салқын gazды жеміс лимонады.", "desc_en": "Chilled sparkling fruity lemonades with natural citrus zest.",
                    "price": 1500, "is_popular": True, "img": "/static/assets/drinks_tea.jpg",
                    "variants": [
                        {"name_ru": "Кувшин 1 л", "name_kz": "1 л", "name_en": "1 L Pitcher", "size": "1 L", "price": 1500},
                        {"name_ru": "Бокал 0.4 л", "name_kz": "0.4 л", "name_en": "0.4 L Glass", "size": "0.4 L", "price": 1700},
                    ]
                },
                {
                    "cat": "drinks", "sku": "DR-02", "name_ru": "Соки натуральные в ассортименте", "name_kz": "Табиғи жеміс шырындары", "name_en": "Natural fruit juices", "desc_ru": "Освежающий натуральный фруктовый сок (яблоко, апельсин, мультифрукт).", "desc_kz": "Алма, апельсин немесе мультифрукт дәмі бар балғын табиғи шырындар.", "desc_en": "Chilled pure fruit juices (apple, orange, mixed fruit).",
                    "volume": "1 L", "price": 1500, "is_popular": False, "img": "/static/assets/menu/dr-02.jpg"
                },
                {
                    "cat": "drinks", "sku": "DR-03", "name_ru": "Детский сок с трубочкой", "name_kz": "Түтікшелі балалар шырыны", "name_en": "Kids juice box with straw", "desc_ru": "Удобная коробочка натурального сока для маленьких путешественников.", "desc_kz": "Кішкентай жолаушыларға арналған ыңғайлы түтікшесі бар табиғи шырын.", "desc_en": "Convenient natural juice box designed for young passengers.",
                    "volume": "0.2 L", "price": 700, "is_popular": False, "img": "/static/assets/menu/dr-03.jpg"
                },
                {
                    "cat": "drinks", "sku": "DR-04", "name_ru": "Минеральная вода Сарыагаш", "name_kz": "Сарыағаш минералды суы", "name_en": "Saryagash mineral water", "desc_ru": "Знаменитая природная минеральная лечебно-столовая вода из Казахстана.", "desc_kz": "Қазақстанның әйгілі табиғи минералды емдік-асханалық газдалған суы.", "desc_en": "Renowned Kazakhstan natural sparkling mineral water.",
                    "volume": "1.5 L", "price": 700, "is_popular": True, "img": "/static/assets/menu/dr-04.jpg"
                },
                {
                    "cat": "drinks", "sku": "DR-05", "name_ru": "Coca-Cola (газ. напиток)", "name_kz": "Кока-кола салқын сусыны", "name_en": "Coca-Cola chilled drink", "desc_ru": "Классический охлажденный газированный напиток Coca-Cola.", "desc_kz": "Мұздай сергітетін әйгілі классикалық Coca-Cola газды сусыны.", "desc_en": "Chilled iconic refreshing Coca-Cola soda.",
                    "price": 650, "is_popular": True, "img": "",
                    "variants": [
                        {"name_ru": "Бутылка 0.5 л", "name_kz": "0.5 л", "name_en": "0.5 L Bottle", "size": "0.5 L", "price": 650},
                        {"name_ru": "Бутылка 1 л", "name_kz": "1 л", "name_en": "1 L Bottle", "size": "1 L", "price": 1000},
                    ]
                },
                {
                    "cat": "drinks", "sku": "DR-06", "name_ru": "Maxi Tea / Fuse Tea холодный чай", "name_kz": "Макси чай / Fuse Tea салқын шайы", "name_en": "Maxi Tea / Fuse Tea iced tea", "desc_ru": "Освежающий холодный чай с сочным вкусом персика или лимона.", "desc_kz": "Шабдалы немесе лимон дәмі бар сергіткіш салқын шөл басар шай.", "desc_en": "Refreshing chilled iced tea with peach or lemon infusion.",
                    "price": 650, "is_popular": False, "img": "",
                    "variants": [
                        {"name_ru": "Бутылка 0.5 л", "name_kz": "0.5 л", "name_en": "0.5 L Bottle", "size": "0.5 L", "price": 650},
                        {"name_ru": "Бутылка 1 л", "name_kz": "1 л", "name_en": "1 L Bottle", "size": "1 L", "price": 1000},
                    ]
                },
                {
                    "cat": "drinks", "sku": "DR-07", "name_ru": "Вода питьевая негазированная", "name_kz": "Табиғи газдалмаған ауыз су", "name_en": "Pure still drinking water", "desc_ru": "Кристально чистая природная питьевая вода без газа.", "desc_kz": "Мөлдір таза табиғи газдалмаған бөтелкедегі ауыз суы.", "desc_en": "Pure natural still drinking water bottle.",
                    "price": 500, "is_popular": False, "img": "",
                    "variants": [
                        {"name_ru": "0.5 л", "name_kz": "0.5 л", "name_en": "0.5 L", "size": "0.5 L", "price": 500},
                        {"name_ru": "1 л", "name_kz": "1 л", "name_en": "1 L", "size": "1 L", "price": 700},
                    ]
                },
                {
                    "cat": "drinks", "sku": "DR-08", "name_ru": "Dizzy энергетический напиток", "name_kz": "Диззи энергетикалық сусыны", "name_en": "Dizzy energy drink", "desc_ru": "Бодрящий энергетический напиток для поддержания сил во время долгой поездки.", "desc_kz": "Ұзақ сапарда сергектік пен күш-қуат беретін салқын энергетикалық сусын.", "desc_en": "Chilled energy drink to keep your energy high during night travels.",
                    "volume": "0.33 L", "price": 900, "is_popular": False, "img": "/static/assets/menu/dr-08.jpg"
                },
                {
                    "cat": "drinks", "sku": "DR-09", "name_ru": "Gorilla энергетический напиток", "name_kz": "Горилла энергетикалық сусыны", "name_en": "Gorilla energy drink", "desc_ru": "Мощный энергетический напиток для максимального заряда бодрости.", "desc_kz": "Қуаттандыратын ерекше дәмі бар салқын Gorilla энергетикалық сусыны.", "desc_en": "Powerful energy drink for a quick refreshing boost.",
                    "volume": "0.5 L", "price": 1000, "is_popular": False, "img": "/static/assets/menu/dr-09.jpg"
                },

                # --- BEER SNACKS ---
                {
                    "cat": "beer-snacks", "sku": "BS-01", "name_ru": "Чипсы Lay's в ассортименте", "name_kz": "Lays қытырлақ картоп чипсылары", "name_en": "Lay's potato chips assortment", "desc_ru": "Хрустящие картофельные чипсы из натурального картофеля с любимыми вкусами.", "desc_kz": "Табиғи картоптан әзірленген қытырлақ Lays чипсыларының ассортименті.", "desc_en": "Crispy salted potato chips made with natural potatoes in popular flavors.",
                    "price": 700, "is_popular": False, "img": "",
                    "variants": [
                        {"name_ru": "40 г", "name_kz": "40 г", "name_en": "40 g", "size": "40 g", "price": 700},
                        {"name_ru": "80 г", "name_kz": "80 г", "name_en": "80 g", "size": "80 g", "price": 1000},
                    ]
                },
                {
                    "cat": "beer-snacks", "sku": "BS-02", "name_ru": "Сухарики ржаные к пиву", "name_kz": "Кептірілген қытырлақ нан (сухарики)", "name_en": "Toasted rye beer croutons", "desc_ru": "Пикантные хрустящие ржаные сухарики с чесноком или вкусом дымка.", "desc_kz": "Сарымсақ немесе қақталған дәмдеуіштер қосылған қытырлақ қара нан.", "desc_en": "Crunchy roasted rye bread croutons seasoned with garlic and spices.",
                    "price": 500, "is_popular": False, "img": "",
                    "variants": [
                        {"name_ru": "40 г", "name_kz": "40 г", "name_en": "40 g", "size": "40 g", "price": 500},
                        {"name_ru": "130 г", "name_kz": "130 г", "name_en": "130 g", "size": "130 g", "price": 800},
                    ]
                },
                {
                    "cat": "beer-snacks", "sku": "BS-03", "name_ru": "Арахис соленый обжаренный", "name_kz": "Қуырылған тұзды жержаңғақ", "name_en": "Roasted salted peanuts", "desc_ru": "Золотистый отборный обжаренный арахис с морской солью.", "desc_kz": "Теңіз тұзымен алтын түстес қызарып қуырылған таңдаулы жержаңғақ.", "desc_en": "Golden crunchy peanuts roasted with fine sea salt.",
                    "weight": "50 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bs-03.jpg"
                },
                {
                    "cat": "beer-snacks", "sku": "BS-04", "name_ru": "Фисташки отборные соленые", "name_kz": "Таңдаулы тұздалған пісте (фисташки)", "name_en": "Premium salted pistachios", "desc_ru": "Отборные калифорнийские фисташки в раскрытой скорлупе с легкой солью.", "desc_kz": "Жеңіл тұздалған, қабығы ашылған ірі әрі сапалы дәмді пісте.", "desc_en": "Roasted jumbo in-shell pistachios with light sea salt.",
                    "weight": "30 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bs-04.jpg"
                },
                {
                    "cat": "beer-snacks", "sku": "BS-05", "name_ru": "Сыр Чечил копченый косичка", "name_kz": "Чечил қақталған сүзбе ірімшігі", "name_en": "Chechil smoked string cheese", "desc_ru": "Традиционный натуральный копченый волокнистый сыр к прохладным напиткам.", "desc_kz": "Салқын сыра мен сусындарға өте үйлесімді қақталған өрімді Чечил ірімшігі.", "desc_en": "Braided smoked string cheese with savory smoky aroma and chewy texture.",
                    "weight": "50 g", "price": 800, "is_popular": False, "img": "/static/assets/menu/bs-05.jpg"
                },

                # --- BEER ---
                {"cat": "beer", "sku": "BR-01", "name_ru": "Кружка свежего разливного пива", "name_kz": "Балғын құйма сыра кружкасы", "name_en": "Mug of fresh draft beer", "desc_ru": "Освежающее светлое разливное пиво с плотной белой шапкой пены.", "desc_kz": "Қою ақ көбігі бар, шөлді керемет басатын салқын құйма сыра.", "desc_en": "Chilled fresh draft lager served in a frosted mug with a creamy head.", "volume": "0.45 L", "price": 1200, "is_popular": True, "img": "/static/assets/menu/br-01.jpg"},
                {"cat": "beer", "sku": "BR-02", "name_ru": "Пиво Белый медведь", "name_kz": "Ақ аю сырасы (Белый медведь)", "name_en": "Bely Medved lager beer", "desc_ru": "Классический светлый лагер с мягким солодовым вкусом и легкой горчинкой.", "desc_kz": "Жұмсақ уыт дәмі мен жеңіл ащылығы бар классикалық ақшыл лагер.", "desc_en": "Classic light lager with mellow malt flavor and clean crisp finish.", "volume": "0.45 L", "price": 1200, "is_popular": False, "img": "/static/assets/menu/br-02.jpg"},
                {"cat": "beer", "sku": "BR-03", "name_ru": "Пиво Жатецкий гусь", "name_kz": "Жатецкий гусь чех сырасы", "name_en": "Zatecky Gus Czech-style beer", "desc_ru": "Традиционное пиво, сваренное с добавлением знаменитого чешского жатецкого хмеля.", "desc_kz": "Атақты чех жатец құлмағынан қайнатылған хош иісті сыра.", "desc_en": "Aromatic lager brewed with celebrated Saaz hops for rich herbal flavor.", "volume": "0.45 L", "price": 1200, "is_popular": False, "img": "/static/assets/menu/br-03.jpg"},
                {"cat": "beer", "sku": "BR-04", "name_ru": "Пиво Жигулевское", "name_kz": "Жигули дәстүрлі сырасы", "name_en": "Zhigulevskoe classic beer", "desc_ru": "Легендарный советский сорт светлого ячменного пива с чистым вкусом.", "desc_kz": "Таза арпа уыты дәмі бар әйгілі дәстүрлі ақшыл сыра сорты.", "desc_en": "Legendary crisp pale lager brewed to authentic heritage standards.", "volume": "0.45 L", "price": 1200, "is_popular": False, "img": "/static/assets/menu/br-04.jpg"},
                {"cat": "beer", "sku": "BR-05", "name_ru": "Пиво Прага (Praga)", "name_kz": "Прага премиум сырасы", "name_en": "Praga premium pilsner", "desc_ru": "Премиальный европейский пилснер с глубоким золотистым цветом и благородным хмелем.", "desc_kz": "Алтын түстес реңкі және ерекше дәмі бар еуропалық премиум сыра.", "desc_en": "European premium pilsner with deep golden hue and noble hop bitterness.", "volume": "0.45 L", "price": 1200, "is_popular": False, "img": "/static/assets/menu/br-05.jpg"},
                {"cat": "beer", "sku": "BR-06", "name_ru": "Пиво Miller Genuine Draft", "name_kz": "Miller салқын сырасы", "name_en": "Miller Genuine Draft beer", "desc_ru": "Мягкое американское пиво четырехкратной холодной фильтрации в прозрачной бутылке.", "desc_kz": "Төрт мәрте салқын сүзгіден өткен жұмсақ дәмі бар америкалық сыра.", "desc_en": "Exceptionally smooth cold-filtered American draft lager in bottle.", "volume": "0.5 L", "price": 1500, "is_popular": True, "img": "/static/assets/menu/br-06.jpg"},
                {"cat": "beer", "sku": "BR-07", "name_ru": "Пиво Heineken премиум", "name_kz": "Heineken премиум сырасы", "name_en": "Heineken premium lager", "desc_ru": "Всемирно известный премиальный нидерландский лагер в фирменной зеленой бутылке.", "desc_kz": "Әлемге танымал голландиялық премиум ақшыл лагер сырасы.", "desc_en": "World-famous Dutch premium lager with characteristic 100% barley malt.", "volume": "0.5 L", "price": 1500, "is_popular": True, "img": "/static/assets/menu/br-07.jpg"},

                # --- VODKA ---
                {"cat": "vodka", "sku": "VD-01", "name_ru": "Водка Хаома (Haoma)", "name_kz": "Хаома премиум арағы", "name_en": "Haoma premium vodka", "desc_ru": "Премиальная казахстанская водка на чистейшей родниковой воде с мягким вкусом.", "desc_kz": "Мөлдір бұлақ суынан жасалған жұмсақ дәмі бар қазақстандық премиум арақ.", "desc_en": "Classic Kazakhstan premium wheat vodka distilled with pristine mineral water.", "volume": "0.5 L", "price": 6000, "is_popular": False, "img": "/static/assets/menu/vd-01.jpg"},
                {"cat": "vodka", "sku": "VD-02", "name_ru": "Водка Зерно", "name_kz": "Зерно астық арағы", "name_en": "Zerno grain vodka", "desc_ru": "Классическая водка из отборного зернового спирта Люкс с кристальной очисткой.", "desc_kz": "Таңдаулы Люкс астық спиртінен сүзіліп жасалған кристалдай таза арақ.", "desc_en": "Traditional grain vodka distilled from select wheat with crystal filtration.", "volume": "0.5 L", "price": 6000, "is_popular": False, "img": "/static/assets/menu/vd-02.jpg"},
                {"cat": "vodka", "sku": "VD-03", "name_ru": "Водка Organic", "name_kz": "Organic табиғи таза арағы", "name_en": "Organic clean craft vodka", "desc_ru": "Экологически чистая натуральная органическая водка высшей категории.", "desc_kz": "Табиғи органикалық өнімдерден дайындалған жоғары санатты таза арақ.", "desc_en": "Certified organic wheat vodka with ultra-smooth character.", "volume": "0.5 L", "price": 7000, "is_popular": False, "img": "/static/assets/menu/vd-03.jpg"},
                {"cat": "vodka", "sku": "VD-04", "name_ru": "Водка Хортица Айс", "name_kz": "Хортица айс салқын арағы", "name_en": "Khortytsa Ice chilled vodka", "desc_ru": "Особая мягкая водка в бутылке, меняющей цвет при охлаждении.", "desc_kz": "Салқындатылған кезде түсін өзгертетін ерекше бөтелкедегі жұмсақ арақ.", "desc_en": "Specially filtered smooth vodka in temperature-sensitive frost bottle.", "volume": "0.5 L", "price": 7000, "is_popular": False, "img": "/static/assets/menu/vd-04.jpg"},
                {"cat": "vodka", "sku": "VD-05", "name_ru": "Водка Кызылжар", "name_kz": "Қызылжар дәстүрлі арағы", "name_en": "Kyzylzhar heritage vodka", "desc_ru": "Традиционная северно-казахстанская водка с проверенным мягким вкусом.", "desc_kz": "Солтүстік Қазақстанның байырғы рецептімен жасалған дәстүрлі жұмсақ арақ.", "desc_en": "Heritage Northern Kazakhstan vodka crafted from pure grain spirit.", "volume": "0.5 L", "price": 7000, "is_popular": False, "img": "/static/assets/menu/vd-05.jpg"},
                {"cat": "vodka", "sku": "VD-06", "name_ru": "Водка Nemiroff Lex", "name_kz": "Nemiroff Lex элиталық арағы", "name_en": "Nemiroff Lex luxury vodka", "desc_ru": "Элитная супер-премиальная водка двенадцатиступенчатой очистки.", "desc_kz": "Он екі мәрте сүзгіден өткен жоғары санатты элиталық салтанатты арақ.", "desc_en": "Ultra-premium luxury vodka finished with fine platinum and silver filtration.", "volume": "0.5 L", "price": 9000, "is_popular": True, "img": "/static/assets/menu/vd-06.jpg"},

                # --- SPIRITS: COGNAC / WINE / WHISKY ---
                {
                    "cat": "spirits", "sku": "SP-01", "name_ru": "Коньяк Казахстан выдержанный", "name_kz": "Қазақстан ескірген коньяғы", "name_en": "Kazakhstan aged amber cognac", "desc_ru": "Благородный золотисто-янтарный коньяк из отборных виноматериалов с тонами ванили и дуба.", "desc_kz": "Емен бөшкесінде бапталған ваниль мен кепкен жеміс хош иісі бар атақты коньяк.", "desc_en": "Aged golden amber brandy with smooth notes of oak, vanilla, and dried fruits.",
                    "price": 700, "is_popular": True, "img": "",
                    "variants": [
                        {"name_ru": "Порция 50 мл", "name_kz": "50 мл порция", "name_en": "50 ml Shot", "size": "50 ml", "price": 700},
                        {"name_ru": "Бутылка 0.5 л", "name_kz": "0.5 л бөтелке", "name_en": "0.5 L Bottle", "size": "0.5 L", "price": 7000},
                    ]
                },
                {
                    "cat": "spirits", "sku": "SP-02", "name_ru": "Вино коллекционное (красное / белое)", "name_kz": "Коллекциялық шарап (қызыл / ақ)", "name_en": "Fine wine bottle (red / white)", "desc_ru": "Изысканное столовое вино с гармоничным фруктовым букетом и долгим послевкусием.", "desc_kz": "Жемісті үйлесімді хош иісі бар таңдаулы қызыл немесе ақ шарап бөтелкесі.", "desc_en": "Selected dining wine featuring balanced fruit bouquet and elegant finish.",
                    "volume": "0.7 L", "price": 7000, "is_popular": False, "img": "/static/assets/menu/sp-02.jpg"
                },
                {
                    "cat": "spirits", "sku": "SP-03", "name_ru": "Виски Ballantine's Scotch", "name_kz": "Ballantines шотланд вискиі", "name_en": "Ballantine's Blended Scotch Whisky", "desc_ru": "Знаменитый купажированный шотландский виски со сбалансированным вкусом меда и спелых яблок.", "desc_kz": "Бал мен піскен алманың үйлесімді дәмі бар әйгілі купажды шотланд вискиі.", "desc_en": "Renowned blended Scotch whisky balanced with subtle notes of honey, vanilla, and apple.",
                    "price": 1500, "is_popular": True, "img": "",
                    "variants": [
                        {"name_ru": "Порция 50 мл", "name_kz": "50 мл порция", "name_en": "50 ml Shot", "size": "50 ml", "price": 1500},
                        {"name_ru": "Бутылка 0.5 л", "name_kz": "0.5 л бөтелке", "name_en": "0.5 L Bottle", "size": "0.5 L", "price": 15000},
                    ]
                },
                {
                    "cat": "spirits", "sku": "SP-04", "name_ru": "Виски Jack Daniel's Tennessee", "name_kz": "Jack Daniel's америкалық вискиі", "name_en": "Jack Daniel's Tennessee Whiskey", "desc_ru": "Легендарный американский виски с фильтрацией через уголь сахарного клена и нотками карамели.", "desc_kz": "Қантты үйеңкі көмірінен сүзілген карамель мен түтін дәмі бар аңызға айналған виски.", "desc_en": "Iconic charcoal-mellowed Tennessee whiskey with rich caramel and toasted oak aroma.",
                    "price": 2000, "is_popular": True, "img": "",
                    "variants": [
                        {"name_ru": "Порция 50 мл", "name_kz": "50 мл порция", "name_en": "50 ml Shot", "size": "50 ml", "price": 2000},
                        {"name_ru": "Бутылка 0.5 л", "name_kz": "0.5 л бөтелке", "name_en": "0.5 L Bottle", "size": "0.5 L", "price": 20000},
                    ]
                },
            ]

            for item in items_to_seed:
                cid = cat_map[item["cat"]]
                mi = MenuItem(
                    category_id=cid,
                    sku=item.get("sku", ""),
                    name_ru=item["name_ru"],
                    name_kz=item["name_kz"],
                    name_en=item["name_en"],
                    ingredients_ru=item.get("ingredients_ru", ""),
                    ingredients_kz=item.get("ingredients_kz", ""),
                    ingredients_en=item.get("ingredients_en", ""),
                    description_ru=item.get("desc_ru", ""),
                    description_kz=item.get("desc_kz", ""),
                    description_en=item.get("desc_en", ""),
                    weight_value=item.get("weight", ""),
                    volume_value=item.get("volume", ""),
                    price=Decimal(str(item["price"])),
                    image_url=item.get("img") or f"/static/assets/menu/{item.get('sku', '').lower()}.jpg",
                    is_popular=item.get("is_popular", False),
                    is_available=True,
                    is_active=True
                )
                db.add(mi)
                db.flush()

                if "variants" in item:
                    for v in item["variants"]:
                        db.add(MenuItemVariant(
                            menu_item_id=mi.id,
                            name_ru=v["name_ru"],
                            name_kz=v.get("name_kz", v["name_ru"]),
                            name_en=v.get("name_en", v["name_ru"]),
                            volume_or_weight=v.get("size", ""),
                            price=Decimal(str(v["price"])),
                            is_available=True
                        ))

        db.commit()
    print("DAR | RES group database upgrade & seed completed successfully.")


if __name__ == "__main__":
    upgrade_and_seed()
