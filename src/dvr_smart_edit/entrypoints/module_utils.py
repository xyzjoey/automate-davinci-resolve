import importlib
import sys
import traceback
from types import ModuleType


class ModuleUtils:
    @classmethod
    def _recursive_reload(cls, module, root_package_name, visited_modules):
        if not module.__package__.startswith(root_package_name):
            return
        if module in visited_modules:
            return

        visited_modules.add(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if type(attr) is ModuleType:
                dependant_module = attr
                cls._recursive_reload(dependant_module, root_package_name, visited_modules)
            elif hasattr(attr, "__module__"):
                dependant_module = sys.modules[attr.__module__]
                cls._recursive_reload(dependant_module, root_package_name, visited_modules)

        try:
            return importlib.reload(module)
        except:
            traceback.print_exc()
            return None

    @classmethod
    def reload_module(cls):
        import dvr_smart_edit

        module = dvr_smart_edit

        visited_modules = set()
        return cls._recursive_reload(module, module.__package__, visited_modules)
