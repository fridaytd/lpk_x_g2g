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
    lapak_code: Annotated[
        str | None,
        {
            COL_META: "O",
            IS_UPDATE_META: True,
        },
    ] = None


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
    note: Annotated[
        str | None,
        {
            COL_META: "B",
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

    @staticmethod
    def write_log(
        note: str,
    ) -> None:
        last_row_index = LogToSheet.get_last_log_row()
        LogToSheet(
            index=last_row_index + 1,
            time=formated_datetime(datetime.now()),
            note=note,
        ).update()
