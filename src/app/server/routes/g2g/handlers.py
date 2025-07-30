from typing import Final

from fastapi import BackgroundTasks

from .models import APIDeliveryPayload
from .enums import DeliveryMethodCode

from . import logger
from ...models import ProductMap, G2GProductMapping, ProviderMode
from ...background_tasks import (
    check_lpk_order_status_cron_job,
    check_eli_order_status_cron_job,
)
from ...utils import load_product_mapping_and_rates_from_sheet

from app.g2g.api_client import g2g_api_client
from app.g2g.models import GetOfferResponse
from app.elite.api_client import elitedias_api_client
from app.lpk.api_client import lpk_api_client
from app.lpk.utils import get_lowest_price_from_list_code
from app.lpk.models import Product as LpkProduct
from app.shared.utils import (
    load_lapak_delivery_method_list_mapping,
    load_eli_delivery_method_list_mapping,
)
from app.lpk.models import OrderPayload
from app.shared.models import LpkStoreModel, EliStoreModel
from app.sheet.models import LogToSheet
from app.shared.utils import afunc_retry

from app import kv_store, config, eli_kv_store

DEFAULT_KEY: Final[str] = "DEFAULT_KEY"


async def api_delivery_hanlder(
    payload: APIDeliveryPayload,
    background_tasks: BackgroundTasks,
):
    # Check if delivery method code is DIRECT TOP UP
    if (
        payload.delivery_summary.delivery_method_code
        is DeliveryMethodCode.DIRECT_TOP_UP
    ):
        await handle_direct_topup_api_delivery(payload, background_tasks)
    return {"message": "ok"}


def map_delivery_method_list(
    payload: APIDeliveryPayload,
    product_delivery_method_list_mapping: dict,
) -> dict:
    mapping_payload: dict = {}

    for delivery_method_list in payload.delivery_summary.delivery_method_list:
        for (
            payload_key,
            map_attribute_group_id,
        ) in product_delivery_method_list_mapping.items():
            # This case handle for no need to mapping value
            if isinstance(map_attribute_group_id, str):
                if delivery_method_list.attribute_group_id == map_attribute_group_id:
                    if delivery_method_list.value:
                        mapping_payload[payload_key] = delivery_method_list.value
                    else:
                        mapping_payload[payload_key] = (
                            delivery_method_list.attribute_value
                        )
            if isinstance(map_attribute_group_id, dict):
                for attribute_group_id, value_mapping in map_attribute_group_id.items():
                    # This case handle for Default Key
                    if DEFAULT_KEY == attribute_group_id:
                        mapping_payload[payload_key] = value_mapping

                    # This case handle for mapping value
                    if delivery_method_list.attribute_group_id == attribute_group_id:
                        if delivery_method_list.value in value_mapping:
                            mapping_payload[payload_key] = value_mapping[
                                delivery_method_list.value
                            ]
                        elif delivery_method_list.attribute_value in value_mapping:
                            mapping_payload[payload_key] = value_mapping[
                                delivery_method_list.attribute_value
                            ]

    return mapping_payload


