import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, enum.Enum):
    PASSENGER = "PASSENGER"
    KITCHEN = "KITCHEN"
    DELIVERY_STAFF = "DELIVERY_STAFF"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.KITCHEN)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Train(Base):
    __tablename__ = "trains"

    id: Mapped[int] = mapped_column(primary_key=True)
    train_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    route_name: Mapped[str] = mapped_column(String(160), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(String(255), default="")
    # WhatsApp нөмірі — осы пойыздың аспазы (поваруы). Тапсырыс осы нөмірге жіберіледі.
    cook_name: Mapped[str] = mapped_column(String(120), default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    carriages: Mapped[list["Carriage"]] = relationship(back_populates="train", cascade="all, delete-orphan", lazy="selectin")


class Carriage(Base):
    __tablename__ = "carriages"

    id: Mapped[int] = mapped_column(primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id", ondelete="CASCADE"), index=True)
    carriage_number: Mapped[str] = mapped_column(String(16), index=True)
    carriage_type: Mapped[str] = mapped_column(String(60), default="Купе / Compartment")
    delivery_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    qr_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    train: Mapped[Train] = relationship(back_populates="carriages")


class QRCodeContext(Base):
    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    train_number: Mapped[str] = mapped_column(String(32))
    carriage_number: Mapped[str] = mapped_column(String(16))
    table_number: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(120))
    name_kz: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["MenuItem"]] = relationship(back_populates="category", cascade="all, delete-orphan", lazy="selectin")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("menu_categories.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(60), default="")
    name_ru: Mapped[str] = mapped_column(String(160))
    name_kz: Mapped[str] = mapped_column(String(160))
    name_en: Mapped[str] = mapped_column(String(160))
    description_ru: Mapped[str] = mapped_column(Text, default="")
    description_kz: Mapped[str] = mapped_column(Text, default="")
    description_en: Mapped[str] = mapped_column(Text, default="")
    ingredients_ru: Mapped[str] = mapped_column(Text, default="")
    ingredients_kz: Mapped[str] = mapped_column(Text, default="")
    ingredients_en: Mapped[str] = mapped_column(Text, default="")
    weight_value: Mapped[str] = mapped_column(String(50), default="")
    volume_value: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[float] = mapped_column(Numeric(12, 2))
    image_url: Mapped[str] = mapped_column(String(500), default="")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    # Стоп-лист: тағам қай күні таусылды деп белгіленді (келесі күні автоматты қайта қосылады)
    sold_out_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category: Mapped[MenuCategory] = relationship(back_populates="items")
    variants: Mapped[list["MenuItemVariant"]] = relationship(back_populates="menu_item", cascade="all, delete-orphan", lazy="selectin")


class MenuItemVariant(Base):
    __tablename__ = "menu_item_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"), index=True)
    name_ru: Mapped[str] = mapped_column(String(120))
    name_kz: Mapped[str] = mapped_column(String(120), default="")
    name_en: Mapped[str] = mapped_column(String(120), default="")
    volume_or_weight: Mapped[str] = mapped_column(String(60))
    price: Mapped[float] = mapped_column(Numeric(12, 2))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    menu_item: Mapped[MenuItem] = relationship(back_populates="variants")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    passenger_name: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    train_no: Mapped[str] = mapped_column(String(32), index=True)
    wagon_no: Mapped[str] = mapped_column(String(16), index=True)
    seat_no: Mapped[str] = mapped_column(String(16), index=True, default="")
    compartment_no: Mapped[str] = mapped_column(String(16), default="")
    table_no: Mapped[str] = mapped_column(String(16), default="")
    
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    service_charge_rate: Mapped[float] = mapped_column(Numeric(4, 2), default=0.10)
    service_charge: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.NEW,
        index=True,
    )
    comment: Mapped[str] = mapped_column(String(500), default="")
    cancel_reason: Mapped[str] = mapped_column(String(255), default="")
    # ONBOARD — пойыздағы тапсырыс; PREORDER — ланчбокс алдын ала тапсырысы (билетпен бірге, ≥24 сағат бұрын)
    order_type: Mapped[str] = mapped_column(String(16), default="ONBOARD", index=True)
    departure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Дайын болу уақыты (аспаз белгілейді), жолаушы бағасы, кім бас тартты
    ready_eta_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating_comment: Mapped[str] = mapped_column(String(500), default="")
    rated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_by: Mapped[str] = mapped_column(String(16), default="")
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preparing_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    out_for_delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    delivery_assignment: Mapped[Optional["DeliveryAssignment"]] = relationship(back_populates="order", uselist=False, lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[int] = mapped_column(Integer, index=True)
    menu_variant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    item_name_snapshot: Mapped[str] = mapped_column(String(160))
    variant_snapshot: Mapped[str] = mapped_column(String(80), default="")
    price_snapshot: Mapped[float] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    line_total: Mapped[float] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[str] = mapped_column(String(40))
    new_status: Mapped[str] = mapped_column(String(40))
    changed_by: Mapped[str] = mapped_column(String(80), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="status_history")


class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True, index=True)
    staff_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    staff_name: Mapped[str] = mapped_column(String(120), default="")
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="delivery_assignment")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrderSequence(Base):
    __tablename__ = "order_sequences"

    id: Mapped[int] = mapped_column(primary_key=True)
    sequence_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    current_val: Mapped[int] = mapped_column(Integer, default=1000)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

