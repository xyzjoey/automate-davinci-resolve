import importlib.metadata
import time
import traceback
from contextlib import contextmanager
from pprint import pprint

from ...extended_resolve import davinci_resolve_module
from ...extended_resolve.textplus import TextPlusComposition
from ...extended_resolve.track import TrackHandle
from ...extended_resolve.ui_dispatcher import UiDispatcher
from ...resolve_types import PyRemoteComposition
from ...smart_edit.constants import SnapMode
from ...smart_edit.effect_control import EffectControl
from ...smart_edit.smart_edit_bin import SmartEditBin
from ...smart_edit.textplus_utilities import TextPlusUtilities
from ...smart_edit.ui.error_window import ErrorWindow
from ...smart_edit.ui.loading_window import LoadingWindow
from ...smart_edit.ui.menu_factory import MenuFactory
from .. import textplus_clip
from ..script_utils import ScriptUtils


class TextplusMenuCallbacks:
    def __init__(self, composition: PyRemoteComposition):
        self.composition = composition

    def on_copy_style_for_clip(self):
        textplus_clip.on_copy_style_for_clip(self.composition)

    def on_copy_style_for_track(self):
        textplus_clip.on_copy_style_for_track(self.composition)

    def on_copy_style_for_all(self):
        textplus_clip.on_copy_style_for_all()

    def on_fit_textbox_for_clip(self):
        textplus_clip.on_fit_textbox_for_clip(self.composition)

    def on_fit_textbox_for_track(self):
        pass
        # textplus_clip.on_fit_textbox_for_track(self.composition)

    def on_fit_textbox_for_all(self):
        pass
        # textplus_clip.on_fit_textbox_for_all()

    def on_export_srt_for_track(self):
        textplus_clip.on_export_srt_for_track(self.composition)

    def on_export_srt_for_all(self):
        pass


def textplus_menu(composition: PyRemoteComposition):
    ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
    ui_manager = davinci_resolve_module.get_ui_manager()
    ui = ui_manager._ui_manager
    disp = ui_dispatcher._ui_dispatcher
    menu_factory = MenuFactory(ui_manager)

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
                        ui.HGroup(
                            [
                                ui.Button({"Text": "for This Clip", "ID": "FitTextBoxForClip"}),
                                # ui.Button({"Text": "for This Track", "ID": "FitTextBoxForTrack"}),
                                # ui.Button({"Text": "for All", "ID": "FitTextBoxForAll"}),
                            ]
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
    # functional callbacks
    callbacks = TextplusMenuCallbacks(composition)
    window.On.CopyStyleForClip.Clicked = lambda event: focus_window_on_exit(callbacks.on_copy_style_for_clip)
    window.On.CopyStyleForTrack.Clicked = lambda event: focus_window_on_exit(callbacks.on_copy_style_for_track)
    window.On.CopyStyleForAll.Clicked = lambda event: focus_window_on_exit(callbacks.on_copy_style_for_all)
    window.On.FitTextBoxForClip.Clicked = lambda event: focus_window_on_exit(callbacks.on_fit_textbox_for_clip)
    window.On.FitTextBoxForTrack.Clicked = lambda event: focus_window_on_exit(callbacks.on_fit_textbox_for_track)
    window.On.FitTextBoxForAll.Clicked = lambda event: focus_window_on_exit(callbacks.on_fit_textbox_for_all)
    window.On.ExportSrtForTrack.Clicked = lambda event: focus_window_on_exit(callbacks.on_export_srt_for_track)
    window.On.ExportSrtForAll.Clicked = lambda event: focus_window_on_exit(callbacks.on_export_srt_for_all)

    window.Resize((350, 350))
    window.Show()
    window.SetFocus("ActiveWindowFocusReason")
    disp.RunLoop()