async def eli_delivery(
    payload: APIDeliveryPayload,
    background_tasks: BackgroundTasks,
    offer: GetOfferResponse,
    product_map: ProductMap,
    SGD_to_USD_rate: float,
    eli_delivery_method_list_mapping: dict,
    log_to_sheet: LogToSheet,
):
    logger.info("Delivery with Elitedias")
    log_to_sheet.provider = "Elitedias"
    logger.info(f"Supported product id: {offer.product_id}")

    if (
        not product_map["elitedias"]
        or not product_map["elitedias"]["game"]
        or not product_map["elitedias"]["denom"]
    ):
        logger.info(
            f"Missing mapping product G2G - Elitedias for product: {offer.product_id}"
        )
        log_to_sheet.append_note(
            f"Missing mapping product G2G - Elitedias for product: {offer.product_id}"
        )
        log_to_sheet.update
        return

    log_to_sheet.provider_product_id = (
        f"{product_map['elitedias']['game']} | {product_map['elitedias']['denom']}"
    )
    logger.info(
        f"Getting elitedias product price | game: {product_map['elitedias']['game']}, denom: {product_map['elitedias']['denom']}"
    )
    elite_unit_price: float | None = None
    try:
        elite_unit_price = await afunc_retry(elitedias_api_client.get_price)(
            game=product_map["elitedias"]["game"],
            denom=product_map["elitedias"]["denom"],
        )
    except Exception:
        pass

    if elite_unit_price:
        log_to_sheet.buy_price_in_provider_curency = str(
            payload.purchased_qty * elite_unit_price
        )
        log_to_sheet.buy_price_use = str(
            payload.purchased_qty * elite_unit_price * SGD_to_USD_rate
        )
    else:
        log_to_sheet.buy_price_in_provider_curency = "Can not retrieve"
        log_to_sheet.buy_price_use = "Can not retrieve"
    eli_topup_payload: dict = {}
    # Fill game and demon
    eli_topup_payload.update(product_map["elitedias"])

    if offer.product_id not in eli_delivery_method_list_mapping:
        logger.info(
            f"Missing delivery method list mappping G2G - Elitedias for product: {offer.product_id}"
        )
        log_to_sheet.append_note(
            f"Missing delivery method list mappping G2G - Elitedias for product: {offer.product_id}"
        )
        log_to_sheet.update()
        return

    # Find to fill userid and (serverid)
    map_eli_delivery_method_list_dict = map_delivery_method_list(
        payload=payload,
        product_delivery_method_list_mapping=eli_delivery_method_list_mapping[
            offer.product_id
        ],
    )

    if map_eli_delivery_method_list_dict:
        eli_topup_payload.update(map_eli_delivery_method_list_dict)

    logger.info(f"Updated elitedias topup payload: {eli_topup_payload}")
    log_to_sheet.append_note(f"Order payload: {eli_topup_payload}")

    eli_order_ids: list[str] = []

    failed_reason: str | None = None
    # Create offer to Elitedias
    retry_time: int = 0
    while (
        len(eli_order_ids) < payload.purchased_qty
        and retry_time < 2 + payload.purchased_qty
    ):
        try:
            create_topup_res = await afunc_retry(
                elitedias_api_client.create_topup, sleep_interval=5
            )(eli_topup_payload)

            if create_topup_res.order_id is None or (
                create_topup_res.status and "success" not in create_topup_res.status
            ):
                logger.info(
                    f"Failed to create Elitedias. Reason: {create_topup_res.message}"
                )
                failed_reason = create_topup_res.message

            else:
                eli_order_ids.append(create_topup_res.order_id)
        except Exception as e:
            logger.exception(e)

        retry_time += 1

    if len(eli_order_ids) == payload.purchased_qty:
        eli_kv_store.set(
            key=payload.order_id,
            value=EliStoreModel(
                g2g_order_id=payload.order_id,
                eli_order_ids=eli_order_ids,
                delivery_id=payload.delivery_summary.delivery_id,
                quantity=payload.purchased_qty,
                log_index=log_to_sheet.index,
            ),
        )
        background_tasks.add_task(check_eli_order_status_cron_job, payload.order_id)
        log_to_sheet.provider_order_ids = "\n".join(eli_order_ids)
        logger.info(
            f"Successfully create order to Elitedias with G2G order id: {payload.order_id}"
        )
        log_to_sheet.append_note(
            f"Successfully create order to Elitedias with G2G order id: {payload.order_id}"
        )
    else:
        logger.info(
            f"FAILED create order to Elitedias with G2G order id: {payload.order_id}"
        )
        log_to_sheet.append_note(
            f"FAILED create order to Elitedias with G2G order id: {payload.order_id}. Failed reason: {failed_reason}"
        )

    log_to_sheet.update()
    return


