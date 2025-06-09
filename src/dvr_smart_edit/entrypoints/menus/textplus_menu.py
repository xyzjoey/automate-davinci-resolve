from ...extended_resolve import davinci_resolve_module
from ...resolve_types import PyRemoteComposition, PyRemoteOperator
from ...smart_edit.constants import CharacterLevelStylingCopyMode
from ...smart_edit.errors import UserError
from ...smart_edit.textplus_custom_data import TextPlusCustomData
from ...smart_edit.ui.error_window import ErrorWindow
from ...smart_edit.ui.menu_factory import MenuFactory
from .. import textplus_clip


class TextplusMenuCallbacks:
    def __init__(self, composition: PyRemoteComposition, tool: PyRemoteOperator):
        self.composition = composition
        self.tool = tool

    def on_copy_style_for_clip(self):
        textplus_clip.on_copy_style_for_clip(self.composition)

    def on_copy_style_for_track(self):
        textplus_clip.on_copy_style_for_track(self.composition)

    def on_copy_style_for_all(self):
        textplus_clip.on_copy_style_for_all()

    def on_toggle_fit_to_textbox(self, enabled: bool):
        TextPlusCustomData.set_fit_to_textbox_enabled(self.tool, enabled)

        if enabled:
            textplus_clip.on_enable_fit_to_textbox(self.tool)
        else:
            textplus_clip.on_disable_fit_to_textbox(self.tool)

    def on_set_character_styling_level_copy_mode(self, mode: int):
        TextPlusCustomData.set_character_styling_level_copy_mode(self.composition, CharacterLevelStylingCopyMode(mode))

    def on_export_srt_for_track(self):
        textplus_clip.on_export_srt_for_track(self.composition)

    def on_export_srt_for_all(self):
        pass


