from types import ModuleType

from ..resolve_types import PyRemoteFusion, PyRemoteResolve
from .resolve import Resolve
from .ui_dispatcher import UiDispatcher
from .ui_manager import UiManager


class DavinciResolveModule:
    _module: ModuleType = None
    _resolve: PyRemoteResolve = None
    _fusion: PyRemoteFusion = None

    resolve: Resolve = None

    @classmethod
    def init(cls, _module: ModuleType, _resolve: PyRemoteResolve = None, _fusion: PyRemoteFusion = None):
        cls._module = _module

        if _resolve is not None:
            cls._resolve = _resolve
        else:
            cls._resolve = cls._module.scriptapp("Resolve")

        if _fusion is not None:
            cls._fusion = _fusion
        else:
            cls._fusion = cls._resolve.Fusion()

        cls.resolve = Resolve(cls._resolve)

    @classmethod
    def get_resolve(cls):
        return cls.resolve

    @classmethod
    def get_fusion(cls):
        return cls._fusion

    @classmethod
    def create_ui_dispatcher(cls):
        ui_manager = cls._fusion.UIManager
        ui_dispatcher = UiDispatcher(cls._module.UIDispatcher(ui_manager))

        return ui_dispatcher

    @classmethod
    def get_ui_manager(cls):
        return UiManager(cls._fusion.UIManager)


get_resolve = DavinciResolveModule.get_resolve
get_fusion = DavinciResolveModule.get_fusion
create_ui_dispatcher = DavinciResolveModule.create_ui_dispatcher
get_ui_manager = DavinciResolveModule.get_ui_manager
