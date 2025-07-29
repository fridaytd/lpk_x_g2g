from datetime import datetime

from typing import (
    Annotated,
    Final,
    Self,
    TypeVar,
    Generic,
    Any,
    ClassVar,
)

from gspread.worksheet import Worksheet
from gspread.utils import ValueInputOption
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app import config

from ..shared.decorators import retry_on_fail
from .enums import CheckType
from .g_sheet import gsheet_client
from .exceptions import SheetError
from ..shared.utils import formated_datetime
from .utils import col_index_to_a1

T = TypeVar("T")

COL_META: Final[str] = "col_name_xxx"
IS_UPDATE_META: Final[str] = "is_update_xxx"
IS_NOTE_META: Final[str] = "is_note_xxx"


class NoteMessageUpdatePayload(BaseModel):
    index: int
    message: str


class BatchCellUpdatePayload(BaseModel, Generic[T]):
    cell: str
    value: T


class ColSheetModel(BaseModel):
    # Model config
    model_config = ConfigDict(arbitrary_types_allowed=True)

    sheet_id: str
    sheet_name: str
    index: int

    @classmethod
    def get_worksheet(
        cls,
        sheet_id: str,
        sheet_name: str,
    ) -> Worksheet:
        spreadsheet = gsheet_client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        return worksheet

    @classmethod
    def mapping_fields(cls) -> dict:
        mapping_fields = {}
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if COL_META in metadata:
                        mapping_fields[field_name] = metadata[COL_META]
                        break

        return mapping_fields

    @classmethod
    def updated_mapping_fields(cls) -> dict:
        mapping_fields = {}
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if (
                        COL_META in metadata
                        and IS_UPDATE_META in metadata
                        and metadata[IS_UPDATE_META]
                    ):
                        mapping_fields[field_name] = metadata[COL_META]
                        break

        return mapping_fields

    @classmethod
    def get_col_by_attribute_name(cls, attribute_name: str) -> str:
        mapping_fields = cls.mapping_fields()
        for field_name, col_name in mapping_fields.items():
            if attribute_name == field_name:
                return col_name

        raise SheetError(f"Can not field col with attribute name: {attribute_name}")

    @classmethod
    def get(
        cls,
        sheet_id: str,
        sheet_name: str,
        index: int,
    ) -> Self:
        mapping_dict = cls.mapping_fields()

        query_value = []

        for _, v in mapping_dict.items():
            query_value.append(f"{v}{index}")

        worksheet = cls.get_worksheet(sheet_id=sheet_id, sheet_name=sheet_name)

        model_dict = {
            "index": index,
            "sheet_id": sheet_id,
            "sheet_name": sheet_name,
        }

        query_results = worksheet.batch_get(query_value)
        count = 0
        for k, _ in mapping_dict.items():
            model_dict[k] = query_results[count].first()
            if isinstance(model_dict[k], str):
                model_dict[k] = model_dict[k].strip()
            count += 1
        return cls.model_validate(model_dict)

    @classmethod
    def batch_get(
        cls,
        sheet_id: str,
        sheet_name: str,
        indexes: list[int],
    ) -> list[Self]:
        worksheet = cls.get_worksheet(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
        )
        mapping_dict = cls.mapping_fields()

        result_list: list[Self] = []
        error_list: list[NoteMessageUpdatePayload] = []

        query_value = []
        for index in indexes:
            for _, v in mapping_dict.items():
                query_value.append(f"{v}{index}")

        query_results = worksheet.batch_get(query_value)

        count = 0

        for index in indexes:
            model_dict = {
                "index": index,
                "sheet_id": sheet_id,
                "sheet_name": sheet_name,
            }

            for k, _ in mapping_dict.items():
                model_dict[k] = query_results[count].first()
                if isinstance(model_dict[k], str):
                    model_dict[k] = model_dict[k].strip()
                count += 1
            try:
                result_list.append(cls.model_validate(model_dict))
            except ValidationError as e:
                error_list.append(
                    NoteMessageUpdatePayload(
                        index=index,
                        message=f"{formated_datetime(datetime.now())} Validation Error at row {index}: {e.errors(include_url=False)}",
                    )
                )

        cls.batch_update_note_message(
            sheet_id=sheet_id, sheet_name=sheet_name, update_payloads=error_list
        )

        return result_list

    @classmethod
    @retry_on_fail(max_retries=3, sleep_interval=30)
    def batch_update(
        cls,
        sheet_id: str,
        sheet_name: str,
        list_object: list[Self],
    ) -> None:
        worksheet = cls.get_worksheet(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
        )
        mapping_dict = cls.updated_mapping_fields()
        update_batch = []

        for object in list_object:
            model_dict = object.model_dump(mode="json")

            for k, v in mapping_dict.items():
                update_batch.append(
                    {
                        "range": f"{v}{object.index}",
                        "values": [[model_dict[k]]],
                    }
                )

        if len(list_object) > 0:
            worksheet.batch_update(
                update_batch, value_input_option=ValueInputOption.user_entered
            )

    @retry_on_fail(max_retries=3, sleep_interval=30)
    def update(
        self,
    ) -> None:
        mapping_dict = self.updated_mapping_fields()
        model_dict = self.model_dump(mode="json")

        worksheet = self.get_worksheet(
            sheet_id=self.sheet_id, sheet_name=self.sheet_name
        )

        update_batch = []
        for k, v in mapping_dict.items():
            update_batch.append(
                {
                    "range": f"{v}{self.index}",
                    "values": [[model_dict[k]]],
                }
            )

        worksheet.batch_update(
            update_batch, value_input_option=ValueInputOption.user_entered
        )

    @classmethod
    @retry_on_fail(max_retries=5, sleep_interval=30)
    def update_note_message(
        cls,
        sheet_id: str,
        sheet_name: str,
        index: int,
        messages: str,
    ):
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if COL_META in metadata and IS_NOTE_META in metadata:
                        worksheet = cls.get_worksheet(
                            sheet_id=sheet_id,
                            sheet_name=sheet_name,
                        )

                        worksheet.batch_update(
                            [
                                {
                                    "range": f"{metadata[COL_META]}{index}",
                                    "values": [[messages]],
                                }
                            ],
                            value_input_option=ValueInputOption.user_entered,
                        )
                        return

        raise SheetError("Can't update sheet message")

    @classmethod
    @retry_on_fail(max_retries=5, sleep_interval=30)
    def batch_update_note_message(
        cls,
        sheet_id: str,
        sheet_name: str,
        update_payloads: list[NoteMessageUpdatePayload],
    ):
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if (
                        COL_META in metadata
                        and IS_NOTE_META in metadata
                        and metadata[IS_NOTE_META]
                    ):
                        worksheet = cls.get_worksheet(
                            sheet_id=sheet_id,
                            sheet_name=sheet_name,
                        )

                        batch: list[dict] = []
                        for payload in update_payloads:
                            batch.append(
                                {
                                    "range": f"{metadata[COL_META]}{payload.index}",
                                    "values": [[payload.message]],
                                }
                            )
                        worksheet.batch_update(
                            batch, value_input_option=ValueInputOption.user_entered
                        )
                        return

        raise SheetError("Can't update sheet message")

    @classmethod
    @retry_on_fail(max_retries=5, sleep_interval=30)
    def free_style_batch_update(
        cls,
        sheet_id: str,
        sheet_name: str,
        update_payloads: list[BatchCellUpdatePayload],
    ):
        worksheet = cls.get_worksheet(sheet_id=sheet_id, sheet_name=sheet_name)
        batch: list[dict] = []
        for payload in update_payloads:
            batch.append(
                {
                    "range": payload.cell,
                    "values": [[payload.value]],
                }
            )

        worksheet.batch_update(batch, value_input_option=ValueInputOption.user_entered)

    @classmethod
    @retry_on_fail(max_retries=5, sleep_interval=10)
    def get_cell_value(
        cls,
        sheet_id: str,
        sheet_name: str,
        cell: str,
    ) -> Any | None:
        res = gsheet_client.http_client.values_get(
            params={"valueRenderOption": "UNFORMATTED_VALUE"},
            id=sheet_id,
            range=f"{sheet_name}!{cell}",
        )

        stock = res.get("values", None)
        if stock:
            return stock[0][0]

        return None


