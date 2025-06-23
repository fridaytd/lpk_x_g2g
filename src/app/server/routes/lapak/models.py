from pydantic import BaseModel


class ProductCallback(BaseModel):
    code: str
    name: str
    provider_code: str
    price: int
    status: str


class ProductCallbackPayload(BaseModel):
    data: ProductCallback
    meta: dict


class Transaction(BaseModel):
    id: str  # The id of the order
    product_name: str  # The name of the product
    note: str  # The notes of the transaction fulfillment
    status: str  # The status of the order
    voucher_code: str  # The value of voucher code, if the product is voucher. Otherwise it will be empty


class OrderCallbackData(BaseModel):
    status: str  # Overall status of the TID: SUCCESS | PENDING | REFUNDED
    tid: str  # The order ID that Lapakgaming returns upon creating order
    reference_id: str  # The reference ID that you've sent during create order
    transactions: list[Transaction]  # The list of orders for one single transaction ID


class OrderCallbackPayload(BaseModel):
    code: str  # The indication of overall status
    data: OrderCallbackData  # Contains all information status
