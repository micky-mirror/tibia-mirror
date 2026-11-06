"""The choice of how to select the area of a mirror again."""

import tkinter as tk
from functools import partial

from tibia_mirror.i18n import tr
from tibia_mirror.ui.panel.controls.popup import Popup
from tibia_mirror.ui.panel.mirrors.select_area_callback import SelectAreaCallback


class SelectAgainDialog(Popup):
    """Asks if the new area of a mirror is selected by drag or by click."""

    def __init__(
        self,
        window: tk.Misc,
        mirror_id: str,
        on_select_area: SelectAreaCallback,
    ) -> None:
        super().__init__(window, tr("Select area again"))
        self._mirror_id = mirror_id  # the mirror whose area is selected again
        self._on_select_area = on_select_area

        self._add_choice_buttons()
        self._open()

    def _add_choice_buttons(self) -> None:
        row = self._add_button_row()
        by_drag = partial(self._select, is_by_click=False)
        by_click = partial(self._select, is_by_click=True)

        self._add_button(row, tr("Cancel"), self._cancel, kind="secondary", count=3)
        self._add_button(row, tr("By drag"), by_drag, kind="primary", count=3)
        self._add_button(row, tr("By click"), by_click, kind="mauve", count=3)

    def _select(self, *, is_by_click: bool) -> None:
        self.destroy()
        self._on_select_area(self._mirror_id, is_by_click=is_by_click)

    def _confirm(self) -> None:
        self._select(is_by_click=False)
