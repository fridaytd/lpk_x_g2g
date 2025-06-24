from pydantic import BaseModel

from .enums import (
    OrderStatus,
    OrderPaymentStatus,
    OrderEventType,
    DeliveryMethodCode,
    DeliveryMode,
)


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


class AttributeItem(BaseModel):
    attribute_group_id: str
    attribute_group_name: str
    attribute_id: str
    attribute_key: str
    attribute_value: str
    value: str


class DeliverySummary(BaseModel):
    delivery_id: str
    delivery_method_code: DeliveryMethodCode
    delivery_method_list: list[AttributeItem]
    delivery_mode: DeliveryMode
    case_id: str
    requested_qty: int
    requested_at: int
    expired_at: int = 0


class APIDeliveryPayload(BaseModel):
    order_id: str
    buyer_id: str
    seller_id: str
    offer_id: str
    purchased_qty: int
    defected_qty: int
    delivered_qty: int
    refunded_qty: int
    replacement_qty: int
    undelivered_qty: int
    delivery_summary: DeliverySummary


class OrderEvent(BaseModel):
    id: str | None = None
    event_happened_at: int | None = None
    event_type: OrderEventType
    payload: dict