class RowModel(ColSheetModel):
    CHECK: Annotated[
        str,
        {
            COL_META: "B",
        },
    ]
    GAME: Annotated[
        str | None,
        {
            COL_META: "C",
        },
    ] = None
    PACK: Annotated[
        str | None,
        {
            COL_META: "D",
        },
    ] = None
    code: Annotated[
        str,
        {
            COL_META: "E",
        },
    ]
    LOWEST_PRICE: Annotated[
        str | None,
        {
            COL_META: "F",
            IS_UPDATE_META: True,
        },
    ] = None
    NOTE: Annotated[
        str | None,
        {
            COL_META: "G",
            IS_UPDATE_META: True,
            IS_NOTE_META: True,
        },
    ] = None
    STATUS: Annotated[
        str | None,
        {
            COL_META: "H",
        },
    ] = None
    process_time: Annotated[
        int | None,
        {
            COL_META: "I",
        },
    ] = None
    country_code_priority: Annotated[
        str | None,
        {
            COL_META: "J",
        },
    ] = None
    FILL_IN: Annotated[
        str | None,
        {
            COL_META: "K",
        },
    ] = None
    ID_SHEET: Annotated[
        str | None,
        {
            COL_META: "L",
        },
    ] = None
    SHEET: Annotated[
        str | None,
        {
            COL_META: "M",
        },
    ] = None
    CELL: Annotated[
        str | None,
        {
            COL_META: "N",
        },
    ] = None

    @classmethod
    @retry_on_fail(max_retries=5, sleep_interval=10)
    def get_run_indexes(
        cls, sheet_id: str, sheet_name: str, col_index: int
    ) -> list[int]:
        sheet = cls.get_worksheet(sheet_id=sheet_id, sheet_name=sheet_name)
        run_indexes = []
        check_col = sheet.col_values(col_index)
        for idx, value in enumerate(check_col):
            idx += 1
            if not isinstance(value, str):
                value = str(value)
            if value in [type.value for type in CheckType]:
                run_indexes.append(idx)

        return run_indexes


