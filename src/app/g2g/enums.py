from enum import Enum


class OrderStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    START_DELIVERING = "start_delivering"
    DELIVERING = "delivering"
    AWAITING_BUYER_CONFIRMATION = "awaiting_buyer_confirmation"
    DELIVERED = "delivered"
    PARTIAL_DELIVERED = "partial_delivered"
