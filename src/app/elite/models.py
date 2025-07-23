from pydantic import BaseModel


class AvailableGameResponse(BaseModel):
    code: str
    games: list[str]


class ElitediasGameFieldsInfo(BaseModel):
    fields: list[str]
    notes: str


class ElitediasGameFields(BaseModel):
    code: str
    info: ElitediasGameFieldsInfo


class FriElidiasGame(BaseModel):
    game: str
    denominations: dict[str, str | float]
    notes: str
    currency: str = "SGD"


class CreateTopUpResponse(BaseModel):
    status: str | None = None
    order_id: str | None = None
    code: str | None = None
    message: str | None = None


class TrackOrderResponse(BaseModel):
    order_id: str | None = None
    order_status: str
    price: float | None = None
    game: str | None = None
    denom: str | None = None
    userid: str | None = None
    serviceid: str | None = None
    order_details: list[str] | None = None
    timestamp: float | None = None
    message: str | None = None
    code: str | None = None