class G2GTopUpProduct(ColSheetModel):
    STT: Annotated[
        int,
        {
            COL_META: "A",
            IS_UPDATE_META: True,
        },
    ]
    service_id: Annotated[
        str,
        {
            COL_META: "B",
            IS_UPDATE_META: True,
        },
    ]
    service_name: Annotated[
        str,
        {
            COL_META: "C",
            IS_UPDATE_META: True,
        },
    ]
    brand_id: Annotated[
        str | None,
        {
            COL_META: "D",
            IS_UPDATE_META: True,
        },
    ] = None
    brand_name: Annotated[
        str,
        {
            COL_META: "E",
            IS_UPDATE_META: True,
        },
    ]
    service_option: Annotated[
        str,
        {
            COL_META: "F",
            IS_UPDATE_META: True,
        },
    ]
    product_id: Annotated[
        str,
        {
            COL_META: "G",
            IS_UPDATE_META: True,
        },
    ]
    product_name: Annotated[
        str,
        {
            COL_META: "H",
            IS_UPDATE_META: True,
        },
    ]
    attribute_group_id: Annotated[
        str,
        {
            COL_META: "I",
            IS_UPDATE_META: True,
        },
    ]
    attribute_name: Annotated[
        str,
        {
            COL_META: "J",
            IS_UPDATE_META: True,
        },
    ]
    attribute_id: Annotated[
        str,
        {
            COL_META: "K",
            IS_UPDATE_META: True,
        },
    ]

    attribute_value: Annotated[
        str,
        {
            COL_META: "L",
            IS_UPDATE_META: True,
        },
    ]
    sub_attribute_id: Annotated[
        str | None,
        {
            COL_META: "M",
            IS_UPDATE_META: True,
        },
    ] = None
    sub_attribute_value: Annotated[
        str | None,
        {
            COL_META: "N",
            IS_UPDATE_META: True,
        },
    ] = None
    lapak_codes: Annotated[
        str | None,
        {
            COL_META: "O",
            IS_UPDATE_META: True,
        },
    ] = None
    eli_game: Annotated[
        str | None,
        {
            COL_META: "P",
            IS_UPDATE_META: True,
        },
    ] = None
    eli_denomination: Annotated[
        str | None,
        {
            COL_META: "Q",
            IS_UPDATE_META: True,
        },
    ] = None
    provider_mode: Annotated[
        str | None,
        {
            COL_META: "R",
            IS_UPDATE_META: True,
        },
    ] = None

    @staticmethod
    def get_all_from_sheet(
        sheet_id: str,
        sheet_name: str,
        start_row: int,
    ) -> tuple[list["G2GTopUpProduct"], float, float]:
        """
        Retrieves all G2G top-up product data from a specified Google Sheet along with currency exchange rates.
        Args:
            sheet_id (str): The ID of the Google Sheet to read from
            sheet_name (str): The name of the specific worksheet to read
            start_row (int): The row number to start reading data from
        Returns:
            tuple[list[G2GTopUpProduct], float, float]: A tuple containing:
                - List of G2GTopUpProduct objects parsed from the sheet
                - IDR to USD exchange rate
                - SGD to USD exchange rate
        Notes:
            - Skips invalid rows that fail model validation
            - Exchange rates will be -1 if not found in specified cells
            - Only processes columns that match the G2GTopUpProduct field mappings
        """

        g2g_top_up_products: list[G2GTopUpProduct] = []
        worksheet = G2GTopUpProduct.get_worksheet(
            sheet_id=sheet_id, sheet_name=sheet_name
        )

        all_cells = worksheet.get_all_cells()

        _temp_product_dict: dict[str, dict] = {}

        mapping_fields = G2GTopUpProduct.mapping_fields()
        reversed_mapping_dict: dict = {v: k for k, v in mapping_fields.items()}

        for cell in all_cells:
            if cell.address == config.IDR_TO_USD_RATE_CELL:
                IDR_to_USE_rate = float(cell.value if cell.value else -1)
            if cell.address == config.SGD_TO_USD_RATE_CELL:
                SGD_to_USE_rate = float(cell.value if cell.value else -1)

            if cell.row >= start_row:
                if str(cell.row) not in _temp_product_dict:
                    _temp_product_dict[str(cell.row)] = {
                        "index": cell.row,
                        "sheet_id": sheet_id,
                        "sheet_name": sheet_name,
                    }
                if col_index_to_a1(cell.col) in reversed_mapping_dict:
                    _temp_product_dict[str(cell.row)][
                        reversed_mapping_dict[col_index_to_a1(cell.col)]
                    ] = cell.value

        for _, value in _temp_product_dict.items():
            try:
                g2g_top_up_product = G2GTopUpProduct.model_validate(value)
                g2g_top_up_products.append(g2g_top_up_product)
            except ValidationError:
                pass

        return g2g_top_up_products, IDR_to_USE_rate, SGD_to_USE_rate


