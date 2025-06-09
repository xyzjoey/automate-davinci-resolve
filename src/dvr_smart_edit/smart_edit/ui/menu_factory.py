from dataclasses import dataclass
from typing import Any, Callable

from ...extended_resolve.ui_manager import UiManager


class UiFactory:
    # FIXME header2 padding
    HEADER1_STYLE = "color: lightgray; font-size: 14px; font-weight: bold;"
    HEADER2_STYLE = "color: lightgray; font-size: 14px; font-weight: bold; margin-bottom: 5px;"
    HEADER3_STYLE = "color: lightgray; font-size: 14px;"
    CONTROL_NAME_STYLE = "color: lightgray;"
    SEPARATER_STYLE = "border-top: 1px solid #090909; margin-top: 10px;"

    id_for_repeating_ui = 0

    def __init__(self, ui_manager: UiManager):
        self.ui_manager = ui_manager

    @property
    def _ui(self):
        return self.ui_manager._ui_manager

    def next_id_for_repeating_ui(self):
        UiFactory.id_for_repeating_ui += 1
        return UiFactory.id_for_repeating_ui


class BaseUiGroup(UiFactory):
    def __init__(self, ui_group_id, window, **kw):
        super().__init__(**kw)
        self.ui_group_id = ui_group_id
        self.window = window

    def extend_callback(self, callback, *args, **kw):
        return lambda event: callback(event, *args, **kw)


class Tabs(BaseUiGroup):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.root_element = self._ui.VGroup(
            {"ID": f"{self.ui_group_id}Container"},
            [
                self._ui.TabBar(
                    {
                        "ID": self.ui_group_id,
                        "Weight": 0.0,
                    }
                ),
                self._ui.Stack(
                    {
                        "ID": f"{self.ui_group_id}Stack",
                        "Weight": 1.0,
                    },
                    [],
                ),
            ],
        )
        self._tab_bar = self.root_element.GetChildren()[1]
        self._stack = self.root_element.GetChildren()[2]

    def get_root_element(self):
        return self.root_element

    def add_tab(self, tab_name, element):
        self._tab_bar.AddTab(tab_name)

        self._stack.AddChild(element)
        self._switch_stack(tab_index=self._tab_bar.CurrentIndex)

        self.window._window.RecalcLayout()

    def finalize(self):
        self.window.register_event(self._tab_bar.ID, "CurrentChanged", self._on_tab_changed)

    def _switch_stack(self, tab_index):
        self._stack.CurrentIndex = len(self._stack.GetChildren()) - tab_index - 1  # reverse order

    def _on_tab_changed(self, event):
        self._switch_stack(tab_index=event["Index"])


class MultiButtons(BaseUiGroup):
    def __init__(self, button_props_list, **kw):
        super().__init__(**kw)

        self.root_element = self._ui.HGroup(
            [
                self._ui.Button(
                    {
                        "ID": f"{self.ui_group_id}{i}",
                        "Weight": 0.0,
                        "Checkable": True,
                        **button_props,
                    }
                )
                for i, button_props in enumerate(button_props_list)
            ],
        )
        self.on_select_callbacks = []

    def get_root_element(self):
        return self.root_element

    def register_on_select(self, *callbacks):
        self.on_select_callbacks.extend(callbacks)

    def finalize(self):
        for i, button_element in self.root_element.GetChildren().items():
            self.window.register_event(button_element.ID, "Clicked", self.extend_callback(self._on_select, i - 1))

        index = self.get_selected_index()

        if index is not None:
            self._on_select(None, index)

    def get_selected_index(self):
        for i, button_element in self.root_element.GetChildren().items():
            if button_element.Checked:
                return i - 1

        return None

    def _on_select(self, event, index):
        for i, button_element in self.root_element.GetChildren().items():
            if i - 1 == index:
                button_element.Checked = True
            else:
                button_element.Checked = False

        for callback in self.on_select_callbacks:
            callback(event, index)


class List(BaseUiGroup):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.root_element = self._ui.VGroup(
            {
                "ID": f"{self.ui_group_id}Container",
            },
            [],
        )

        self.items = {}

        self.on_item_added = lambda *_: ...
        self.on_index_changed_callback = lambda *_: ...
        self.on_item_removed = lambda *_: ...

    def get_root_element(self):
        return self.root_element

    def add_item(self):
        new_item_id = self.next_id_for_repeating_ui()
        new_index = len(self.items)
        new_element = self._ui.VGroup()

        self.items[new_item_id] = new_element

        self._update_elements()
        self.on_item_added(new_item_id, new_index, new_element)
        self.window._window.RecalcLayout()

        return new_item_id, new_element

    def remove_item(self, item_id):
        shifted = False

        for i, (curr_item_id, item_element) in enumerate(self.items.items()):
            if curr_item_id == item_id:
                shifted = True
                continue

            if shifted:
                self.on_index_changed_callback(curr_item_id, i - 1, item_element)

        self.items.pop(item_id)

        self._update_elements()
        self.on_item_removed()
        self.window._window.RecalcLayout()

    def reset_items(self, count: int):
        had_items = len(self.items) != 0
        self.items.clear()

        if had_items:
            self.on_item_removed()

        pending = []

        for i in range(count):
            new_item_id = self.next_id_for_repeating_ui()
            new_index = len(self.items)
            new_element = self._ui.VGroup()

            self.items[new_item_id] = new_element

            pending.append((new_item_id, new_index, new_element))

        self._update_elements()

        for new_item_id, new_index, new_element in pending:
            self.on_item_added(new_item_id, new_index, new_element)

        self.window._window.RecalcLayout()

    def register_on_item_added(self, callback):
        self.on_item_added = callback

    def register_on_index_changed(self, callback):
        self.on_index_changed_callback = callback

    def register_on_item_removed(self, callback):
        self.on_item_removed = callback

    def _update_elements(self):
        for child in self.root_element.GetChildren().values():
            self.root_element.RemoveChild(child)

        for i, item_element in reversed(list(enumerate(self.items.values()))):
            self.root_element.AddChild(item_element)

    def get_items(self):
        return self.items

    def iter_items_before(self, before_item_id):
        for item_id, item_element in self.items.items():
            if item_id == before_item_id:
                break

            yield item_id, item_element

    def finalize(self):
        pass


