from .models import APIDeliveryPayload
from .enums import DeliveryMethodCode
from ....sheet.models import LogToSheet
from . import logger

from app.g2g.api_client import g2g_api_client
from app.lpk.api_client import lpk_api_client
from app.shared.utils import load_product_mapping, load_delivery_method_list_mapping
from app.lpk.models import OrderPayload


def api_delivery_hanlder(
    payload: APIDeliveryPayload,
):
    logger.info(payload.model_dump_json())
    if (
        payload.delivery_summary.delivery_method_code
        is DeliveryMethodCode.DIRECT_TOP_UP
    ):
        logger.info("Handling Direct top up")
        product_mapping = load_product_mapping()
        delivery_method_list_mapping = load_delivery_method_list_mapping()

        offer = g2g_api_client.get_offer(payload.offer_id).payload

        logger.info(offer.model_dump_json())

        if (
            offer.product_id in product_mapping
            and offer.product_id in delivery_method_list_mapping
        ):
            logger.info(f"Supported product id: {offer.product_id}")

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
                    valided_lpk_product_codes_str = product_mapping[offer.product_id][
                        attribute.attribute_group_id
                    ][attribute.attribute_id]

            for delivery_method_list in payload.delivery_summary.delivery_method_list:
                if (
                    "user_id" in delivery_method_list_mapping[offer.product_id]
                    and delivery_method_list_mapping[offer.product_id]["user_id"]
                    == delivery_method_list.attribute_group_id
                ):
                    logger.info(
                        f"User id: {delivery_method_list.attribute_value if delivery_method_list.attribute_value else delivery_method_list.value}"
                    )
                    user_id = (
                        delivery_method_list.attribute_value
                        if delivery_method_list.attribute_value
                        else delivery_method_list.value
                    )

                if (
                    "additional_id" in delivery_method_list_mapping[offer.product_id]
                    and delivery_method_list_mapping[offer.product_id]["additional_id"]
                    == delivery_method_list.attribute_group_id
                ):
                    logger.info(
                        f"Additional id: {delivery_method_list.attribute_value if delivery_method_list.attribute_value else delivery_method_list.value}"
                    )
                    additional_id = (
                        delivery_method_list.attribute_value
                        if delivery_method_list.attribute_value
                        else delivery_method_list.value
                    )

            order_payload = OrderPayload.model_validate(
                {
                    "user_id": user_id,
                    "addtional_id": additional_id,
                    "count_order": payload.purchased_qty,
                    "product_code": valided_lpk_product_codes_str.split(",")[0]
                    if valided_lpk_product_codes_str
                    else "",
                }
            )
            logger.info(f"""Payload: {order_payload.model_dump_json()}""")
            res = lpk_api_client.create_order(order_payload)

            logger.info(res.model_dump_json())

        # LogToSheet.write_log(payload.model_dump_json())

    return {"message": "ok"}
