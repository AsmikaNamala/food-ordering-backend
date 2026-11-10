from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(15))
    created_at = Column(DateTime, server_default=func.now())
class Client(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(15))
    created_at = Column(DateTime, server_default=func.now())
class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"), nullable=True)
    item_name = Column(String(100), nullable=False, unique=True)
    available_quantity = Column(Integer, nullable=False, default=0)
    minimum_quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    order_status = Column(String(30), default="PENDING")
    payment_status = Column(String, default="PENDING")
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    item_id = Column(Integer, ForeignKey("items.item_id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
class ReplenishmentRequest(Base):
    __tablename__ = "replenishment_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"), nullable=False)
    requested_quantity = Column(Integer, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime, nullable=True)