def textplus_menu(composition: PyRemoteComposition):
    resolve = davinci_resolve_module.get_resolve()
    page = resolve._resolve.GetCurrentPage()

    tool = None

    if page == "fusion":
        tool = composition.ActiveTool
    else:
        tool = composition.Template

    if tool is None:
        ErrorWindow.log_and_pop(Exception("Cannot find target tool"))
        return

    if tool.ID != "TextPlus":
        ErrorWindow.log_and_pop(UserError("Text+ menu is not applicable to non Text+ node"))
        return

    if tool.Name.startswith("TextDodSimulate"):
        ErrorWindow.log_and_pop(UserError("Text+ menu is not allowed on TextDodSimulate node"))
        return

    character_styling_level_copy_mode = TextPlusCustomData.get_character_styling_level_copy_mode(composition)

    ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
    ui_manager = davinci_resolve_module.get_ui_manager()
    ui = ui_manager._ui_manager
    disp = ui_dispatcher._ui_dispatcher
    menu_factory = MenuFactory(ui_manager)

    char_level_style_copy_modes = menu_factory.multi_buttons()

    window = disp.AddWindow(
        {
            "WindowTitle": "Smart Edit Text+ Menu",
            "ID": "SmartEditTextplusMenu",
            "WindowFlags": {"SplashScreen": True},
            "Events": {
                "MouseMove": True,
                "MouseRelease": True,
                # "Leave": True,  # `Leave` event + create other window -> davinci error (KeyError: 'On')
                "FocusOut": True,
                "Close": True,
            },
        },
        [
            ui.VGroup(
                [
                    menu_factory.header1(
                        {
                            "Text": "Text+ Utilites",
                        }
                    ),
                    ui.Label({"Text": f"Node: {tool.Name}"}),
                    menu_factory.separater(),
                    menu_factory.header2(
                        {
                            "Text": "Styling",
                        }
                    ),
                    menu_factory.horizontal_padding(
                        menu_factory.control_label(
                            {
                                "Text": "Copy Style from Media Pool",
                            }
                        ),
                        ui.HGroup(
                            [
                                ui.Button({"Text": "to This Clip", "ID": "CopyStyleForClip"}),
                                ui.Button({"Text": "to This Track", "ID": "CopyStyleForTrack"}),
                                ui.Button({"Text": "to All", "ID": "CopyStyleForAll"}),
                            ]
                        ),
                        menu_factory.control_label(
                            {
                                "Text": "Fit to Text Box",
                            }
                        ),
                        menu_factory.horizontal_center(
                            ui.CheckBox(
                                {
                                    "Text": "Fit to Text Box",
                                    "ID": "FitToTextBox",
                                    "Checked": TextPlusCustomData.get_fit_to_textbox_enabled(tool),
                                }
                            ),
                        ),
                    ),
                    menu_factory.separater(),
                    menu_factory.header2(
                        {
                            "Text": "Options on Copied",
                        }
                    ),
                    menu_factory.horizontal_padding(
                        menu_factory.control_label(
                            {
                                "Text": "Character Level Styling Mode",
                            }
                        ),
                        menu_factory.horizontal_center(
                            *char_level_style_copy_modes.create_elements(
                                {
                                    "ID": "CharacterLevelStyleCopyMode{index}",
                                    "Weight": 0.0,
                                },
                                [
                                    {
                                        "Text": "None",
                                        "Checked": CharacterLevelStylingCopyMode.NONE == character_styling_level_copy_mode,
                                    },
                                    {
                                        "Text": "Map to Lines",
                                        "Checked": CharacterLevelStylingCopyMode.MAP_TO_LINES == character_styling_level_copy_mode,
                                    },
                                ],
                            ),
                        ),
                    ),
                    menu_factory.separater(),
                    menu_factory.header2(
                        {
                            "Text": "Subtitle",
                        }
                    ),
                    menu_factory.horizontal_padding(
                        menu_factory.label_and_controls(
                            {
                                "Text": "Export SRT",
                            },
                            [
                                ui.Button({"Text": "from This Track", "ID": "ExportSrtForTrack"}),
                                ui.Button({"Text": "from All (WIP)", "ID": "ExportSrtForAll"}),
                            ],
                        ),
                    ),
                    menu_factory.separater(),
                    ui.VGap(0, 10),
                    menu_factory.horizontal_center(
                        ui.Button({"Text": "Close", "ID": "Close"}),
                    ),
                ],
            ),
        ],
    )

    old_mouse_pos = None

    def drag_window(ev):
        nonlocal old_mouse_pos
        new_mouse_pos = ev["GlobalPos"]

        if old_mouse_pos is not None:
            window_pos = window.Pos()
            window_pos[1] += new_mouse_pos[1] - old_mouse_pos[1]
            window_pos[2] += new_mouse_pos[2] - old_mouse_pos[2]
            window.Move(window_pos)

        old_mouse_pos = new_mouse_pos

    def reset_mouse_pos(ev):
        nonlocal old_mouse_pos
        old_mouse_pos = None

    def on_close(event):
        disp.ExitLoop()
        window.Hide()

    def on_focus_out(event):
        # click outside window immediately -> "OtherFocusReason"
        # click outside window after certain operation -> "ActiveWindowFocusReason"
        # click on nested element -> "MouseFocusReason"
        if event["Reason"] != "MouseFocusReason":
            on_close(event)

    def focus_window_on_exit(func):
        try:
            func()
        finally:
            window.SetFocus("ActiveWindowFocusReason")

    # window control
    window.On.SmartEditTextplusMenu.Close = on_close
    window.On.SmartEditTextplusMenu.MouseMove = drag_window
    window.On.SmartEditTextplusMenu.MouseRelease = reset_mouse_pos
    window.On.SmartEditTextplusMenu.FocusOut = on_focus_out
    window.On.Close.Clicked = on_close
    # functional callbacks
    callbacks = TextplusMenuCallbacks(composition, tool)
    char_level_style_copy_modes.register_callbacks(window, callbacks.on_set_character_styling_level_copy_mode)
    window.On.CopyStyleForClip.Clicked = lambda event: focus_window_on_exit(callbacks.on_copy_style_for_clip)
    window.On.CopyStyleForTrack.Clicked = lambda event: focus_window_on_exit(callbacks.on_copy_style_for_track)
    window.On.CopyStyleForAll.Clicked = lambda event: focus_window_on_exit(callbacks.on_copy_style_for_all)
    window.On.FitToTextBox.Clicked = lambda event: focus_window_on_exit(lambda: callbacks.on_toggle_fit_to_textbox(enabled=event["On"]))
    window.On.ExportSrtForTrack.Clicked = lambda event: focus_window_on_exit(callbacks.on_export_srt_for_track)
    window.On.ExportSrtForAll.Clicked = lambda event: focus_window_on_exit(callbacks.on_export_srt_for_all)

    window.Resize((350, 500))
    window.Show()
    window.SetFocus("ActiveWindowFocusReason")
    disp.RunLoop()
