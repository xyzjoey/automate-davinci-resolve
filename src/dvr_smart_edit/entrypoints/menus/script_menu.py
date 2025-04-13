import importlib.metadata
import tkinter as tk
from pathlib import Path
from pprint import pprint
from tkinter import filedialog

from ...extended_resolve import davinci_resolve_module
from ...extended_resolve.textplus import TextPlusComposition
from ...extended_resolve.track import TrackHandle
from ...extended_resolve.ui_dispatcher import UiDispatcher
from ...smart_edit.constants import SnapMode
from ...smart_edit.effect_control import EffectControl
from ...smart_edit.errors import UserError
from ...smart_edit.smart_edit_bin import SmartEditBin
from ...smart_edit.textplus_utilities import TextPlusUtilities
from ...smart_edit.ui.error_window import ErrorWindow
from ...smart_edit.ui.loading_window import LoadingWindow
from ...smart_edit.ui.menu_factory import MenuFactory
from ...smart_edit.user_settings import UserSettings
from ..script_utils import ScriptUtils


class MenuCallbacks:
    def on_import_smart_edit_bin(self):
        with LoadingWindow("Bin", "Importing bin.."):
            SmartEditBin.import_bin()

    def on_generate_textplus_clips(self, **kw):
        with LoadingWindow("Text+", "Generating clips..."):
            TextPlusUtilities.generate_textplus_clips(**kw)

    def on_generate_effect_control_clips(self):
        with LoadingWindow("EffectControl", "Generating clips..."):
            EffectControl.generate_effect_control_clips()

    def on_toggle_init_fusion(self, enabled):
        UserSettings.set_init_fusion_enabled(enabled)

    def on_debug(self, *args, **kw):
        pass


