from typing import Literal

from fastapi import BackgroundTasks

from .models import APIDeliveryPayload
from .enums import DeliveryMethodCode
from ....sheet.models import LogToSheet
from . import logger

from ...background_tasks import check_lpk_order_status_cron_job

from app.g2g.api_client import g2g_api_client
from app.lpk.api_client import lpk_api_client
from app.lpk.utils import get_lowest_price_from_list_code
from app.shared.utils import load_product_mapping, load_delivery_method_list_mapping
from app.lpk.models import OrderPayload
from app.shared.models import StoreModel

from app import kv_store


def map_delivery_method_list(
    payload: APIDeliveryPayload,
    product_delivery_method_list_mapping: dict,
    key: Literal["user_id", "additional_id"],
) -> str | None:
    for delivery_method_list in payload.delivery_summary.delivery_method_list:
        if key in product_delivery_method_list_mapping:
            _mapping = product_delivery_method_list_mapping[key]
            if isinstance(_mapping, str):
                if _mapping == delivery_method_list.attribute_group_id:
                    if delivery_method_list.value:
                        return delivery_method_list.value
                    else:
                        return delivery_method_list.attribute_value
            elif isinstance(_mapping, dict):
                if delivery_method_list.attribute_group_id in _mapping:
                    _value_mapping = _mapping[delivery_method_list.attribute_group_id]
                    if delivery_method_list.value in _value_mapping:
                        return _value_mapping[delivery_method_list.value]
                    elif delivery_method_list.attribute_value in _value_mapping:
                        return _value_mapping[delivery_method_list.attribute_value]

    return None


def api_delivery_hanlder(
    payload: APIDeliveryPayload,
    background_tasks: BackgroundTasks,
):
    # Check if delivery method code is DIRECT TOP UP
    if (
        payload.delivery_summary.delivery_method_code
        is DeliveryMethodCode.DIRECT_TOP_UP
    ):
        logger.info("Handling Direct top up")
        product_mapping = load_product_mapping()
        delivery_method_list_mapping = load_delivery_method_list_mapping()

        # Get offer by offer id
        offer = g2g_api_client.get_offer(payload.offer_id).payload
        logger.info(f"Offer ID: {offer.offer_id} | Title: {offer.title}")
        log_message: str = f"Offer ID: {offer.offer_id} | Title: {offer.title}\n"

        # Mapping G2G product with Lapak
        if (
            offer.product_id in product_mapping
            and offer.product_id in delivery_method_list_mapping
        ):
            logger.info(f"Supported product id: {offer.product_id}")
            log_message += f"Supported product id: {offer.product_id}\n"

            valided_lpk_product_codes_str: str | None = None
            user_id: str | None = None
            additional_id: str | None = None

            for attribute in offer.offer_attributes:
                if (
                    attribute.attribute_group_id in product_mapping[offer.product_id]
                    and attribute.attribute_id
                    in product_mapping[offer.product_id][attribute.attribute_group_id]
                ):
                    logger.info(
                        f"Valid lapak product code: {product_mapping[offer.product_id][attribute.attribute_group_id][attribute.attribute_id]}"
                    )
                    log_message += f"Valid lapak product code: {product_mapping[offer.product_id][attribute.attribute_group_id][attribute.attribute_id]}\n"
                    valided_lpk_product_codes_str = product_mapping[offer.product_id][
                        attribute.attribute_group_id
                    ][attribute.attribute_id]

            product_delivery_method_list_mapping = delivery_method_list_mapping[
                offer.product_id
            ]

            user_id = map_delivery_method_list(
                payload=payload,
                product_delivery_method_list_mapping=product_delivery_method_list_mapping,
                key="user_id",
            )

            logger.info(f"User id: {user_id}")
            log_message += f"User id: {user_id}\n"

            additional_id = map_delivery_method_list(
                payload=payload,
                product_delivery_method_list_mapping=product_delivery_method_list_mapping,
                key="additional_id",
            )

            logger.info(f"Additional id: {additional_id}")
            log_message += f"Additional id: {additional_id}\n"

            # Find the lowest lapak product
            if valided_lpk_product_codes_str:
                min_lpk_product = get_lowest_price_from_list_code(
                    [code.strip() for code in valided_lpk_product_codes_str.split(",")]
                )

                if min_lpk_product:
                    logger.info(f"Lowest product: {min_lpk_product.model_dump_json()}")
                    log_message += (
                        f"Lowest product: {min_lpk_product.model_dump_json()}\n"
                    )

                    # Only delivery when g2g offer price < lapak product price
                    fx_rate = lpk_api_client.get_fx_rate()

                    idr_g2g_offer_price = offer.unit_price * fx_rate.data.buy_rate
                    logger.info(
                        f"Price: IDR G2G: {idr_g2g_offer_price} | LPK: {min_lpk_product.price}"
                    )
                    log_message += f"Price: IDR G2G: {idr_g2g_offer_price} | LPK: {min_lpk_product.price}\n"

                    order_payload = OrderPayload.model_validate(
                        {
                            "user_id": user_id,
                            "additional_id": additional_id,
                            "count_order": payload.purchased_qty,
                            "product_code": min_lpk_product.code,
                        }
                    )
                    logger.info(f"""Payload: {order_payload.model_dump_json()}""")
                    try:
                        lpk_create_order_res = lpk_api_client.create_order(
                            order_payload
                        )
                    except Exception as e:
                        logger.exception(e)
                        logger.info("Fail to create lpk_offer")
                        log_message += "Fail to create lpk_offer\n"

                    if lpk_create_order_res.data:
                        kv_store.set(
                            lpk_create_order_res.data.tid,
                            StoreModel(
                                order_id=payload.order_id,
                                delivery_id=payload.delivery_summary.delivery_id,
                                quantity=order_payload.count_order,
                            ),
                        )
                        background_tasks.add_task(
                            check_lpk_order_status_cron_job,
                            lpk_create_order_res.data.tid,
                        )
                    else:
                        logger.info("Fail to create lpk_offer")
                        log_message += "Fail to create lpk_offer\n"

                else:
                    logger.info("Product in lapak is not available")
                    log_message += "Product in lapak is not available"

        LogToSheet.write_log(log_message)
    return {"message": "ok"}
