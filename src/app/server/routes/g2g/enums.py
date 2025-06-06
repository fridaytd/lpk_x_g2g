from enum import Enum


class OrderEventType(Enum):
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_DELIVERY_STATUS = "order.delivery_status"
    ORDER_API_DELIVERY = "order.api_delivery"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_COMPLETED = "order.completed"
    ORDER_ROLLBACK_CANCELLED = "order.rollback_cancelled"
    ORDER_ROLLBACK_COMPLETED = "order.rollback_completed"
    ORDER_CASE_OPENED = "order.case_opened"


class OrderStatus(Enum):
    UNPAID = "unpaid"
    PAYMENT_REVIEW = "payment_review"
    PENDING_CLEARING = "pending_clearing"
    VERIFYING_PAYMENT = "verifying_payment"
    REFUND_TXN_IN_PROGRESS = "refund_txn_in_progress"
    TO_DELIVER = "to_deliver"
    START_DELIVER = "start_deliver"
    DELIVERING = "delivering"
    DELIVERING_IN_PROGRESS = "delivering_in_progress"
    AWAITING_BUYER_CONFIRMATION = "awaiting_buyer_confirmation"
    DELIVERED = "delivered"
    PARTIAL_DELIVERED = "partial_delivered"
    REFUNDED = "refunded"
    PAYMENT_NOT_RECEIVED = "payment_not_received"
    PAYMENT_FAILED = "payment_failed"


class OrderPaymentStatus(Enum):
    TO_PAY = "to_pay"
    PAID = "paid"
    CANCELLED = "cancelled"
