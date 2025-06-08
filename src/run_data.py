from typing import Final

from app import logger, config

from app.sheet.models import G2GTopUpProduct
from app.g2g.api_client import g2g_api_client

from typing import TypedDict


class Attribute(TypedDict):
    attribute_group_id: str
    attribute_id: str
    attribute_name: str
    attribute_value: str


class NewPlatformDataDict(TypedDict):
    STT: int
    service_id: str
    service_name: str
    brand_id: str | None
    brand_name: str
    service_option: str
    product_id: str
    product_name: str
    attributes: list[Attribute]


selling_brand_id: list[str] = [
    "2419de86-6bf0-4b15-8a1c-3a60fd2ee9a2",
    "39415af5-c99f-437f-b49b-8d466b4143cd",
    "44d8846e-3777-4e8b-b932-98866e2389cb",
    "5c77157a-a6a2-49bc-bdfd-f04f40ebaab6",
    "606641ec-65d4-458c-b3ad-38ef1ac95752",
    "72143a89-7265-4de7-ad13-cb9ce5123ab9",
    "7b4d1c30-586f-469a-8b2b-1af42cd87ace",
    "88771df9-1b9e-4ddf-bbef-3a5773c18cf1",
    "97734730-86a6-48b3-87c5-5d429dfd1e5a",
    "9c3e6883-c8b4-4315-ab3d-e4d05c04c974",
    "b0e8dbfc-69fd-45a8-a438-43f11e09eff1",
    "b59c6458-723a-461c-8e29-9b444305c73c",
    "b66cf236-b650-4363-b6b1-de6110edef59",
    "b831cba9-92f3-4870-9e86-a8e0c4c7b82b",
    "c39e8b35-54d5-4c83-9bef-dec7f025cc13",
    "d1ffe265-4835-46d8-9b7f-552674d1db96",
    "d58640b5-60a9-4b8e-8371-a5b7a2536374",
    "e4e0b704-985b-492d-abee-6fa33de45c38",
    "ed694bba-1148-4f84-abdd-7e20d8cf6aef",
    "f6268e73-0dcb-4c0e-9b5d-24607716c87e",
    "ffe5f48c-46a4-4fdf-a5a5-933a27740241",
    "lgc_game_19398",
    "lgc_game_19955",
    "lgc_game_20347",
    "lgc_game_22666",
    "lgc_game_23420",
    "lgc_game_23794",
    "lgc_game_23957",
    "lgc_game_24121",
    "lgc_game_24349",
    "lgc_game_24393",
    "lgc_game_24473",
    "lgc_game_24569",
    "lgc_game_24733",
    "lgc_game_24742",
    "lgc_game_24937",
    "lgc_game_25067",
    "lgc_game_25259",
    "lgc_game_25260",
    "lgc_game_25408",
    "lgc_game_25588",
    "lgc_game_25782",
    "lgc_game_25830",
    "lgc_game_26029",
    "lgc_game_26042",
    "lgc_game_26179",
    "lgc_game_26644",
    "lgc_game_26766",
    "lgc_game_26812",
    "lgc_game_27083",
    "lgc_game_27098",
    "lgc_game_27203",
    "lgc_game_27288",
    "lgc_game_27301",
    "lgc_game_27308",
    "lgc_game_27667",
    "lgc_game_27920",
    "lgc_game_28047",
    "lgc_game_28072",
    "lgc_game_28151",
    "lgc_game_28195",
    "lgc_game_28205",
    "lgc_game_28221",
    "lgc_game_28287",
    "lgc_game_28781",
    "lgc_game_28906",
    "lgc_game_29381",
    "lgc_game_29401",
    "lgc_game_29524",
    "lgc_game_29547",
    "lgc_game_29998",
    "lgc_game_30627",
    "lgc_game_30978",
    "lgc_game_31561",
    "lgc_game_31573",
    "lgc_game_31671",
    "lgc_game_31698",
    "lgc_game_31897",
    "lgc_game_31998",
    "lgc_game_32116",
    "lgc_game_32159",
    "lgc_game_32264",
    "lgc_game_32343",
    "lgc_game_32542",
    "lgc_game_32712",
    "lgc_game_32830",
    "lgc_game_32837",
    "lgc_game_33024",
    "lgc_game_33037",
    "lgc_game_33049",
    "lgc_game_33052",
    "lgc_game_33179",
    "lgc_game_33187",
    "lgc_game_33375",
    "lgc_game_33406",
    "lgc_game_33511",
    "lgc_game_33618",
    "lgc_game_33715",
    "lgc_game_33791",
    "lgc_game_33794",
    "lgc_game_33797",
    "lgc_game_33803",
    "lgc_game_33830",
    "lgc_game_33833",
    "lgc_game_33858",
    "lgc_game_33863",
    "lgc_game_33904",
    "lgc_game_33932",
    "lgc_game_33960",
    "lgc_game_33965",
    "lgc_game_33968",
    "lgc_game_34017",
    "lgc_game_34114",
    "lgc_game_34117",
    "lgc_game_34120",
    "lgc_game_34430",
    "lgc_game_34496",
    "lgc_game_34626",
    "lgc_game_34668",
    "lgc_game_34853",
    "lgc_game_35505",
    "lgc_game_35587",
    "lgc_game_35592",
    "lgc_game_36280",
    "lgc_game_36584",
    "lgc_game_36792",
    "1a329322-d673-402d-b570-a7e8493f4131",
    "251520a0-edae-42f3-9be9-c03a45b5085d",
    "51afb001-d0b2-4816-a32a-9841bf9da98f",
    "551f9ace-293c-4d98-b1ef-b5720edd02a5",
    "66eb8ae2-0ea0-4fb5-9eaa-8dc73abfcba1",
    "734316be-521e-4812-be0b-f46024e31c04",
    "98ba0c6c-5c01-40e0-8d33-1cda5c1026dd",
    "b1c2a95f-aef0-4d1d-b413-41d914653cf5",
    "c4b71bad-9e83-484b-b34e-c9e78320a041",
    "d8573e3e-9adf-4e5a-ac86-f3ed3ccb15bb",
    "f00f4d21-4a57-4921-bfb4-b229e7f58d27",
    "fc96f35b-3f21-407a-8f2d-329213081048",
    "lgc_game_25313",
    "lgc_game_25485",
    "lgc_game_25909",
    "lgc_game_26891",
    "lgc_game_27036",
    "lgc_game_27087",
    "lgc_game_27102",
    "lgc_game_27952",
    "lgc_game_28212",
    "lgc_game_31307",
    "lgc_game_31986",
    "lgc_game_32107",
    "lgc_game_32536",
    "lgc_game_32539",
    "lgc_game_32958",
    "lgc_game_32967",
    "lgc_game_33046",
    "lgc_game_33164",
    "lgc_game_33219",
    "lgc_game_33237",
    "lgc_game_33381",
    "lgc_game_33420",
    "lgc_game_33430",
    "lgc_game_33664",
    "lgc_game_33860",
    "lgc_game_33956",
    "lgc_game_33963",
    "lgc_game_34487",
    "lgc_game_34490",
    "lgc_game_35551",
    "lgc_game_35677",
    "lgc_game_35743",
    "lgc_game_35746",
    "lgc_game_36240",
    "lgc_game_36322",
]

