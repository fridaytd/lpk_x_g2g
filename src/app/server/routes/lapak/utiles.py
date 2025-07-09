from app.lpk.models import OrderStatusResponse
from .models import OrderCallbackPayload


def is_success_order(
    order_status_res: OrderStatusResponse | OrderCallbackPayload,
) -> bool:
    if order_status_res.data.status.upper() != "SUCCESS":
        return False

    for transaction in order_status_res.data.transactions:
        if transaction.status.upper() != "SUCCESS":
            return False

    return True
