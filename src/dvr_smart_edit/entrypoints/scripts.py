import importlib.metadata

from ..extended_resolve import davinci_resolve_module
from ..smart_edit.constants import SnapMode
from ..smart_edit.effect_control import EffectControl
from ..smart_edit.smart_edit_bin import SmartEditBin
from ..smart_edit.ui.loading_window import LoadingWindow
from ..smart_edit.uni_textplus import UniTextPlus


class FunctionalCallbacks:
    @staticmethod
    def on_import_smart_edit_bin():
        with LoadingWindow("SmartEdit", "Importing bin.."):
            SmartEditBin.import_bin()

    @staticmethod
    def on_generate_textplus_clips(snap_mode):
        with LoadingWindow("UniText+", "Generating clips..."):
            UniTextPlus.generate_textplus_clips(snap_mode)

    @staticmethod
    def on_generate_effect_control_clips():
        with LoadingWindow("EffectControl", "Generating clips..."):
            EffectControl.generate_effect_control_clips()

    @staticmethod
    def on_debug(items):
        with LoadingWindow("Debug", "Debug..."):
            pass


def smart_edit_menu():
    version = importlib.metadata.version("dvr_smart_edit")

    ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
    ui = ui_dispatcher._ui_manager
    disp = ui_dispatcher._ui_dispatcher

    window = disp.AddWindow(
        {
            "WindowTitle": "Smart Edit Menu",
            "ID": "SmartEditMenu",
            "Geometry": [100, 100, 350, 300],
        },
        [
            ui.VGroup(
                [
                    ui.Label(
                        {
                            "ID": "VersionLabel",
                            "Text": f"version: {version}",
                            "Weight": 0.0,
                        }
                    ),
                    ui.TabBar(
                        {
                            "ID": "MainTabs",
                            "Weight": 0.0,
                        }
                    ),
                    ui.VGap(0, 10),
                    ui.Stack(
                        {
                            "ID": "MainStack",
                            "Weight": 1.0,
                        },
                        [
                            # General tab content
                            ui.VGroup(
                                {"Spacing": 10},
                                [
                                    ui.Button(
                                        {
                                            "ID": "ImportSmartEditBin",
                                            "Text": "Import SmartEdit Bin",
                                            "ToolTip": "The SmartEdit bin contains UniText+, EffectControl, etc.",
                                            "Weight": 0.0,
                                        }
                                    ),
                                    ui.Button(
                                        {
                                            "ID": "Debug",
                                            "Text": "Debug",
                                            "Visible": False,
                                            "Weight": 0.0,
                                        }
                                    ),
                                ],
                            ),
                            # UniText+ tab content
                            ui.VGroup(
                                {"Spacing": 10},
                                [
                                    ui.HGroup(
                                        [
                                            ui.Label(
                                                {
                                                    "ID": "SnapModeLabel",
                                                    "Text": "Snap Mode:",
                                                    "ToolTip": "Select the snapping mode for generating clips.",
                                                    "Weight": 0.0,
                                                }
                                            ),
                                            ui.Button(
                                                {
                                                    "ID": "SnapModeChoice0",
                                                    "Text": "None",
                                                    "Checkable": True,
                                                    "Checked": False,
                                                }
                                            ),
                                            ui.Button(
                                                {
                                                    "ID": "SnapModeChoice1",
                                                    "Text": "Audio Clips",
                                                    "ToolTip": "Snap to clips in the audio track with most clips.",
                                                    "Checkable": True,
                                                    "Checked": True,
                                                }
                                            ),
                                        ],
                                    ),
                                    ui.Button(
                                        {
                                            "ID": "GenerateTextPlusClips",
                                            "Text": "Generate UniText+ Clips",
                                            "ToolTip": "Generate UniText+ clips based on active subtitle track.",
                                            "Weight": 0.0,
                                        }
                                    ),
                                ],
                            ),
                            # EffectControl tab content
                            ui.VGroup(
                                {"Spacing": 10},
                                [
                                    ui.Button(
                                        {
                                            "ID": "GenerateEffectControlClips",
                                            "Text": "Generate EffectControl Clips",
                                            "ToolTip": "Generate EffectControl clips according to `Generated Text+` track.\nOverwrite `Generated Control` track if already exist.",
                                            "Geometry": [0, 0, 30, 50],
                                            "Weight": 0.0,
                                        }
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ui.VGap(0, 10),
                ],
            ),
        ],
    )

    items = window.GetItems()
    items["MainTabs"].AddTab("General")
    items["MainTabs"].AddTab("UniText+")
    items["MainTabs"].AddTab("EffectControl")
    items["MainStack"].CurrentIndex = 0

    def on_tab_changed(event):
        items["MainStack"].CurrentIndex = event["Index"]

    def on_snap_mode_selected(event):
        selected_name = event["who"]

        for name, element in items.items():
            if name == selected_name:
                element.Checked = True
            elif name.startswith("SnapModeChoice"):
                element.Checked = False

    window.On.SmartEditMenu.Close = lambda ev: disp.ExitLoop()
    # ui control
    window.On.MainTabs.CurrentChanged = on_tab_changed
    window.On.SnapModeChoice0.Clicked = on_snap_mode_selected
    window.On.SnapModeChoice1.Clicked = on_snap_mode_selected
    # functional callbacks
    window.On.ImportSmartEditBin.Clicked = lambda event: FunctionalCallbacks.on_import_smart_edit_bin()
    window.On.GenerateTextPlusClips.Clicked = lambda event: FunctionalCallbacks.on_generate_textplus_clips(
        next(
            (SnapMode(int(name.removeprefix("SnapModeChoice"))) for name, element in items.items() if name.startswith("SnapModeChoice") and element.Checked),
            SnapMode.NONE,
        )
    )
    window.On.GenerateEffectControlClips.Clicked = lambda event: FunctionalCallbacks.on_generate_effect_control_clips()
    window.On.Debug.Clicked = lambda ev: FunctionalCallbacks.on_debug(items)

    window.Show()
    disp.RunLoop()
    window.Hide()