class MenuUiFactory(UiFactory):
    def __init__(self, window, *args, **kw):
        super().__init__(*args, **kw)
        self.window = window

        self._ui_groups = {}

    def header1(self, label_props):
        ui = self.ui_manager._ui_manager

        return ui.Label(
            {
                "StyleSheet": self.HEADER1_STYLE,
                **label_props,
            }
        )

    def header2(self, label_props):
        ui = self.ui_manager._ui_manager

        return ui.Label(
            {
                "StyleSheet": self.HEADER2_STYLE,
                **label_props,
            }
        )

    def header3(self, label_props):
        ui = self.ui_manager._ui_manager

        return ui.Label(
            {
                "StyleSheet": self.HEADER3_STYLE,
                **label_props,
            }
        )

    def empty_line(self):
        return self._ui.Label(
            {
                "Weight": 0,
                "Text": "",
            }
        )

    def separater(self):
        return self._ui.Label(
            {
                "Weight": 0,
                "FrameStyle": 4,  # QFrame::HLine
            }
        )

    def control_label(self, label_props):
        return self._ui.Label(
            {
                "StyleSheet": self.CONTROL_NAME_STYLE,
                **label_props,
            }
        )

    def label_and_controls(self, label_props, elements):
        return self._ui.HGroup(
            [
                self._ui.Label(
                    {
                        "StyleSheet": self.CONTROL_NAME_STYLE,
                        "Weight": 2,
                        **label_props,
                    }
                ),
                self._ui.HGroup(
                    {
                        "Weight": 6,
                    },
                    elements,
                ),
            ],
        )

    def vertical_center(self, *elements):
        return self._ui.VGroup(
            {
                "Weight": 0,
            },
            [
                self._ui.VGap(0, 10),
                *elements,
                self._ui.VGap(0, 10),
            ],
        )

    def horizontal_center(self, *elements):
        return self._ui.HGroup(
            {
                "Weight": 0,
            },
            [
                self._ui.HGap(0, 10),
                *elements,
                self._ui.HGap(0, 10),
            ],
        )

    def horizontal_left(self, *elements):
        return self._ui.HGroup(
            {
                "Weight": 0,
            },
            [
                *elements,
                self._ui.HGap(0, 10),
            ],
        )

    def horizontal_right(self, *elements):
        return self._ui.HGroup(
            {
                "Weight": 0,
            },
            [
                self._ui.HGap(0, 10),
                *elements,
            ],
        )

    def horizontal_padding(self, *elements):
        return self._ui.HGroup(
            [
                self._ui.HGap(5),
                self._ui.VGroup(elements),
                self._ui.HGap(5),
            ]
        )

    def horizontal_left_padding(self, *elements):
        return self._ui.HGroup(
            [
                self._ui.HGap(5),
                self._ui.VGroup(elements),
            ]
        )

    def tabs(self, ui_group_id: str):
        tabs = Tabs(ui_group_id=ui_group_id, window=self.window, ui_manager=self.ui_manager)
        self._add_ui_group(ui_group_id, tabs)
        return tabs.get_root_element()

    def multi_buttons(self, ui_group_id: str, button_props_list):
        multi_buttons = MultiButtons(button_props_list, ui_group_id=ui_group_id, window=self.window, ui_manager=self.ui_manager)
        self._add_ui_group(ui_group_id, multi_buttons)
        return multi_buttons.get_root_element()

    def list(self, ui_group_id: str):
        list = List(ui_group_id=ui_group_id, window=self.window, ui_manager=self.ui_manager)
        self._add_ui_group(ui_group_id, list)
        return list.get_root_element()

    def find_group(self, ui_group_id: str):
        return self._ui_groups.get(ui_group_id)

    def _add_ui_group(self, ui_group_id, ui_group):
        if ui_group_id not in self._ui_groups:
            self._ui_groups[ui_group_id] = ui_group
        else:
            raise KeyError(f"ui group id '{ui_group_id}' already exist")

    def finalize(self):
        for ui_group in self._ui_groups.values():
            ui_group.finalize()


MenuFactory = MenuUiFactory
