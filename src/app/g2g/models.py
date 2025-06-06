from pydantic import BaseModel
from typing import TypedDict, Generic, TypeVar, Literal


T = TypeVar("T", bound=BaseModel)

AuthorizationHeader = TypedDict(
    "AuthorizationHeader",
    {
        "g2g-api-key": str,
        "g2g-userid": str,
        "g2g-signature": str,
        "g2g-timestamp": str,
        "Content-Type": str | None,
    },
)


class ResponseModel(BaseModel, Generic[T]):
    request_id: str
    code: int
    message: str
    warning: str
    payload: T


class Category(BaseModel):
    category_id: str | None = None
    category_name: str
    sub_categories: list["Category"] | None = None


class Service(BaseModel):
    service_id: str
    service_name: str
    categories: list[Category] | None = None


class ServicePayload(BaseModel):
    service_list: list[Service]


class Brand(BaseModel):
    brand_id: str
    brand_name: str


class BrandPayLoad(BaseModel):
    service_id: str
    brand_list: list[Brand]
    after: str


class Product(BaseModel):
    product_id: str
    product_name: str
    service_name: str
    brand_name: str
    region_name: str
    category_id: str
    service_id: str
    brand_id: str


class ProductPayload(BaseModel):
    service_id: str | None = None
    brand_id: str | None = None
    product_list: list[Product]


################
# ATTRIBUTES


class Attribute(BaseModel):
    attribute_id: str
    attribute_name: str
    sub_attribute_list: list["Attribute"]


class InputSettings(BaseModel):
    min: int | float | None = None
    max: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    is_searchable: bool | None = None
    value: str | int | float | None = None


class AttributeGroup(BaseModel):
    attribute_group_id: str
    attribute_group_name: str
    input_field: Literal[
        "text",
        "number",
        "textarea",
        "paragraph",
        "dropdown",
        "password",
        "number_string",
    ]
    input_settings: InputSettings
    is_required: bool
    attribute_list: list[Attribute]


class DeliveryMethod(BaseModel):
    delivery_code: str
    delivery_method_id: str
    delivery_method_name: str
    attribute_group_list: list[AttributeGroup]


class AttributePayload(BaseModel):
    product_id: str
    attribute_group_list: list[AttributeGroup]
    delivery_method_list: list[DeliveryMethod]
    additional_info_list: list[AttributeGroup]


class OfferAttribute(BaseModel):
    attribute_group_id: str
    attribute_id: str


class WholesaleDetail(BaseModel):
    min: int
    max: int
    unit_price: float


class SalesTerritorySettings(BaseModel):
    countries: list[str] = []
    settings_type: Literal["global", "by_country", "exclusion"] = "global"


class CreateOfferRequest(BaseModel):
    product_id: str
    title: str
    description: str
    min_qty: int
    api_qty: int
    low_stock_alert_qty: int
    offer_attributes: list[OfferAttribute]
    currency: str
    unit_price: float
    wholesale_details: list[WholesaleDetail]
    sales_territory_settings: SalesTerritorySettings
    delivery_method_ids: list[str]


class CreateOfferResponse(BaseModel):
    offer_id: str
    seller_id: str
    offer_type: str
    delivery_type: list[str]
    product_id: str
    service_id: str
    brand_id: str
    region_id: str
    title: str
    description: str
    status: str
    currency: str
    unit_price: float
    min_qty: int
    available_qty: int
    api_qty: int
    low_stock_alert_qty: int
    offer_attributes: list[OfferAttribute]
    wholesale_details: list[dict]
    other_pricing: list[dict]
    other_wholesale_details: list[dict]
    sales_territory_settings: dict
    delivery_method_ids: list[str]
    delivery_speed: str
    created_at: int
    updated_at: int


class DeleteOfferResponse(BaseModel):
    success: bool
