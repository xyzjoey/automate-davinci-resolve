from ..resolve_types import _UIDispatcher


class UiDispatcher:
    def __init__(self, _ui_dispatcher: _UIDispatcher):
        self._ui_dispatcher = _ui_dispatcher
        self._ui_manager = _ui_dispatcher.UIManager()