def lapak_delivery(
    payload: APIDeliveryPayload,
    background_tasks: BackgroundTasks,
    offer: GetOfferResponse,
    product_map: ProductMap,
    IDR_to_USD_rate: float,
    lapak_delivery_method_list_mapping: dict,
    log_to_sheet: LogToSheet,
    min_price_product: LpkProduct | None = None,
):
    logger.info("Delivery with Lapakgaming")
    log_to_sheet.provider = "Lapakgaming"
    logger.info(f"Supported product id: {offer.product_id}")

    if min_price_product is None and product_map["lapakgaming"]:
        product_codes = product_map["lapakgaming"].split(",")
        min_price_product = get_lowest_price_from_list_code(product_codes)

    if min_price_product is None:
        # Handle when min_price_product is None
        logger.info(
            f"Can not find min price lapakgaming product for product: {offer.product_id}"
        )
        log_to_sheet.append_note(
            f"Can not find min price lapakgaming product for product: {offer.product_id}"
        )
        log_to_sheet.update()
        return

    log_to_sheet.buy_price_in_provider_curency = str(
        min_price_product.price * payload.purchased_qty
    )
    log_to_sheet.buy_price_use = str(
        min_price_product.price * payload.purchased_qty * IDR_to_USD_rate
    )
    log_to_sheet.provider_product_id = min_price_product.code

    if offer.product_id not in lapak_delivery_method_list_mapping:
        logger.info(
            f"Missing delivery method list mappping G2G - Lapakgaming for product: {offer.product_id}"
        )
        log_to_sheet.append_note(
            f"Missing delivery method list mappping G2G - EliLapakgamingtedias for product: {offer.product_id}"
        )
        log_to_sheet.update()

    map_lpk_delivery_method_list = map_delivery_method_list(
        payload,
        lapak_delivery_method_list_mapping[offer.product_id],
    )

    lpk_order_payload = OrderPayload.model_validate(
        {
            "count_order": payload.purchased_qty,
            "product_code": min_price_product.code,
            **map_lpk_delivery_method_list,
        }
    )
    logger.info(f"""Payload: {lpk_order_payload.model_dump_json()}""")
    log_to_sheet.append_note(f"Order payload: {lpk_order_payload.model_dump_json()}")
    try:
        lpk_create_order_res = lpk_api_client.create_order(lpk_order_payload)
    except Exception as e:
        logger.exception(e)
        logger.info("Fail to create lpk_offer")

    if lpk_create_order_res.data:
        kv_store.set(
            lpk_create_order_res.data.tid,
            LpkStoreModel(
                order_id=payload.order_id,
                delivery_id=payload.delivery_summary.delivery_id,
                quantity=lpk_order_payload.count_order,
                log_index=log_to_sheet.index,
            ),
        )
        background_tasks.add_task(
            check_lpk_order_status_cron_job,
            lpk_create_order_res.data.tid,
        )
        log_to_sheet.provider_order_ids = lpk_create_order_res.data.tid
        log_to_sheet.append_note(
            f"Successfully create order to Lapakgaming with G2G order id: {payload.order_id}"
        )
    else:
        logger.info("Fail to create lpk_offer")
        log_to_sheet.append_note(
            f"FAILED create order to Lapakgaming with G2G order id: {payload.order_id}"
        )

    log_to_sheet.update()


def find_product_map(
    offer: GetOfferResponse,
    product_mapping: G2GProductMapping,
) -> ProductMap | None:
    if offer.product_id in product_mapping:
        for attribute in offer.offer_attributes:
            if (
                attribute.attribute_group_id in product_mapping[offer.product_id]
                and attribute.attribute_id
                in product_mapping[offer.product_id][attribute.attribute_group_id]
            ):
                return product_mapping[offer.product_id][attribute.attribute_group_id][
                    attribute.attribute_id
                ]

    return None


