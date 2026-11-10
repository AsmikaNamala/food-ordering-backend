from pydantic import BaseModel, Field
from typing import Optional


class VendorCreate(BaseModel):
    vendor_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
class ClientCreate(BaseModel):
    client_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
class ItemCreate(BaseModel):
    item_name: str
    available_quantity: int = 0
    minimum_quantity: int
    price: float
    vendor_id: Optional[int] = None
class OrderItemCreate(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
class OrderCreate(BaseModel):
    client_id: int = Field(gt=0)
    items: list[OrderItemCreate] = Field(min_length=1)
class PaymentRequest(BaseModel):
    payment_success: bool
class ReplenishmentRequestCreate(BaseModel):
    item_id: int


class ReplenishmentReview(BaseModel):
    approved: bool