SERVICE_ID: Final[str] = "90015a0f-3983-4953-8368-96ac181d9e92"
SHEET_ID: Final[str] = config.SHEET_ID
SHEET_NAME: Final[str] = "G2GxLapak Mapping"


def update_new_sheet_data():
    logger.info("Getting brands of sevice: TOP UP")

    brand_response = g2g_api_client.get_brand(service_id=SERVICE_ID)
    brands = brand_response.payload.brand_list
    logger.info(f"Total of TOP UP's brand: {len(brands)}")

    item_count = 0

    for brand in brands:
        g2g_top_up_products: list[G2GTopUpProduct] = []

        if brand.brand_id not in selling_brand_id:
            continue

        logger.info(f"Getting {brand.brand_name}'s product")
        product_response = g2g_api_client.get_product(
            service_id=SERVICE_ID,
            brand_id=brand.brand_id,
        )

        products = product_response.payload.product_list
        logger.info(f"Total of {brand.brand_name}'s products: {len(products)}")
        for product in products:
            logger.info(f"Getting {product.product_name}'s attributes")

            attribute_response = g2g_api_client.get_attribute(
                product_id=product.product_id
            )

            for attribute_group in attribute_response.payload.attribute_group_list:
                for attribute in attribute_group.attribute_list:
                    if len(attribute.sub_attribute_list) > 0:
                        for sub_attribute in attribute.sub_attribute_list:
                            g2g_top_up_products.append(
                                G2GTopUpProduct(
                                    sheet_id=SHEET_ID,
                                    sheet_name=SHEET_NAME,
                                    index=item_count + 2,
                                    STT=item_count + 1,
                                    service_id=SERVICE_ID,
                                    service_name="Top Up",
                                    brand_id=brand.brand_id,
                                    brand_name=brand.brand_name,
                                    service_option=attribute_group.attribute_group_name,
                                    product_id=product.product_id,
                                    product_name=product.product_name,
                                    attribute_group_id=attribute_group.attribute_group_id,
                                    attribute_name=attribute_group.attribute_group_name,
                                    attribute_id=attribute.attribute_id,
                                    attribute_value=attribute.attribute_name,
                                    sub_attribute_id=sub_attribute.attribute_id,
                                    sub_attribute_value=sub_attribute.attribute_name,
                                )
                            )
                            item_count += 1
                    else:
                        g2g_top_up_products.append(
                            G2GTopUpProduct(
                                sheet_id=SHEET_ID,
                                sheet_name=SHEET_NAME,
                                index=item_count + 2,
                                STT=item_count + 1,
                                service_id=SERVICE_ID,
                                service_name="Top Up",
                                brand_id=brand.brand_id,
                                brand_name=brand.brand_name,
                                service_option=attribute_group.attribute_group_name,
                                product_id=product.product_id,
                                product_name=product.product_name,
                                attribute_group_id=attribute_group.attribute_group_id,
                                attribute_name=attribute_group.attribute_group_name,
                                attribute_id=attribute.attribute_id,
                                attribute_value=attribute.attribute_name,
                            )
                        )
                        item_count += 1

        G2GTopUpProduct.batch_update(
            sheet_id=SHEET_ID,
            sheet_name=SHEET_NAME,
            list_object=g2g_top_up_products,
        )
