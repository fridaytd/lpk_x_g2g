import hashlib
import hmac

from datetime import datetime

from typing import cast
from httpx import Client, HTTPStatusError

from .. import config
from . import logger
from .consts import G2G_API_URL, G2G_API_VERSION
from .models import (
    AuthorizationHeader,
    ResponseModel,
    ServicePayload,
    BrandPayLoad,
    ProductPayload,
    AttributePayload,
    CreateOfferRequest,
    CreateOfferResponse,
    DeleteOfferResponse,
    Order,
    PatchDeliveryPayload,
    PathchDeliveryResponse,
    GetOfferResponse,
)
from .exceptions import G2GAPIError
from ..shared.decorators import retry_on_fail


class G2GAPIClient:
    def __init__(self) -> None:
        self.http_client = Client(
            base_url=f"{G2G_API_URL}",
            timeout=20,
        )

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def generate_authorization_header(
        self,
        canonical_url: str,
    ) -> AuthorizationHeader:
        secret_key = config.G2G_SECRET_KEY
        api_key = config.G2G_API_KEY  # Your API Key
        user_id = config.G2G_ACCOUNT_ID  # Your User ID
        timestamp = str(int(datetime.now().timestamp()))  # g2g-timestamp

        canonical_string = canonical_url + api_key + user_id + str(timestamp)
        signature = hmac.new(
            key=bytes(secret_key.encode("utf8")),
            msg=bytes(canonical_string.encode("utf8")),
            digestmod=hashlib.sha256,
        ).hexdigest()

        authorization_header: AuthorizationHeader = {
            "g2g-api-key": config.G2G_API_KEY,
            "g2g-userid": config.G2G_ACCOUNT_ID,
            "g2g-signature": signature,
            "g2g-timestamp": timestamp,
            "Content-Type": "application/json",
        }
        return authorization_header

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def get_service(
        self,
    ) -> ResponseModel[ServicePayload]:
        canonical_url = f"/{G2G_API_VERSION}/services"
        headers = self.generate_authorization_header(canonical_url=canonical_url)

        res = self.http_client.get(canonical_url, headers=cast(dict[str, str], headers))
        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[ServicePayload].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def get_brand(
        self,
        service_id: str,
    ) -> ResponseModel[BrandPayLoad]:
        canonical_url = f"/{G2G_API_VERSION}/services/{service_id}/brands"
        headers = self.generate_authorization_header(canonical_url=canonical_url)

        res = self.http_client.get(canonical_url, headers=cast(dict[str, str], headers))

        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[BrandPayLoad].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def get_product(
        self,
        category_id: str | None = None,
        service_id: str | None = None,
        brand_id: str | None = None,
    ) -> ResponseModel[ProductPayload]:
        if category_id or (service_id and brand_id):
            query_params = {}
            if category_id:
                query_params["category_id"] = category_id

            if service_id:
                query_params["service_id"] = service_id

            if brand_id:
                query_params["brand_id"] = brand_id

            canonical_url = f"/{G2G_API_VERSION}/products"
            headers = self.generate_authorization_header(canonical_url)

            res = self.http_client.get(
                canonical_url,
                headers=cast(dict[str, str], headers),
                params=query_params,
            )
            try:
                res.raise_for_status()
            except HTTPStatusError:
                print(res.text)
                raise G2GAPIError(status_code=res.status_code, detail=res.text)

            return ResponseModel[ProductPayload].model_validate(res.json())

        raise G2GAPIError(status_code=400, detail="Invalid query parameter")

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def get_attribute(
        self,
        product_id: str,
    ) -> ResponseModel[AttributePayload]:
        canonical_url = f"/{G2G_API_VERSION}/products/{product_id}/attributes"
        headers = self.generate_authorization_header(canonical_url)

        res = self.http_client.get(canonical_url, headers=cast(dict[str, str], headers))

        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[AttributePayload].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def get_offer(
        self,
        offer_id: str,
    ) -> ResponseModel[GetOfferResponse]:
        canonical_url = f"/v1/offers/{offer_id}"
        headers = self.generate_authorization_header(canonical_url)

        res = self.http_client.get(
            canonical_url,
            headers=cast(dict[str, str], headers),
        )

        try:
            res.raise_for_status()
        except HTTPStatusError:
            logger.error(res.text)
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[GetOfferResponse].model_validate(res.json())

    # @retry_on_fail(max_retries=3, sleep_interval=2)
    def create_offer(
        self, create_offer_request: CreateOfferRequest
    ) -> ResponseModel[CreateOfferResponse]:
        canonical_url = f"/{G2G_API_VERSION}/offers"
        headers = self.generate_authorization_header(canonical_url)

        print(create_offer_request.model_dump_json(indent=4))

        res = self.http_client.post(
            canonical_url,
            headers=cast(dict[str, str], headers),
            data=create_offer_request.model_dump(mode="json"),
        )
        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        print(res.json())
        return ResponseModel[CreateOfferResponse].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def update_offer(
        self,
        offer_id: str,
        update_offer_request: CreateOfferRequest,
    ) -> ResponseModel[CreateOfferResponse]:
        canonical_url = f"/{G2G_API_VERSION}/offers/{offer_id}"
        headers = self.generate_authorization_header(canonical_url)

        res = self.http_client.patch(
            canonical_url,
            headers=cast(dict[str, str], headers),
            data=update_offer_request.model_dump(mode="json"),
        )
        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[CreateOfferResponse].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def delete_offer(
        self,
        offer_id: str,
    ) -> ResponseModel[DeleteOfferResponse]:
        canonical_url = f"/{G2G_API_VERSION}/offers/{offer_id}"
        headers = self.generate_authorization_header(canonical_url)

        res = self.http_client.delete(
            canonical_url,
            headers=cast(dict[str, str], headers),
        )
        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[DeleteOfferResponse].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def search_offer(self):
        canonical_url = f"/{G2G_API_VERSION}/offers/search"
        headers = self.generate_authorization_header(canonical_url)

        payload = {}

        res = self.http_client.post(
            canonical_url,
            headers=cast(dict[str, str], headers),
            data=payload,
        )
        try:
            res.raise_for_status()
        except HTTPStatusError:
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        print(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def get_order(
        self,
        order_id: str,
    ) -> ResponseModel[Order]:
        canonical_url = f"/{G2G_API_VERSION}/orders/{order_id}"
        headers = self.generate_authorization_header(canonical_url)
        res = self.http_client.get(
            canonical_url,
            headers=cast(dict[str, str], headers),
        )

        try:
            res.raise_for_status()
        except HTTPStatusError:
            logger.exception(res.text)
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[Order].model_validate(res.json())

    @retry_on_fail(max_retries=3, sleep_interval=2)
    def patch_delivery_order(
        self,
        order_id: str,
        delivery_id: str,
        payload: PatchDeliveryPayload,
    ) -> ResponseModel[PathchDeliveryResponse]:
        canonical_url = f"/{G2G_API_VERSION}/orders/{order_id}/delivery/{delivery_id}"
        headers = self.generate_authorization_header(canonical_url)
        res = self.http_client.patch(
            canonical_url,
            headers=cast(dict[str, str], headers),
            data=payload.model_dump(mode="json"),
        )
        try:
            res.raise_for_status()
        except HTTPStatusError:
            logger.exception(res.text)
            raise G2GAPIError(status_code=res.status_code, detail=res.text)

        return ResponseModel[PathchDeliveryResponse].model_validate(res.json)


g2g_api_client = G2GAPIClient()