async def handle_direct_topup_api_delivery(
    payload: APIDeliveryPayload,
    background_tasks: BackgroundTasks,
):
    logger.info(f"Handling Direct top up for order ID: {payload.order_id}")
    log_to_sheet = LogToSheet.register_note_row()
    log_to_sheet.g2g_order_id = payload.order_id
    log_to_sheet.g2g_offer_id = payload.offer_id

    # Load product mapppings and curency exchange rate
    logger.info("Loading product mapppings and curency exchange rate")
    product_mapping, IDR_to_USD_rate, SGD_to_USD_rate = (
        load_product_mapping_and_rates_from_sheet(
            sheet_id=config.SHEET_ID,
            sheet_name=config.MAPPING_SHEET_NAME,
            start_row=2,
        )
    )

    log_to_sheet.append_note(
        f"IDR -> USE rate: {IDR_to_USD_rate:.10f} | SGD -> USD rate: {SGD_to_USD_rate}"
    )

    # Load delivery method list mapping for Lapakgaming
    lapak_delivery_method_list_mapping = load_lapak_delivery_method_list_mapping()

    # Load delivery method list mapping for Elitedias
    eli_delivery_method_list_mapping = load_eli_delivery_method_list_mapping()

    # Get offer by offer id
    logger.info(f"Getting offer in for with offer ID: {payload.offer_id}")
    offer = g2g_api_client.get_offer(payload.offer_id).payload
    logger.info(f"Offer Title: {offer.title}")
    log_to_sheet.g2g_product_id = offer.product_id

    # Get product map
    product_map = find_product_map(offer, product_mapping)
    if product_map is None:
        # Handle product map in None

        log_to_sheet.append_note(
            f"Can not find product mapping for product ID: {offer.product_id}"
        )
        log_to_sheet.update()
        return

    log_to_sheet.sell_price = str(payload.purchased_qty * offer.unit_price)
    log_to_sheet.sell_quantity = str(payload.purchased_qty)

    if product_map["provider_mode"] == ProviderMode.ELITEDIAS.value:
        await eli_delivery(
            payload,
            background_tasks,
            offer,
            product_map,
            SGD_to_USD_rate,
            eli_delivery_method_list_mapping,
            log_to_sheet,
        )
    elif product_map["provider_mode"] == ProviderMode.LAPAKGAMING.value:
        lapak_delivery(
            payload,
            background_tasks,
            offer,
            product_map,
            IDR_to_USD_rate,
            lapak_delivery_method_list_mapping,
            log_to_sheet,
            None,
        )
    elif product_map["provider_mode"] == ProviderMode.AUTO.value:
        if (
            not product_map["elitedias"]
            or not product_map["elitedias"]["game"]
            or not product_map["elitedias"]["denom"]
        ):
            lapak_delivery(
                payload,
                background_tasks,
                offer,
                product_map,
                IDR_to_USD_rate,
                lapak_delivery_method_list_mapping,
                log_to_sheet,
                None,
            )
        elif not product_map["lapakgaming"]:
            await eli_delivery(
                payload,
                background_tasks,
                offer,
                product_map,
                SGD_to_USD_rate,
                eli_delivery_method_list_mapping,
                log_to_sheet,
            )
        else:
            min_lpk_product = get_lowest_price_from_list_code(
                product_map["lapakgaming"].split(",")
            )

            eli_denominations = await elitedias_api_client.get_denominations(
                product_map["elitedias"]["game"]
            )
            eli_price = eli_denominations[product_map["elitedias"]["denom"]]

            if not min_lpk_product:
                await eli_delivery(
                    payload,
                    background_tasks,
                    offer,
                    product_map,
                    SGD_to_USD_rate,
                    eli_delivery_method_list_mapping,
                    log_to_sheet,
                )
            else:
                logger.info(f"Lapak price: {min_lpk_product.price} IDR")
                min_lpk_usd_price = min_lpk_product.price * IDR_to_USD_rate
                logger.info(f"Elite price: {eli_price} SGD")
                eli_usd_price = float(eli_price) * SGD_to_USD_rate
                logger.info(
                    f"LAPAK Price: {min_lpk_usd_price} USD | ELITE Price: {eli_usd_price} USD"
                )
                log_to_sheet.append_note(
                    f"LAPAK Price: {min_lpk_usd_price} USD | ELITE Price: {eli_usd_price} USD"
                )
                if min_lpk_usd_price < eli_usd_price:
                    lapak_delivery(
                        payload,
                        background_tasks,
                        offer,
                        product_map,
                        IDR_to_USD_rate,
                        lapak_delivery_method_list_mapping,
                        log_to_sheet,
                        min_lpk_product,
                    )
                else:
                    await eli_delivery(
                        payload,
                        background_tasks,
                        offer,
                        product_map,
                        SGD_to_USD_rate,
                        eli_delivery_method_list_mapping,
                        log_to_sheet,
                    )
