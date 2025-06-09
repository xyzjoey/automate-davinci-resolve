import traceback
from contextlib import contextmanager

from ...extended_resolve import davinci_resolve_module
from ...utils import log
from ..errors import UserError
from .menu_factory import MenuFactory


class ErrorWindow:
    @classmethod
    def _create(
        cls,
        title: str,
        message: str,
        need_console: bool = False,
        need_report: bool = False,
    ):
        ui_manager = davinci_resolve_module.get_ui_manager()
        ui_dispatcher = davinci_resolve_module.create_ui_dispatcher()
        ui = ui_manager._ui_manager
        disp = ui_dispatcher._ui_dispatcher
        menu_factory = MenuFactory(ui_manager)

        elements = []
        elements.append(
            ui.Label(
                {
                    "ID": "Message",
                    "Text": message,
                    "Alignment": {
                        "AlignVCenter": True,
                        "AlignHCenter": True,
                    },
                    "WordWrap": True,
                }
            )
        )
        if need_console and need_report:
            elements.append(
                menu_factory.horizontal_center(
                    ui.Button(
                        {
                            "Text": "Show Console",
                            "ID": "ShowConsole",
                        }
                    ),
                    ui.Button(
                        {
                            "Text": "Report Issue (WIP)",
                            "ID": "ReportIssue",
                        }
                    ),
                )
            )
        elif need_console:
            elements.append(
                menu_factory.horizontal_center(
                    ui.Button(
                        {
                            "Text": "Show Console",
                            "ID": "ShowConsole",
                        }
                    ),
                )
            )
        elements.append(
            ui.HGroup(
                [
                    ui.HGap(0, 10),
                    ui.Button(
                        {
                            "Text": "OK",
                            "ID": "Ok",
                        }
                    ),
                    ui.HGap(0, 10),
                ]
            ),
        )

        window = disp.AddWindow(
            {
                "WindowTitle": f"Smart Edit - {title}",
                "ID": "SmartEditErrorWindow",
                "WindowFlags": {"CoverWindow": True},
                # "WindowModality": "WindowModal",
                "Margin": 0,
                "Spacing": 0,
            },
            [
                ui.VGroup(
                    {"Spacing": 20},
                    [
                        ui.VGap(0, 10),
                        *elements,
                        ui.VGap(0, 10),
                    ],
                ),
            ],
        )

        def on_close(event):
            disp.ExitLoop()
            window.Hide()

        window.On.SmartEditErrorWindow.Close = on_close
        window.On.Ok.Clicked = on_close

        if need_console:

            def on_show_console(event):
                fusion = davinci_resolve_module.get_fusion()
                fusion.ShowConsole(True)

            window.On.ShowConsole.Clicked = on_show_console

        window.Resize((500, 200))
        window.Show()
        disp.RunLoop()

    @classmethod
    def create(cls, error: Exception, title: str = None):
        if isinstance(error, UserError):
            title = title or "User Error"
            message = str(error)
            need_console = error.detailed_error is not None
            need_report = False
        else:
            title = title or "Error"
            message = "Unexpected error. Check console for details."
            need_console = True
            need_report = True

        cls._create(
            title=title,
            message=message,
            need_console=need_console,
            need_report=need_report,
        )

    @classmethod
    def log_and_pop(cls, error: Exception, title: str = None):
        if isinstance(error, UserError):
            if error.detailed_error is not None:
                traceback.print_exception(error)
            log.info(error)
        else:
            traceback.print_exc()

        cls.create(error, title)

    @classmethod
    @contextmanager
    def pop_on_error(cls):
        try:
            yield
        except Exception as e:
            cls.log_and_pop(e)
