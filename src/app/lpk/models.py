from pydantic import BaseModel

from typing import Generic, TypeVar
from .enums import CategoryVariant, FormType

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    code: str
    data: T


class Product(BaseModel):
    code: str
    category_code: str
    name: str
    provider_code: str
    price: int
    process_time: int
    country_code: str
    status: str


class ProductResponse(BaseModel):
    products: list[Product]


class Server(BaseModel):
    value: str
    name: str


class Option(BaseModel):
    value: str
    name: str


class Form(BaseModel):
    name: str
    type: FormType
    options: list[Option] | None = None


class Category(BaseModel):
    code: str
    name: str
    variant: CategoryVariant
    check_id: str
    country_code: str
    forms: list[Form]
    servers: list[Server]


class CategoryResponse(BaseModel):
    categories: list[Category]
