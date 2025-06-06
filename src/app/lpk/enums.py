from enum import Enum


class CategoryVariant(Enum):
    DIGITAL = "DIGITAL"
    VOUCHER = "VOUCHER"


class FormType(Enum):
    tel = "tel"
    text = "text"
    option = "option"
    textarea = "textarea"
    number = "number"
