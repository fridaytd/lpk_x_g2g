from datetime import datetime
from typing import Final

from app import config, logger
from app.sheet.models import LPKProduct as SheetLPKProduct
from app.lpk.api_client import lpk_api_client
from app.lpk.models import Product as LPKProduct, Category as LPKCategory
from app.lpk.consts import COUNTRY_CODES
from app.shared.utils import formated_datetime, split_list

BATCH_SIZE: Final[int] = 2000
SHEET_ID: Final[str] = config.SHEET_ID
SHEET_NAME: Final[str] = "LPK Products"


def main():
    # print(category_dict)
    # return

    lpk_products: list[LPKProduct] = []
    lpk_categories: list[LPKCategory] = []
    for country_code in COUNTRY_CODES.keys():
        __lpk_products = lpk_api_client.get_all_products(
            country_code=country_code
        ).data.products
        __categories = lpk_api_client.get_categories(
            country_code=country_code
        ).data.categories
        logger.info(
            f"Total product for country code {country_code}: {len(__lpk_products)}"
        )
        lpk_products.extend(__lpk_products)
        lpk_categories.extend(__categories)

    category_dict = {category.code: category for category in lpk_categories}

    logger.info(f"Total product: {len(lpk_products)}")

    sheet_products: list[SheetLPKProduct] = []

    for product in lpk_products:
        sheet_products.append(
            SheetLPKProduct(
                sheet_id=SHEET_ID,
                sheet_name=SHEET_NAME,
                index=len(sheet_products) + 2,
                category=category_dict[product.category_code].name
                if product.category_code in category_dict
                else "",
                **(product.model_dump(mode="json")),
                Note=formated_datetime(datetime.now()),
            )
        )

    logger.info(f"Total valid product: {len(sheet_products)}")

    product_batchs = split_list(sheet_products, BATCH_SIZE)
    logger.info("Sheet updating")
    for i, batch in enumerate(product_batchs):
        logger.info(f"Updating batch: {i + 1}")
        SheetLPKProduct.batch_update(
            sheet_id=SHEET_ID,
            sheet_name=SHEET_NAME,
            list_object=batch,
        )


if __name__ == "__main__":
    main()
