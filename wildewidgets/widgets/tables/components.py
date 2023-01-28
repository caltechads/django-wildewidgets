from typing import List, Tuple


class DataTableColumn:

    def __init__(
        self,
        field: str,
        verbose_name: str = None,
        searchable: bool = False,
        sortable: bool = False,
        align: str = 'left',
        head_align: str = 'left',
        visible: bool = True,
        wrap: bool = True
    ):
        self.field = field
        self.verbose_name = verbose_name if verbose_name else self.field.capitalize()
        self.searchable = searchable
        self.sortable = sortable
        self.align = align
        self.head_align = head_align
        self.visible = visible
        self.wrap = wrap


class DataTableFilter:

    def __init__(self, header=None):
        self.header = header
        self.choices: List[Tuple[str, str]] = [('Any', '')]

    def add_choice(self, label: str, value: str) -> None:
        self.choices.append((label, value))


class DataTableStyler:

    def __init__(self, is_row, test_cell, cell_value, css_class, target_cell=None):
        self.is_row = is_row
        self.test_cell = test_cell
        self.cell_value = cell_value
        self.css_class = css_class
        self.target_cell = target_cell
        self.test_index = 0
        self.target_index = 0


class DataTableForm:

    def __init__(self, table):
        if table.has_form_actions():
            self.is_visible: bool = True
        else:
            self.is_visible = False
        self.actions = table.get_form_actions()
        self.url = table.form_url