class LPKProduct(ColSheetModel):
    CHECK: Annotated[
        str | None,
        {
            COL_META: "A",
        },
    ] = None
    code: Annotated[
        str | None,
        {
            COL_META: "B",
            IS_UPDATE_META: True,
        },
    ] = None
    category_code: Annotated[
        str | None,
        {
            COL_META: "C",
            IS_UPDATE_META: True,
        },
    ] = None
    category: Annotated[
        str | None,
        {
            COL_META: "D",
            IS_UPDATE_META: True,
        },
    ] = None
    name: Annotated[
        str | None,
        {
            COL_META: "E",
            IS_UPDATE_META: True,
        },
    ] = None
    provider_code: Annotated[
        str | None,
        {
            COL_META: "F",
            IS_UPDATE_META: True,
        },
    ] = None
    price: Annotated[
        str | None,
        {
            COL_META: "G",
            IS_UPDATE_META: True,
        },
    ] = None
    process_time: Annotated[
        str | None,
        {
            COL_META: "H",
            IS_UPDATE_META: True,
        },
    ] = None
    country_code: Annotated[
        str | None,
        {
            COL_META: "I",
            IS_UPDATE_META: True,
        },
    ] = None
    status: Annotated[
        str | None,
        {
            COL_META: "J",
            IS_UPDATE_META: True,
        },
    ] = None
    Note: Annotated[
        str | None,
        {
            COL_META: "K",
            IS_UPDATE_META: True,
            IS_NOTE_META: True,
        },
    ] = None

    @field_validator("price", "process_time", mode="before")
    def convert_to_str(cls, v):
        return str(v) if isinstance(v, (int, float)) else v


