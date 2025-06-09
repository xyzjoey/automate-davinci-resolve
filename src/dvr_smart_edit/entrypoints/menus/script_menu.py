import importlib.metadata
from pprint import pprint

from ...extended_resolve import davinci_resolve_module
from ...smart_edit.constants import EffectType, SnapMode
from ...smart_edit.effect_control import EffectControl
from ...smart_edit.effect_defines import (
    DEFAULT_EFFECT_TRACKS_SETTINGS,
    EffectControlTrackSettings,
    EffectTrackSettings,
    EffectTracksSettings,
)
from ...smart_edit.errors import UserError
from ...smart_edit.fusion_custom_data import FusionCustomData
from ...smart_edit.smart_edit_bin import SmartEditBin
from ...smart_edit.textplus_utilities import TextPlusUtilities
from ...smart_edit.ui import menu_factory
from ...smart_edit.ui.error_window import ErrorWindow
from ...smart_edit.ui.loading_window import LoadingWindow
from ...smart_edit.ui.menu import Menu


class MenuCallbacks:
    @staticmethod
    def on_import_smart_edit_bin():
        with LoadingWindow("Bin", "Importing bin.."):
            SmartEditBin.import_bin()

    @staticmethod
    def on_generate_textplus_clips(**kw):
        if "subtitle_track_index" in kw and kw["subtitle_track_index"] is None:
            ErrorWindow.log_and_pop(UserError("Missing subtitle track"))
            return
        elif "srt_file_path" in kw and not kw["srt_file_path"]:
            ErrorWindow.log_and_pop(UserError("Missing SRT file path"))
            return

        with LoadingWindow("Text+", "Generating clips..."):
            TextPlusUtilities.generate_textplus_clips(**kw)

    @staticmethod
    def on_generate_effect_control_clips():
        with LoadingWindow("EffectControl", "Generating clips..."):
            EffectControl.generate_effect_control_clips()

    @staticmethod
    def on_toggle_init_fusion(enabled):
        FusionCustomData.set_init_fusion_enabled(enabled)

    @staticmethod
    def on_debug(menu: Menu):
        print("on_debug!")

        # settings = get_effect_tracks_settings(menu)

        # pprint(settings)


def smart_edit_menu():
    menu = SmartEditMainMenu()
    menu.show_and_run()


