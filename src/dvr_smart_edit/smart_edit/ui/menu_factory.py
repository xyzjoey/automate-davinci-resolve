from ...extended_resolve.ui_manager import UiManager


class MultiButtons:
    def __init__(self, ui_manager: UiManager, common_props, props_list):
        self.ui_manager = ui_manager
        self.props_list = []

        for i, props in enumerate(props_list):
            final_props = {
                "Checkable": True,
                **common_props,
                **props,
            }
            final_props["ID"] = final_props["ID"].format(index=i)
            self.props_list.append(final_props)

    def get_elements(self):
        ui = self.ui_manager._ui_manager

        return [ui.Button(props) for props in self.props_list]

    def register_callbacks(self, window, additional_callback=lambda _: None):
        items = window.GetItems()

        def on_clicked(index):
            for i, props in enumerate(self.props_list):
                if i == index:
                    items[props["ID"]].Checked = True
                else:
                    items[props["ID"]].Checked = False

            additional_callback(index)

        def get_callback(index):
            return lambda event: on_clicked(index)

        for i, props in enumerate(self.props_list):
            element_events = getattr(window.On, props["ID"])
            element_events.Clicked = get_callback(i)

    def get_selected_index(self, window):
        items = window.GetItems()

        for i, props in enumerate(self.props_list):
            if items[props["ID"]].Checked:
                return i

        return None


class MenuFactory:
    HEADER1_STYLE = "color: lightgray; font-size: 14px; font-weight: bold;"
    HEADER2_STYLE = "color: lightgray; font-size: 14px; font-weight: bold; margin-bottom: 5px;"
    CONTROL_NAME_STYLE = "color: lightgray;"
    SEPARATER_STYLE = "border-top: 1px solid #090909; margin-top: 10px;"

    def __init__(self, ui_manager: UiManager):
        self.ui_manager = ui_manager

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

    def separater(self):
        ui = self.ui_manager._ui_manager

        return ui.Label(
            {
                "Weight": 0,
                "FrameStyle": 4,
            }
        )

    def control_label(self, label_props):
        ui = self.ui_manager._ui_manager

        return ui.Label(
            {
                "StyleSheet": self.CONTROL_NAME_STYLE,
                **label_props,
            }
        )

    def label_and_controls(self, label_props, elements):
        ui = self.ui_manager._ui_manager

        return ui.HGroup(
            [
                ui.Label(
                    {
                        "StyleSheet": self.CONTROL_NAME_STYLE,
                        "Weight": 2,
                        **label_props,
                    }
                ),
                ui.HGroup(
                    {
                        "Weight": 6,
                    },
                    elements,
                ),
            ],
        )

    def vertical_center(self, *elements):
        ui = self.ui_manager._ui_manager

        return ui.VGroup(
            {
                "Weight": 0,
            },
            [
                ui.VGap(0, 10),
                *elements,
                ui.VGap(0, 10),
            ],
        )

    def horizontal_center(self, *elements):
        ui = self.ui_manager._ui_manager

        return ui.HGroup(
            {
                "Weight": 0,
            },
            [
                ui.HGap(0, 10),
                *elements,
                ui.HGap(0, 10),
            ],
        )

    def horizontal_padding(self, *elements):
        ui = self.ui_manager._ui_manager

        return ui.HGroup(
            [
                ui.HGap(5),
                ui.VGroup(elements),
                ui.HGap(5),
            ]
        )

    def multi_buttons(self, *args, **kw):
        return MultiButtons(self.ui_manager, *args, **kw)
