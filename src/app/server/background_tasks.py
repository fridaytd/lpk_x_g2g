import time

from datetime import datetime


from app.lpk.api_client import lpk_api_client
from app.g2g.api_client import g2g_api_client
from app.g2g.models import PatchDeliveryPayload
from app import logger, kv_store
from app.shared.models import StoreModel


from .routes.lapak.utiles import is_success_order


def check_lpk_order_status_cron_job(tid: str):
    while True:
        try:
            logger.info(
                f"Background task check lpk order status is running with tid: {tid}"
            )
            mapped_order: StoreModel | None = kv_store.get(tid)
            if mapped_order is None:
                return
            order_status_res = lpk_api_client.get_order_status(tid=tid)
            if is_success_order(order_status_res):
                g2g_api_client.patch_delivery_order(
                    order_id=mapped_order.order_id,
                    delivery_id=mapped_order.delivery_id,
                    payload=PatchDeliveryPayload(
                        delivered_qty=mapped_order.quantity,
                        delivered_at=int(
                            datetime.now().timestamp(),
                        ),
                    ),
                )
                kv_store.delete(tid)
                return

            time.sleep(10 * 10)  # Sleep in 10 minutes
        except Exception as e:
            logger.exception(e)