class SmartEditMainMenu:
    def __init__(self):
        ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
        ui_manager = davinci_resolve_module.get_ui_manager()

        self.menu = Menu(
            ui_dispatcher,
            ui_manager,
            {
                "WindowTitle": "Smart Edit Menu",
                "ID": "SmartEditMenu",
            },
        )
        self.enrich_menu()

        self.auto_save_effect_track_settings_enabled = True

    def show_and_run(self):
        self.menu.show_and_run()

    def enrich_menu(self):
        version = importlib.metadata.version("dvr_smart_edit")

        ui_factory = self.menu.ui_factory
        ui = ui_factory._ui

        self.menu.add_elements(
            ui.VGroup(
                [
                    ui.Label(
                        {
                            "ID": "VersionLabel",
                            "Text": f"version: {version}",
                            "Weight": 0.0,
                        }
                    ),
                    ui_factory.tabs("MainTabs"),
                ],
            ),
        )

        main_tabs = self.menu.find_group("MainTabs")

        self.add_text_tab(main_tabs)
        self.add_effect_tab(main_tabs)
        self.add_settings_tab(main_tabs)

        self.menu.window.resize(width=500)

    def add_text_tab(self, main_tabs):
        ui_factory = self.menu.ui_factory
        ui = ui_factory._ui

        main_tabs.add_tab(
            "Text+",
            ui_factory.vertical_center(
                ui_factory.header2(
                    {
                        "Text": "Generate Text+",
                    }
                ),
                ui_factory.horizontal_padding(
                    ui_factory.label_and_controls(
                        {
                            "Text": "Source Type",
                        },
                        [
                            ui_factory.multi_buttons(
                                "GenerateTextSourceType",
                                [
                                    {
                                        "Text": "Subtitle Track",
                                        "Checked": True,
                                    },
                                    {
                                        "Text": "SRT",
                                    },
                                ],
                            ),
                        ],
                    ),
                    ui.Stack(
                        {
                            "ID": "GenerateTextSource",
                        },
                        [
                            ui_factory.label_and_controls(
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
                            ui_factory.label_and_controls(
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
                    ui_factory.label_and_controls(
                        {
                            "Text": "Target Track (WIP)",
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
                    ui_factory.label_and_controls(
                        {
                            "Text": "Snap Mode",
                            "ToolTip": "Select the snapping mode for generating clips.",
                        },
                        ui_factory.multi_buttons(
                            "GenerateTextSnapMode",
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
                        ),
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
        )

        def on_source_type(event, index):
            self.menu.window.find_item("GenerateTextSource").CurrentIndex = index

        def on_refresh_subtitle_track_list(event):
            resolve = davinci_resolve_module.get_resolve()
            timeline = resolve.get_current_timeline()

            if timeline is None:
                return

            subtitle_track_dropdown_list = self.menu.window.find_item("GenerateTextSubtitleTrack")

            not_selected = subtitle_track_dropdown_list.CurrentIndex == -1
            subtitle_track_dropdown_list.Clear()

            for i, track_handle in enumerate(timeline.iter_tracks(track_type="subtitle")):
                track_name = timeline._timeline.GetTrackName(track_handle.type, track_handle.index)
                item_name = f"ST{track_handle.index} {track_name}"

                subtitle_track_dropdown_list.AddItem(item_name)

                if not_selected and timeline.get_track_enabled(track_handle):
                    subtitle_track_dropdown_list.CurrentIndex = i

        def on_browse_srt_file_path(event):
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
                self.menu.window.find_item("GenerateTextSrtFile").Text = str(file_path)

        def get_generate_text_args():
            source_type_index = self.menu.find_group("GenerateTextSourceType").get_selected_index()
            snap_mode_index = self.menu.find_group("GenerateTextSnapMode").get_selected_index()
            snap_mode = SnapMode(snap_mode_index) if snap_mode_index is not None else SnapMode.NONE

            args = {
                "snap_mode": snap_mode,
            }

            if source_type_index == 0:
                sutitle_track_code = self.menu.window.find_item("GenerateTextSubtitleTrack").CurrentText

                if sutitle_track_code:
                    sutitle_track_code = sutitle_track_code.split(" ", 1)[0]
                    sutitle_track_index = int(sutitle_track_code.removeprefix("ST"))
                    args["subtitle_track_index"] = sutitle_track_index
                else:
                    args["subtitle_track_index"] = None
            else:
                srt_file_path = self.menu.window.find_item("GenerateTextSrtFile").Text
                args["srt_file_path"] = srt_file_path

            return args

        # reset ui
        on_refresh_subtitle_track_list(None)

        # ui control callbacks
        self.menu.find_group("GenerateTextSourceType").register_on_select(on_source_type)
        self.menu.window.register_event("GenerateTextSubtitleTrackRefresh", "Clicked", on_refresh_subtitle_track_list)
        self.menu.window.register_event("GenerateTextSrtFileBrowse", "Clicked", on_browse_srt_file_path)

        # functional callbacks
        self.menu.window.register_event("GenerateText", "Clicked", lambda event: MenuCallbacks.on_generate_textplus_clips(**get_generate_text_args()))

    def add_effect_tab(self, main_tabs):
        ui_factory = self.menu.ui_factory
        ui = ui_factory._ui

        main_tabs.add_tab(
            "EffectControl",
            ui_factory.vertical_center(
                ui_factory.header2(
                    {
                        "Text": "Effect Tracks Settings",
                    }
                ),
                ui_factory.horizontal_padding(
                    ui.VGroup({"ID": "EffectTracksSettings"}, []),
                ),
                ui_factory.separater(),
                ui_factory.header2(
                    {
                        "Text": "Add Effect Control Clips",
                    }
                ),
                ui_factory.horizontal_padding(
                    ui_factory.horizontal_center(
                        ui_factory.multi_buttons(
                            "AddEffectControlMethod",
                            [
                                {
                                    "Text": "Generate from Track",
                                    "Checked": True,
                                },
                                {
                                    "Text": "Add Manually",
                                },
                            ],
                        ),
                    ),
                    ui.Stack(
                        {
                            "ID": "AddEffectControlStack",
                        },
                        [
                            ui.VGroup(
                                [
                                    ui_factory.label_and_controls(
                                        {
                                            "Text": "Source Track (WIP)",
                                        },
                                        [
                                            ui.ComboBox(
                                                {
                                                    "ID": "GenerateEffectControlSourceTrack",
                                                }
                                            ),
                                            ui.Button(
                                                {
                                                    "ID": "GenerateEffectControlSourceTrackRefresh",
                                                    "Text": "Refresh",
                                                    "Weight": 0,
                                                }
                                            ),
                                        ],
                                    ),
                                    ui_factory.label_and_controls(
                                        {
                                            "Text": "Target Track (WIP)",
                                        },
                                        [
                                            ui.LineEdit(
                                                {
                                                    "ID": "GenerateEffectControlTargetTrack",
                                                    "Text": "Generated EffectControl",
                                                    "ReadOnly": True,
                                                }
                                            ),
                                        ],
                                    ),
                                    ui_factory.empty_line(),
                                    ui.Button(
                                        {
                                            "ID": "GenerateEffectControlClips",
                                            "Text": "Generate EffectControl Clips",
                                            "ToolTip": "Generate EffectControl clips according to `Generated Text+` track.\nOverwrite `Generated Control` track if already exist.",
                                            "Weight": 0.0,
                                        }
                                    ),
                                ]
                            ),
                            ui.VGroup(
                                [
                                    ui_factory.horizontal_center(
                                        ui.Label(
                                            {
                                                "Text": "Use EffectControl Clip from SmartEdit bin",
                                            }
                                        ),
                                    ),
                                    ui_factory.empty_line(),
                                    ui.Button(
                                        {
                                            "ID": "ImportSmartEditBin",
                                            "Text": "Import SmartEdit Bin",
                                            "ToolTip": "the SmartEdit bin contains EffectControl, AdjustFusion, etc.",
                                            "Weight": 0.0,
                                        }
                                    ),
                                ]
                            ),
                        ],
                    ),
                ),
            ),
        )

        self.enrich_effect_tracks_settings()

        def on_add_effect_control_method(event, index):
            self.menu.window.find_item("AddEffectControlStack").CurrentIndex = index

        self.menu.find_group("AddEffectControlMethod").register_on_select(on_add_effect_control_method)
        self.menu.window.find_item("GenerateEffectControlSourceTrack").AddItem("Generated Text+")

        # functional callbacks
        self.menu.window.register_event("GenerateEffectControlClips", "Clicked", lambda event: MenuCallbacks.on_generate_effect_control_clips())
        self.menu.window.register_event("ImportSmartEditBin", "Clicked", lambda event: MenuCallbacks.on_import_smart_edit_bin())

    def add_settings_tab(self, main_tabs):
        ui_factory = self.menu.ui_factory
        ui = ui_factory._ui

        main_tabs.add_tab(
            "Settings",
            ui_factory.vertical_center(
                ui_factory.horizontal_center(
                    ui.CheckBox(
                        {
                            "ID": "EnableInitFusionOnProjectOpen",
                            "Text": "Initialize Fusion Page on Project loaded",
                            "ToolTip": (
                                "Opens Fusion Page automatically on project loaded.\n"
                                "Required for full Fusion UI functionality.\n"
                                "If disabled, Smart Edit Text+ Menu won't open until Fusion Page is ever manually opened.\n"
                                "Changes to this setting will take effect after restarting DaVinci Resolve."
                            ),
                            "Checked": FusionCustomData.get_init_fusion_enabled(),
                            "Weight": 0.0,
                        }
                    ),
                ),
                ui_factory.horizontal_center(
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
        )

        # functional callbacks
        self.menu.window.register_event(
            "EnableInitFusionOnProjectOpen",
            "Clicked",
            lambda event: MenuCallbacks.on_toggle_init_fusion(self.menu.window.find_item("EnableInitFusionOnProjectOpen").Checked),
        )
        self.menu.window.register_event("Debug", "Clicked", lambda event: MenuCallbacks.on_debug(self.menu))

    def enrich_effect_tracks_settings(self):
        ui_factory = self.menu.ui_factory
        ui = ui_factory._ui

        effect_tracks_settings = self.menu.window.find_item("EffectTracksSettings")
        effect_tracks_settings.AddChild(
            ui.VGroup(
                [
                    ui_factory.label_and_controls(
                        {
                            "Text": "Preset",
                        },
                        ui.ComboBox(
                            {
                                "ID": "EffectTrackPreset",
                            }
                        ),
                    ),
                    ui_factory.horizontal_center(
                        ui.Button(
                            {
                                "ID": "EffectTrackPresetLoad",
                                "Text": "Load from Preset",
                                "Weight": 0.0,
                            }
                        ),
                        ui.Button(
                            {
                                "ID": "EffectTrackPresetDelete",
                                "Text": "Delete Preset",
                                "Weight": 0.0,
                            }
                        ),
                    ),
                    ui_factory.separater(),
                    ui_factory.list("EffectControlTrackList"),
                    ui_factory.empty_line(),
                    ui_factory.horizontal_right(
                        ui.Button(
                            {
                                "ID": "EffectControlTrackListReset",
                                "Text": "Reset",
                                "Weight": 0.0,
                                # "StyleSheet": "padding: 0 20px; margin: 0px;",
                                # "Visible": is_dev,
                            }
                        ),
                        ui.Button(
                            {
                                "ID": "EffectControlTrackListAddItem",
                                "Text": "+",
                                "Weight": 0.0,
                                # "StyleSheet": "padding: 0 20px; margin: 0px;",
                            }
                        ),
                    ),
                    ui_factory.separater(),
                    ui_factory.label_and_controls(
                        {
                            "Text": "Save as Preset",
                        },
                        [
                            ui.LineEdit(
                                {
                                    "ID": "EffectTrackSaveAsPresetName",
                                }
                            ),
                            ui.Button(
                                {
                                    "ID": "EffectTrackSaveAsPreset",
                                    "Text": "Save",
                                    "Weight": 0.0,
                                }
                            ),
                        ],
                    ),
                ]
            )
        )

        effect_control_track_list = self.menu.find_group("EffectControlTrackList")

        def on_item_added(item_id, index, element):
            last_effect_control_number = 0

            for curr_item_id, item_element in effect_control_track_list.iter_items_before(before_item_id=item_id):
                track_name = item_element.Find(f"EffectControlTrackName{curr_item_id}")
                number_str = track_name.PlaceholderText.removeprefix("Effect Control ")

                try:
                    number = int(number_str)
                    last_effect_control_number = max(last_effect_control_number, number)
                except:
                    pass

            element.AddChild(
                ui.VGroup(
                    {
                        "Weight": 1,
                    },
                    [
                        ui.HGroup(
                            [
                                ui.Label(
                                    {
                                        "ID": f"EffectControlTrackLabel{item_id}",
                                        "Text": f"Effect Control Track",
                                    }
                                ),
                                ui.HGap(0, 10),
                                ui.Button(
                                    {
                                        "ID": f"EffectControlTrackListRemoveItem{item_id}",
                                        "Text": "-",
                                        "Weight": 0.0,
                                        "StyleSheet": "padding: 0 10px; margin: 0px;",
                                    }
                                ),
                            ]
                        ),
                        ui_factory.horizontal_padding(
                            ui_factory.label_and_controls(
                                {
                                    "Text": "Track Name",
                                },
                                [
                                    ui.LineEdit(
                                        {
                                            "ID": f"EffectControlTrackName{item_id}",
                                            "PlaceholderText": f"Effect Control {last_effect_control_number+1}",
                                        }
                                    )
                                ],
                            ),
                            ui.VGroup(
                                {
                                    "ID": f"EffectTracks{item_id}",
                                }
                            ),
                        ),
                    ],
                )
            )

            self.add_effect_track_list(item_id, self.menu.window.find_item(f"EffectTracks{item_id}"))

            self.menu.window.register_event(
                f"EffectControlTrackListRemoveItem{item_id}",
                "Clicked",
                lambda event: effect_control_track_list.remove_item(item_id),
            )

            self.auto_save_effect_track_settings()

        def on_item_removed():
            self.auto_save_effect_track_settings()

        effect_control_track_list.register_on_item_added(on_item_added)
        effect_control_track_list.register_on_item_removed(on_item_removed)

        self.menu.window.register_event("EffectControlTrackListAddItem", "Clicked", lambda event: effect_control_track_list.add_item())
        self.menu.window.register_event("EffectControlTrackListReset", "Clicked", lambda event: self.reset_effect_track_settings())

        self.load_effect_track_settings()

    def add_effect_track_list(self, parent_id, parent):
        ui_factory = self.menu.ui_factory
        ui = ui_factory._ui

        parent.AddChild(
            ui.VGroup(
                [
                    ui_factory.list(f"EffectTrackList{parent_id}"),
                    ui_factory.horizontal_right(
                        ui.Button(
                            {
                                "ID": f"EffectTrackListAddItem{parent_id}",
                                "Text": "+",
                                "Weight": 0.0,
                                "StyleSheet": "padding: 0 20px; margin: 0px;",
                            }
                        ),
                    ),
                ]
            )
        )

        effect_control_track_list = self.menu.find_group("EffectControlTrackList")
        effect_track_list = self.menu.find_group(f"EffectTrackList{parent_id}")

        def on_item_added(item_id, index, element):
            last_effect_track_number = 0

            for curr_parent_id in effect_control_track_list.get_items():
                curr_effect_track_list = self.menu.find_group(f"EffectTrackList{curr_parent_id}")

                for curr_id, item_element in curr_effect_track_list.iter_items_before(before_item_id=item_id):
                    track_name = item_element.Find(f"EffectTrackName{curr_id}")
                    number_str = track_name.PlaceholderText.removeprefix("Effect ")

                    try:
                        number = int(number_str)
                        last_effect_track_number = max(last_effect_track_number, number)
                    except:
                        pass

            element.AddChild(
                ui.VGroup(
                    [
                        ui.HGroup(
                            [
                                ui.Label(
                                    {
                                        "ID": f"EffectTrackLabel{item_id}",
                                        "Text": f"Effect Track",
                                    }
                                ),
                                ui.HGap(0, 10),
                                ui.Button(
                                    {
                                        "ID": f"EffectTrackListMoveItemUp{item_id}",
                                        "Text": "Up",
                                        "Weight": 0.0,
                                        "StyleSheet": "padding: 0 10px; margin: 0px;",
                                    }
                                ),
                                ui.Button(
                                    {
                                        "ID": f"EffectTrackListMoveItemDown{item_id}",
                                        "Text": "Down",
                                        "Weight": 0.0,
                                        "StyleSheet": "padding: 0 10px; margin: 0px;",
                                    }
                                ),
                                ui.Button(
                                    {
                                        "ID": f"EffectTrackListRemoveItem{item_id}",
                                        "Text": "-",
                                        "Weight": 0.0,
                                        "StyleSheet": "padding: 0 10px; margin: 0px;",
                                    }
                                ),
                            ]
                        ),
                        ui_factory.horizontal_padding(
                            ui_factory.label_and_controls(
                                {
                                    "Text": "Track Name",
                                },
                                [
                                    ui.LineEdit(
                                        {
                                            "ID": f"EffectTrackName{item_id}",
                                            "PlaceholderText": f"Effect {last_effect_track_number+1}",
                                        }
                                    )
                                ],
                            ),
                            ui_factory.label_and_controls(
                                {
                                    "Text": "Effect Type",
                                },
                                [
                                    ui.ComboBox(
                                        {
                                            "ID": f"EffectTrackEffectType{item_id}",
                                        }
                                    )
                                ],
                            ),
                            ui.Label(
                                {
                                    "Text": "Media Pool Filter",
                                }
                            ),
                            ui_factory.horizontal_left_padding(
                                ui_factory.label_and_controls(
                                    {
                                        "Text": "by Keyword",
                                    },
                                    [
                                        ui.LineEdit(
                                            {
                                                "ID": f"EffectTrackKeywordFilter{item_id}",
                                            }
                                        )
                                    ],
                                ),
                                ui_factory.label_and_controls(
                                    {
                                        "Text": "by Folder",
                                    },
                                    [
                                        ui.LineEdit(
                                            {
                                                "ID": f"EffectTrackFolderFilter{item_id}",
                                            }
                                        )
                                    ],
                                ),
                            ),
                        ),
                    ]
                )
            )

            effect_type = self.menu.window.find_item(f"EffectTrackEffectType{item_id}")
            effect_type.AddItems([effect_type.get_label() for effect_type in EffectType])
            effect_type.CurrentIndex = EffectType.INSERT_VIDEO.value

            self.menu.window.register_event(f"EffectTrackListRemoveItem{item_id}", "Clicked", lambda event: effect_track_list.remove_item(item_id))

            self.auto_save_effect_track_settings()

        def on_item_removed():
            self.auto_save_effect_track_settings()

        effect_track_list.register_on_item_added(on_item_added)
        effect_track_list.register_on_item_removed(on_item_removed)

        self.menu.window.register_event(f"EffectTrackListAddItem{parent_id}", "Clicked", lambda event: effect_track_list.add_item())

    def get_effect_tracks_settings(self) -> EffectTracksSettings:
        effect_control_track_list = self.menu.find_group("EffectControlTrackList")

        settings = EffectTracksSettings(effect_control_tracks=[])

        for effect_control_track_id, effect_control_track_ui in effect_control_track_list.get_items().items():
            effect_control_track_name_ui = effect_control_track_ui.Find(f"EffectControlTrackName{effect_control_track_id}")
            effect_track_list = self.menu.find_group(f"EffectTrackList{effect_control_track_id}")

            effect_tracks = []

            for effect_track_id, effect_track_ui in effect_track_list.get_items().items():
                effect_track_name_ui = effect_track_ui.Find(f"EffectTrackName{effect_track_id}")
                effect_type_ui = effect_track_ui.Find(f"EffectTrackEffectType{effect_track_id}")
                filter_by_keyword_ui = effect_track_ui.Find(f"EffectTrackKeywordFilter{effect_track_id}")
                filter_by_folder_ui = effect_track_ui.Find(f"EffectTrackFolderFilter{effect_track_id}")

                effect_tracks.append(
                    EffectTrackSettings(
                        track_name=effect_track_name_ui.Text,
                        track_name_default=effect_track_name_ui.PlaceholderText,
                        effect_type=EffectType(effect_type_ui.CurrentIndex),
                        media_pool_filter_by_keyword=list(filter(lambda token: token != "", map(str.strip, filter_by_keyword_ui.Text.split(",")))),
                        media_pool_filter_by_folder=list(filter(lambda token: token != "", map(str.strip, filter_by_folder_ui.Text.split(",")))),
                    )
                )

            settings.effect_control_tracks.append(
                EffectControlTrackSettings(
                    track_name=effect_control_track_name_ui.Text,
                    track_name_default=effect_control_track_name_ui.PlaceholderText,
                    effect_tracks=effect_tracks,
                )
            )

        return settings

    def set_effect_track_settings(self, settings: EffectTracksSettings):
        self.auto_save_effect_track_settings_enabled = False

        effect_control_track_list = self.menu.find_group("EffectControlTrackList")
        effect_control_track_list.reset_items(len(settings.effect_control_tracks))

        for effect_control_track, (effect_control_track_id, effect_control_track_ui) in zip(
            settings.effect_control_tracks, effect_control_track_list.get_items().items()
        ):
            effect_control_track_name_ui = effect_control_track_ui.Find(f"EffectControlTrackName{effect_control_track_id}")
            effect_control_track_name_ui.Text = effect_control_track.track_name
            effect_control_track_name_ui.PlaceholderText = effect_control_track.track_name_default

            effect_track_list = self.menu.find_group(f"EffectTrackList{effect_control_track_id}")
            effect_track_list.reset_items(len(effect_control_track.effect_tracks))

            for effect_track, (effect_track_id, effect_track_ui) in zip(effect_control_track.effect_tracks, effect_track_list.get_items().items()):
                effect_track_name_ui = effect_track_ui.Find(f"EffectTrackName{effect_track_id}")
                effect_track_name_ui.Text = effect_track.track_name
                effect_track_name_ui.PlaceholderText = effect_track.track_name_default

                effect_type_ui = effect_track_ui.Find(f"EffectTrackEffectType{effect_track_id}")
                effect_type_ui.CurrentIndex = effect_track.effect_type.value

                if effect_track.media_pool_filter_by_keyword:
                    filter_by_keyword_ui = effect_track_ui.Find(f"EffectTrackKeywordFilter{effect_track_id}")
                    filter_by_keyword_ui.Text = ", ".join(effect_track.media_pool_filter_by_keyword)

                if effect_track.media_pool_filter_by_folder:
                    filter_by_folder_ui = effect_track_ui.Find(f"EffectTrackFolderFilter{effect_track_id}")
                    filter_by_folder_ui.Text = ", ".join(effect_track.media_pool_filter_by_folder)

        self.auto_save_effect_track_settings_enabled = True

    def auto_save_effect_track_settings(self):
        if self.auto_save_effect_track_settings_enabled:
            settings = self.get_effect_tracks_settings()
            FusionCustomData.set_effect_tracks_settings(settings)

    def load_effect_track_settings(self):
        settings = FusionCustomData.get_effect_tracks_settings()
        self.set_effect_track_settings(settings)

    def reset_effect_track_settings(self):
        FusionCustomData.set_effect_tracks_settings(None)
        self.set_effect_track_settings(DEFAULT_EFFECT_TRACKS_SETTINGS)
