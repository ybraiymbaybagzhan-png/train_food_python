"""WhatsApp helpers: әр пойыздың аспазына тапсырыс жіберу (wa.me сілтемесі арқылы).

Жолаушы тапсырыс бергеннен кейін WhatsApp ашылады, хабарлама дайын жазылып тұрады —
жолаушы тек "Жіберу" батырмасын басады. Қосымша аккаунт немесе API кілті қажет емес.
"""
import re
from datetime import timedelta, timezone
from urllib.parse import quote

# Қазақстан уақыты (UTC+5) — жүрер уақыты осы белдеуде енгізіледі
KZ_TZ = timezone(timedelta(hours=5))


def to_kz(dt):
    """Дерекқордан келген datetime (SQLite-та tz жоғалады) — UTC деп алып, KZ уақытына ауыстырады."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KZ_TZ)


def format_departure(dt) -> str:
    local = to_kz(dt)
    return local.strftime("%d.%m.%Y %H:%M") if local else ""


def normalize_phone(raw: str | None) -> str:
    """Нөмірден тек цифрларды қалдырып, халықаралық пішімге келтіреді (wa.me үшін).

    8 707 123 45 67 -> 77071234567;  707 123 45 67 -> 77071234567
    """
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    return digits


def is_valid_phone(raw: str | None) -> bool:
    return 10 <= len(normalize_phone(raw)) <= 15


def format_money(value) -> str:
    return f"{int(round(float(value))):,}".replace(",", " ") + " ₸"


def build_order_message(order) -> str:
    """Аспазға арналған тапсырыс мәтіні (орыс тілінде — аспаздар үшін ортақ тіл)."""
    is_preorder = getattr(order, "order_type", "ONBOARD") == "PREORDER"
    place = f"Вагон: {order.wagon_no or '—'} | Место: {order.seat_no or '—'}"
    if is_preorder:
        dep_str = format_departure(getattr(order, "departure_at", None)) or "—"
        header = f"🍱 ПРЕДЗАКАЗ ЛАНЧБОКСОВ {order.order_number}"
        route = f"Поезд: {order.train_no} | Отправление: {dep_str} | {place}"
    else:
        header = f"🚆 НОВЫЙ ЗАКАЗ {order.order_number}"
        route = f"Поезд: {order.train_no} | {place}"
    lines = [
        header,
        route + (f" | Купе: {order.compartment_no}" if order.compartment_no else ""),
        f"Пассажир: {order.passenger_name}",
        f"Телефон: {order.phone}",
        "",
        "Состав заказа:",
    ]
    for idx, oi in enumerate(order.items, start=1):
        variant = f" ({oi.variant_snapshot})" if oi.variant_snapshot else ""
        lines.append(
            f"{idx}. {oi.item_name_snapshot}{variant} × {oi.quantity} = {format_money(oi.line_total)}"
        )
    lines += [
        "",
        f"Подытог: {format_money(order.subtotal)}",
        f"Обслуживание ({int(float(order.service_charge_rate) * 100)}%): {format_money(order.service_charge)}",
        f"ИТОГО: {format_money(order.total)}",
    ]
    if order.comment:
        lines += ["", f"Комментарий: {order.comment}"]
    return "\n".join(lines)


def build_whatsapp_url(phone: str | None, message: str) -> str:
    normalized = normalize_phone(phone)
    if not normalized:
        return ""
    return f"https://wa.me/{normalized}?text={quote(message)}"