class LogToSheet(ColSheetModel):
    # Instance attributes
    sheet_id: ClassVar[str] = config.LOG_SHEET_ID
    sheet_name: ClassVar[str] = config.LOG_SHEET_NAME

    time: Annotated[
        str | None,
        {
            COL_META: "A",
            IS_UPDATE_META: True,
        },
    ] = None
    g2g_order_id: Annotated[
        str | None,
        {
            COL_META: "B",
            IS_UPDATE_META: True,
        },
    ] = None
    g2g_offer_id: Annotated[
        str | None,
        {
            COL_META: "C",
            IS_UPDATE_META: True,
        },
    ] = None
    g2g_product_id: Annotated[
        str | None,
        {
            COL_META: "D",
            IS_UPDATE_META: True,
        },
    ] = None
    provider: Annotated[
        str | None,
        {
            COL_META: "E",
            IS_UPDATE_META: True,
        },
    ] = None
    buy_price_use: Annotated[
        str | None,
        {
            COL_META: "F",
            IS_UPDATE_META: True,
        },
    ] = None
    buy_price_in_provider_curency: Annotated[
        str | None,
        {
            COL_META: "G",
            IS_UPDATE_META: True,
        },
    ] = None
    sell_price: Annotated[
        str | None,
        {
            COL_META: "H",
            IS_UPDATE_META: True,
        },
    ] = None
    sell_quantity: Annotated[
        str | None,
        {
            COL_META: "I",
            IS_UPDATE_META: True,
        },
    ] = None
    provider_product_id: Annotated[
        str | None,
        {
            COL_META: "J",
            IS_UPDATE_META: True,
        },
    ] = None
    provider_order_ids: Annotated[
        str | None,
        {
            COL_META: "K",
            IS_UPDATE_META: True,
        },
    ] = None
    receive_note: Annotated[
        str | None,
        {
            COL_META: "L",
            IS_UPDATE_META: True,
        },
    ] = None
    delivery_at: Annotated[
        str | None,
        {
            COL_META: "M",
            IS_UPDATE_META: True,
        },
    ] = None
    delivery_note: Annotated[
        str | None,
        {
            COL_META: "N",
            IS_UPDATE_META: True,
        },
    ] = None

    @classmethod
    def get_last_log_row(
        cls,
    ) -> int:
        worksheet = cls.get_worksheet(
            sheet_id=cls.sheet_id,
            sheet_name=cls.sheet_name,
        )

        return len(worksheet.col_values(1))

    @classmethod
    def register_note_row(cls) -> "LogToSheet":
        worksheet = cls.get_worksheet(
            sheet_id=cls.sheet_id,
            sheet_name=cls.sheet_name,
        )
        next_log_row_index = len(worksheet.col_values(1)) + 1
        time_col = cls.get_col_by_attribute_name("time")
        time_value = formated_datetime(datetime.now())
        worksheet.update([[time_value]], f"{time_col}{next_log_row_index}")
        return LogToSheet(index=next_log_row_index, time=time_value)

    @classmethod
    def note_delivery(
        cls,
        note_index: int,
        note: str,
    ) -> None:
        delivery_at_col = cls.get_col_by_attribute_name("delivery_at")
        delivery_note_col = cls.get_col_by_attribute_name("delivery_note")
        cls.free_style_batch_update(
            sheet_id=cls.sheet_id,
            sheet_name=cls.sheet_name,
            update_payloads=[
                BatchCellUpdatePayload(
                    cell=f"{delivery_at_col}{note_index}",
                    value=formated_datetime(datetime.now()),
                ),
                BatchCellUpdatePayload(
                    cell=f"{delivery_note_col}{note_index}",
                    value=note,
                ),
            ],
        )

    def append_note(self, note: str) -> None:
        if not self.receive_note:
            self.receive_note = ""

        self.receive_note += f"\n{note}"
        self.receive_note.strip()
