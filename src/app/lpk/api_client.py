from typing import Final

import httpx

from .. import config
from . import logger
from .models import (
    ProductResponse,
    Response,
    CategoryResponse,
    OrderPayload,
    CreatedOrderResposne,
    OrderStatusResponse,
    FXRateReponse,
)
from ..shared.decorators import retry_on_fail

LPK_BASE_URL: Final[str] = "https://www.lapakgaming.com"


class LpkAPIClient:
    def __init__(self) -> None:
        self.client = httpx.Client()
        self.base_url = LPK_BASE_URL

    @retry_on_fail()
    def get_categories(self, country_code: str = "id") -> Response[CategoryResponse]:
        logger.info("API Get all product")

        headers = {
            "Authorization": f"Bearer {config.LAPAK_API_KEY}",
        }

        res = self.client.get(
            f"{self.base_url}/api/category?country_code={country_code}",
            headers=headers,
        )

        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            logger.info(res.text)
            res.raise_for_status()

        return Response[CategoryResponse].model_validate(res.json())

    @retry_on_fail()
    def get_products(self, category_code: str, country_code: str = "id") -> None:
        logger.info("API Get all product")

        headers = {
            "Authorization": f"Bearer {config.LAPAK_API_KEY}",
        }

        res = self.client.get(
            f"{self.base_url}/api/product?category_code={category_code}&country_code={country_code}",
            headers=headers,
        )

        try:
            res.raise_for_status()
            print(res.json())
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            logger.info(res.text)
            res.raise_for_status()

        # return Response[CategoryResponse].model_validate(res.json())

    @retry_on_fail()
    def get_all_products(self, country_code: str = "id") -> Response[ProductResponse]:
        logger.info("API Get all product")

        headers = {
            "Authorization": f"Bearer {config.LAPAK_API_KEY}",
        }

        res = self.client.get(
            f"{self.base_url}/api/all-products?country_code={country_code}",
            headers=headers,
        )

        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            logger.info(res.text)
            res.raise_for_status()

        return Response[ProductResponse].model_validate(res.json())

    @retry_on_fail()
    def create_order(self, order: OrderPayload) -> CreatedOrderResposne:
        logger.info("API Create order")

        headers = {
            "Authorization": f"Bearer {config.LAPAK_API_KEY}",
        }

        res = self.client.post(
            f"{self.base_url}/api/order",
            headers=headers,
            json=order.model_dump(mode="json"),
        )

        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            logger.info(res.text)
            res.raise_for_status()

        return CreatedOrderResposne.model_validate(res.json())

    @retry_on_fail()
    def get_order_status(self, tid: str) -> OrderStatusResponse:
        logger.info("API get order status")

        headers = {
            "Authorization": f"Bearer {config.LAPAK_API_KEY}",
        }

        res = self.client.post(
            f"{self.base_url}/api/order_status?tid={tid}",
            headers=headers,
        )

        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            logger.info(res.text)
            res.raise_for_status()

        return OrderStatusResponse.model_validate(res.json())

    @retry_on_fail()
    def get_fx_rate(
        self, from_currency: str = "IDR", to_currency: str = "USD"
    ) -> Response[FXRateReponse]:
        logger.info("API Get FX Rate Response")

        headers = {
            "Authorization": f"Bearer {config.LAPAK_API_KEY}",
        }

        res = self.client.get(
            f"{self.base_url}/api/fx-rate.php?from_currency={from_currency}&to_currency={to_currency}",
            headers=headers,
        )

        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            logger.info(res.text)
            res.raise_for_status()

        return Response[FXRateReponse].model_validate(res.json())


lpk_api_client = LpkAPIClient()