def smart_edit_menu():
    version = importlib.metadata.version("dvr_smart_edit")

    ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
    ui_manager = davinci_resolve_module.get_ui_manager()
    ui = ui_manager._ui_manager
    disp = ui_dispatcher._ui_dispatcher
    menu_factory = MenuFactory(ui_manager)

    menu_factory = MenuFactory(ui_manager)

    source_types = menu_factory.multi_buttons(
        {
            "ID": "SourceType{index}",
            "Weight": 0.0,
        },
        [
            {
                "Text": "Subtitle Track",
                "Checked": True,
            },
            {
                "Text": "SRT",
            },
        ],
    )
    snap_modes = menu_factory.multi_buttons(
        {
            "ID": "SnapMode{index}",
            "Weight": 0.0,
        },
        [
            {
                "Text": "None",
            },
            {
                "Text": "Auto",
                "ToolTip": "Snap to clips in the audio track with most clips.",
                "Checked": True,
            },
            # {
            #     "Text": "Choose Track (WIP)",
            # },
        ],
    )

    window = disp.AddWindow(
        {
            "WindowTitle": "Smart Edit Menu",
            "ID": "SmartEditMenu",
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
                            menu_factory.vertical_center(
                                menu_factory.horizontal_center(
                                    ui.Button(
                                        {
                                            "ID": "ImportSmartEditBin",
                                            "Text": "Import SmartEdit Bin",
                                            "ToolTip": "The SmartEdit bin contains EffectControl, AdjustFusion, etc.",
                                            "Weight": 0.0,
                                        }
                                    )
                                ),
                                menu_factory.horizontal_center(
                                    ui.Button(
                                        {
                                            "ID": "Debug",
                                            "Text": "Debug",
                                            # "Visible": False,
                                            "Weight": 0.0,
                                        }
                                    ),
                                ),
                            ),
                            # Text+ tab content
                            menu_factory.vertical_center(
                                menu_factory.header2(
                                    {
                                        "Text": "Generate Text+",
                                    }
                                ),
                                menu_factory.horizontal_padding(
                                    menu_factory.label_and_controls(
                                        {
                                            "Text": "Source Type",
                                        },
                                        source_types.get_elements(),
                                    ),
                                    ui.Stack(
                                        {
                                            "ID": "GenerateTextSource",
                                        },
                                        [
                                            menu_factory.label_and_controls(
                                                {
                                                    "Text": "Subtitle Track",
                                                },
                                                [
                                                    ui.ComboBox(
                                                        {
                                                            "ID": "GenerateTextSubtitleTrack",
                                                        }
                                                    ),
                                                    ui.Button(
                                                        {
                                                            "ID": "GenerateTextSubtitleTrackRefresh",
                                                            "Text": "Refresh",
                                                            "Weight": 0,
                                                        }
                                                    ),
                                                ],
                                            ),
                                            menu_factory.label_and_controls(
                                                {
                                                    "Text": "SRT File",
                                                },
                                                [
                                                    ui.LineEdit(
                                                        {
                                                            "ID": "GenerateTextSrtFile",
                                                        }
                                                    ),
                                                    ui.Button(
                                                        {
                                                            "ID": "GenerateTextSrtFileBrowse",
                                                            "Text": "Browse",
                                                            "Weight": 0,
                                                        }
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    menu_factory.label_and_controls(
                                        {
                                            "Text": "Target Track",
                                        },
                                        [
                                            ui.LineEdit(
                                                {
                                                    "ID": "GenerateTextTargetTrack",
                                                    "Text": "Generated Text+",
                                                    "ReadOnly": True,
                                                }
                                            )
                                        ],
                                    ),
                                    menu_factory.label_and_controls(
                                        {
                                            "Text": "Snap Mode",
                                            "ToolTip": "Select the snapping mode for generating clips.",
                                        },
                                        snap_modes.get_elements(),
                                    ),
                                    ui.Label(
                                        {
                                            "Text": "",
                                        }
                                    ),
                                    ui.Button(
                                        {
                                            "ID": "GenerateText",
                                            "Text": "Generate",
                                        }
                                    ),
                                ),
                            ),
                            # EffectControl tab content
                            menu_factory.vertical_center(
                                menu_factory.horizontal_center(
                                    ui.Button(
                                        {
                                            "ID": "GenerateEffectControlClips",
                                            "Text": "Generate EffectControl Clips",
                                            "ToolTip": "Generate EffectControl clips according to `Generated Text+` track.\nOverwrite `Generated Control` track if already exist.",
                                            "Weight": 0.0,
                                        }
                                    ),
                                )
                            ),
                            # Settings tab content
                            menu_factory.vertical_center(
                                menu_factory.horizontal_center(
                                    ui.CheckBox(
                                        {
                                            "ID": "EnableInitFusionOnProjectOpen",
                                            "Text": "Initialize Fusion Page on Project loaded",
                                            "ToolTip": (
                                                "Opens Fusion Page automatically on project loaded.\n"
                                                "Required for full Fusion UI functionality.\n"
                                                "If disabled, Smart Edit Text+ Menu won't open until Fusion Page is manually accessed.\n"
                                                "Changes to this setting will take effect after restarting DaVinci Resolve."
                                            ),
                                            "Checked": UserSettings.get_init_fusion_enabled(),
                                            "Weight": 0.0,
                                        }
                                    ),
                                ),
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
    items["MainTabs"].AddTab("Text+")
    items["MainTabs"].AddTab("EffectControl")
    items["MainTabs"].AddTab("Settings")
    items["MainStack"].CurrentIndex = 0

    def on_close(event):
        disp.ExitLoop()
        window.Hide()

    def on_tab_changed(event):
        items["MainStack"].CurrentIndex = event["Index"]

    def on_source_type(index):
        items["GenerateTextSource"].CurrentIndex = index

    def reset_subtitle_track_list():
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        if timeline is None:
            return

        items["GenerateTextSubtitleTrack"].Clear()

        for i, track_handle in enumerate(timeline.iter_tracks(track_type="subtitle")):
            track_name = timeline._timeline.GetTrackName(track_handle.type, track_handle.index)
            item_name = f"ST{track_handle.index} {track_name}"

            items["GenerateTextSubtitleTrack"].AddItem(item_name)

            if timeline.get_track_enabled(track_handle):
                items["GenerateTextSubtitleTrack"].CurrentIndex = i

    def get_snap_mode():
        index = snap_modes.get_selected_index(window)
        return SnapMode(index) if index is not None else SnapMode.NONE

    def browse_srt_file_path():
        fusion = davinci_resolve_module.get_fusion()
        file_path = fusion.RequestFile(
            "",
            "",
            {
                "FReqS_Filter": "Subtitle Files (*.srt)|*.srt",
                "FReqS_Tiitle": "Smart Edit - Import Subtitle",
            },
        )

        if file_path:
            items["GenerateTextSrtFile"].Text = str(file_path)

    def get_generate_text_args():
        source_type_index = source_types.get_selected_index(window)
        snap_mode_index = snap_modes.get_selected_index(window)
        snap_mode = SnapMode(snap_mode_index) if snap_mode_index is not None else SnapMode.NONE

        args = {
            "snap_mode": snap_mode,
        }

        if source_type_index == 0:
            sutitle_track_code = items["GenerateTextSubtitleTrack"].CurrentText.split(" ", 1)[0]
            sutitle_track_index = int(sutitle_track_code.removeprefix("ST"))
            args["subtitle_track_index"] = sutitle_track_index
        else:
            srt_file_path = items["GenerateTextSrtFile"].Text
            args["srt_file_path"] = srt_file_path

        return args

    window.On.SmartEditMenu.Close = on_close
    # ui control
    window.On.MainTabs.CurrentChanged = on_tab_changed
    source_types.register_callbacks(window, on_source_type)
    snap_modes.register_callbacks(window)
    window.On.GenerateTextSubtitleTrackRefresh.Clicked = lambda event: reset_subtitle_track_list()
    window.On.GenerateTextSrtFileBrowse.Clicked = lambda event: browse_srt_file_path()

    on_source_type(0)
    reset_subtitle_track_list()

    # items["GenerateTextFrom"].AddItem("Item1")
    # items["GenerateTextFrom"].AddItem("Item2")
    # items["GenerateTextFrom"].AddItem("Item3")
    # window.On.GenerateTextFrom.CurrentIndexChanged = lambda event: print(f"CurrentIndexChanged\n{event}")
    # window.On.GenerateTextFrom.CurrentTextChanged = lambda event: print(f"CurrentTextChanged\n{event}")
    # window.On.GenerateTextFrom.TextEdited = lambda event: print(f"TextEdited\n{event}")
    # window.On.GenerateTextFrom.EditTextChanged = lambda event: print(f"EditTextChanged\n{event}")
    # window.On.GenerateTextFrom.EditingFinished = lambda event: print(f"EditingFinished\n{event}")
    # window.On.GenerateTextFrom.ReturnPressed = lambda event: print(f"ReturnPressed\n{event}")
    # window.On.GenerateTextFrom.Activated = lambda event: print(f"Activated\n{event}")

    # functional callbacks
    menu_callbacks = MenuCallbacks()
    window.On.ImportSmartEditBin.Clicked = lambda event: menu_callbacks.on_import_smart_edit_bin()
    window.On.GenerateText.Clicked = lambda event: menu_callbacks.on_generate_textplus_clips(**get_generate_text_args())
    # window.On.GenerateTextFromSrt.Clicked = lambda event: menu_callbacks.on_generate_text_from_srt(get_snap_mode())
    window.On.GenerateEffectControlClips.Clicked = lambda event: menu_callbacks.on_generate_effect_control_clips()
    window.On.EnableInitFusionOnProjectOpen.Clicked = lambda event: menu_callbacks.on_toggle_init_fusion(items["EnableInitFusionOnProjectOpen"].Checked)
    window.On.Debug.Clicked = lambda ev: menu_callbacks.on_debug()

    window.Resize((450, 300))
    window.Show()
    disp.RunLoop()
