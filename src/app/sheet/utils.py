from gspread.utils import rowcol_to_a1


def col_index_to_a1(col: int) -> str:
    full_a1_annotation = rowcol_to_a1(row=1, col=col)
    return full_a1_annotation.replace("1", "")
