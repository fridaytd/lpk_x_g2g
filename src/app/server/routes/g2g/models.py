from pydantic import BaseModel

from .enums import OrderStatus, OrderPaymentStatus, OrderEventType


class OtherPricing(BaseModel):
    currency: str
    unit_price: float


class CreatedOrderPayload(BaseModel):
    order_id: str
    order_status: OrderStatus
    order_payment_status: OrderPaymentStatus
    seller_id: str
    buyer_id: str
    offer_currency: str
    checkout_currency: str
    unit_price: float
    amount: float
    refunded_amount: float
    commission_fee: float
    commission_fee_rate: int
    offer_service_type: str
    purchased_qty: int
    delivered_qty: int
    refunded_qty: int
    defected_qty: int
    replacement_qty: int
    product_id: str
    offer_id: str
    order_created_at: int
    other_pricing: list[OtherPricing]


class ConfirmedOrderPayload(BaseModel):
    order_id: str
    order_status: OrderStatus
    order_payment_status: OrderPaymentStatus
    seller_id: str
    buyer_id: str
    offer_currency: str
    checkout_currency: str
    unit_price: float
    amount: float
    refunded_amount: float
    commission_fee: float
    commission_fee_rate: int
    offer_service_type: str
    purchased_qty: int
    delivered_qty: int
    refunded_qty: int
    defected_qty: int
    replacement_qty: int
    product_id: str
    offer_id: str
    order_created_at: int


class OrderEvent(BaseModel):
    id: str
    event_happened_at: int
    event_type: OrderEventType
    payload: CreatedOrderPayload
