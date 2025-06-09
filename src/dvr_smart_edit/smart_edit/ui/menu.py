from ...extended_resolve.ui_dispatcher import UiDispatcher
from ...extended_resolve.ui_manager import UiManager
from .menu_factory import MenuUiFactory


class Window:
    def __init__(self, _window):
        self._window = _window

    def register_event(self, element_id, event_name, callback):
        setattr(getattr(self._window.On, element_id), event_name, callback)

    def resize(self, width=None, height=None):
        size = self._window.Size()

        if width is None:
            width = size[1]

        if height is None:
            height = size[2]

        self._window.Resize((width, height))

    def find_item(self, id):
        return self._window.GetItems().get(id)


class Menu:
    def __init__(self, ui_dispatcer: UiDispatcher, ui_manager: UiManager, window_props: dict):
        self.ui_dispatcer = ui_dispatcer
        self.ui_manager = ui_manager

        self.window_props = window_props
        self.window = Window(self._disp.AddWindow(window_props, []))
        self.window.register_event(window_props["ID"], "Close", self._on_close)

        self.ui_factory = MenuUiFactory(self.window, self.ui_manager)

    @property
    def _disp(self):
        return self.ui_dispatcer._ui_dispatcher

    @property
    def window_id(self):
        return self.window_props["ID"]

    def find_group(self, id):
        return self.ui_factory.find_group(id)

    def add_elements(self, *elements):
        root_item = self.window.find_item(self.window_id)

        for element in elements:
            root_item.AddChild(element)

        self.window._window.RecalcLayout()

    def show_and_run(self):
        self.ui_factory.finalize()

        self.window._window.Show()
        self._disp.RunLoop()

    def _on_close(self, event):
        self._disp.ExitLoop()
        self.window._window.Hide()
