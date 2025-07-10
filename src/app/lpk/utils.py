from .api_client import lpk_api_client
from .models import Product
from .consts import COUNTRY_CODES


def to_product_dict(products: list[Product]) -> dict[str, Product]:
    return {product.code: product for product in products}


def get_lowest_price_from_list_code(codes: list[str]) -> Product | None:
    products: list[Product] = []
    for country_code in COUNTRY_CODES:
        products.extend(
            lpk_api_client.get_all_products(country_code=country_code).data.products,
        )

    min_price: int = 99999999999999999999999
    # min_code: str = products[0].code
    min_product: Product | None = None
    for product in products:
        if product.code in codes and product.status == "available":
            if product.price < min_price:
                min_price = product.price
                # min_code = product.code
                min_product = product

    return min_product
