import traceback
from contextlib import ContextDecorator

from ...extended_resolve import davinci_resolve_module
from ...utils import log
from ..errors import UserError
from .error_window import ErrorWindow


class LoadingWindow(ContextDecorator):
    instances: list["LoadingWindow"] = []

    def __init__(self, title: str, message: str):
        self.title = title
        self.message = message

        self.ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
        self._window = None

        self._context = ErrorWindow.pop_on_error()

    def __enter__(self):
        ui = self.ui_dispatcher._ui_manager
        disp = self.ui_dispatcher._ui_dispatcher

        window = disp.AddWindow(
            {
                "WindowTitle": f"Smart Edit - {self.title}",
                "ID": "SmartEditLoading",
                "WindowFlags": {"CoverWindow": True},
                # "WindowModality": "WindowModal",  # it also block api call e.g. open page, insert clip to timeline
                "Margin": 0,
                "Spacing": 0,
            },
            [
                ui.VGroup(
                    {"Spacing": 20},
                    [
                        ui.VGap(0, 10),
                        ui.Label(
                            {
                                "ID": "Message",
                                "Text": self.message,
                                "Alignment": {
                                    "AlignVCenter": True,
                                    "AlignHCenter": True,
                                },
                                "WordWrap": True,
                            }
                        ),
                        ui.VGap(0, 10),
                    ],
                ),
            ],
        )

        def on_close(event):
            disp.ExitLoop()
            window.Hide()

        window.On.SmartEditLoading.Close = on_close

        window.Resize((500, 200))
        window.Show()

        self._window = window
        self.instances.append(self)

        self._context.__enter__()

        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            self._set_message("Finish")

        self._window.Hide()
        self.instances.remove(self)

        self._context.__exit__(exc_type, exc, exc_tb)

        return True

    def _set_message(self, message: str):
        items = self._window.GetItems()
        items["Message"]["Text"] = message

    @classmethod
    def set_message(cls, message: str, dispatch_log: bool = True):
        if len(cls.instances) == 0:
            return

        if dispatch_log:
            log.info(f"{cls.instances[-1].title} - {message}")

        cls.instances[-1]._set_message(message)
