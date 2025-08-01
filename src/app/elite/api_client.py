import asyncio
import httpx
import json

from typing import Final

from app import config
from app.paths import SRC_PATH


from .models import (
    AvailableGameResponse,
    ElitediasGameFields,
    ElitediasGameFieldsInfo,
    TrackOrderResponse,
    CreateTopUpResponse,
)
from . import logger

ELITEDIAS_BASE_URL: Final[str] = "https://dev.api.elitedias.com"


class ElitediasAPIClient:
    def __init__(self) -> None:
        self.headers = {
            "Origin": config.ORIGIN,
            "Content-Type": "application/json",
            "User-Agent": "PostmanRuntime/7.44.1",
        }
        self.base_url = ELITEDIAS_BASE_URL

    async def get_available_games(self) -> AvailableGameResponse:
        async with httpx.AsyncClient(headers=self.headers) as client:
            res = await client.post(
                f"{self.base_url}/elitedias_games_available",
                json={
                    "api_key": config.ALITEDIAS_API_KEY,
                },
                timeout=60,
            )

            try:
                res.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.exception(e)
                logger.info(res.text)
                res.raise_for_status()

            return AvailableGameResponse.model_validate(res.json())

    async def get_denominations(self, game: str) -> dict[str, str]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            res = await client.post(
                f"{self.base_url}/elitedias_api_denominations",
                json={"api_key": config.ALITEDIAS_API_KEY, "game": game},
                timeout=60,
            )

            try:
                res.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.exception(e)
                logger.info(res.text)
                res.raise_for_status()

            return res.json()

    async def get_price(self, game: str, denom: str) -> float:
        denom_dict = await self.get_denominations(game)

        return float(denom_dict[denom])

    async def get_elitedias_game_fields_in_cache(
        self, game: str
    ) -> ElitediasGameFields:
        cached_data = {}
        with open(SRC_PATH / "data" / "game_notes.json") as f:
            cached_data = json.load(f)
            if game in cached_data:
                return ElitediasGameFields(
                    code="200",
                    info=ElitediasGameFieldsInfo(fields=[], notes=cached_data[game]),
                )
        async with httpx.AsyncClient(headers=self.headers) as client:
            res = await client.post(
                f"{self.base_url}/elitedias_game_fields",
                json={"api_key": config.ALITEDIAS_API_KEY, "game": game},
                timeout=60,
            )

            try:
                res.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.exception(e)
                logger.info(res.text)
                res.raise_for_status()

            await asyncio.sleep(10)

            model_response = ElitediasGameFields.model_validate(res.json())

            cached_data[game] = model_response.info.notes
            with open(SRC_PATH / "data" / "game_notes.json", "w") as f:
                json.dump(cached_data, f, indent=4)

            return model_response

    async def get_elitedias_game_fields(self, game: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as client:
            res = await client.post(
                f"{self.base_url}/elitedias_game_fields",
                json={"api_key": config.ALITEDIAS_API_KEY, "game": game},
                timeout=60,
            )

            try:
                res.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.exception(e)
                logger.info(res.text)
                res.raise_for_status()

            return res.json()

    async def create_topup(
        self,
        payload: dict,
    ) -> CreateTopUpResponse:
        async with httpx.AsyncClient(headers=self.headers) as client:
            payload.update(
                {
                    "api_key": config.ALITEDIAS_API_KEY,
                }
            )

            res = await client.post(
                f"{self.base_url}/elitedias_reseller_topup_api",
                json=payload,
                timeout=60,
            )

            try:
                res.raise_for_status()
                return CreateTopUpResponse.model_validate(res.json())

            except Exception as e:
                logger.exception(e)
                logger.info(res.text)
                raise e

    async def track_order(
        self,
        order_id: str,
    ) -> TrackOrderResponse:
        async with httpx.AsyncClient(headers=self.headers) as client:
            res = await client.post(
                f"{self.base_url}/track_order",
                json={
                    "api_key": config.ALITEDIAS_API_KEY,
                    "order_id": order_id,
                },
                timeout=60,
            )

            try:
                res.raise_for_status()
                return TrackOrderResponse.model_validate(res.json())

            except Exception as e:
                logger.exception(e)
                logger.info(res.text)
                raise e


elitedias_api_client = ElitediasAPIClient()
