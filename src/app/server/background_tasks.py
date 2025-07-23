import asyncio
import time

from typing import Final

from datetime import datetime


from app.lpk.api_client import lpk_api_client
from app.g2g.api_client import g2g_api_client
from app.elite.api_client import elitedias_api_client
from app.g2g.models import PatchDeliveryPayload
from app import logger, kv_store, eli_kv_store
from app.shared.models import StoreModel, EliStoreModel
from app.shared.utils import afunc_retry
from app.sheet.models import LogToSheet


from .routes.lapak.utiles import is_success_order

ELI_SUCCESS_KEY: Final[str] = "success"


def check_lpk_order_status_cron_job(tid: str):
    retry_time: int = 0
    while True:
        if retry_time > 3:
            return
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
                LogToSheet.write_log(
                    f"Delivery success for order id: {mapped_order.order_id}"
                )

                kv_store.delete(tid)
                return

            time.sleep(10 * 60)  # Sleep in 10 minutes
        except Exception as e:
            retry_time += 1
            time.sleep(10 * 60)
            logger.exception(e)


async def check_eli_order_status_cron_job(g2g_order_id: str) -> None:
    async def __inner_function(g2g_order_id: str) -> None:
        while True:
            logger.info(
                f"Background task to trach elitedias orders is running with G2G order id: {g2g_order_id}"
            )
            mapped_order: EliStoreModel | None = eli_kv_store.get(g2g_order_id)

            if mapped_order is None:
                return
            successful_order_ids: list[str] = []
            for eli_order_id in mapped_order.eli_order_ids:
                track_order_res = await elitedias_api_client.track_order(eli_order_id)
                logger.info(track_order_res)
                if ELI_SUCCESS_KEY in track_order_res.order_status:
                    successful_order_ids.append(eli_order_id)

            for success_order_id in successful_order_ids:
                if success_order_id in mapped_order.eli_order_ids:
                    mapped_order.eli_order_ids.remove(success_order_id)
                    eli_kv_store.set(g2g_order_id, mapped_order)

            if len(mapped_order.eli_order_ids) == 0:
                g2g_api_client.patch_delivery_order(
                    order_id=g2g_order_id,
                    delivery_id=mapped_order.delivery_id,
                    payload=PatchDeliveryPayload(
                        delivered_qty=mapped_order.quantity,
                        delivered_at=int(
                            datetime.now().timestamp(),
                        ),
                    ),
                )
                LogToSheet.write_log(f"Delivery success for order id: {g2g_order_id}")
                eli_kv_store.delete(g2g_order_id)
                return

            await asyncio.sleep(2 * 60)  # Sleep for 2 minutes

    await afunc_retry(__inner_function)(g2g_order_id)
