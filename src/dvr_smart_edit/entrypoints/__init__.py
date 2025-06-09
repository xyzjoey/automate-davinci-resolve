import asyncio
from types import ModuleType

from ..resolve_types import PyRemoteFusion, PyRemoteResolve
from ..smart_edit.fusion_custom_data import FusionCustomData


def setup_module(module: ModuleType, resolve: PyRemoteResolve = None, fusion: PyRemoteFusion = None):
    from .module_utils import ModuleUtils

    ModuleUtils.reload_module()

    from ..extended_resolve.davinci_resolve_module import DavinciResolveModule

    DavinciResolveModule.init(module, resolve, fusion)


async def init_fusion():
    from ..extended_resolve.davinci_resolve_module import DavinciResolveModule
    from ..smart_edit.ui.loading_window import LoadingWindow

    resolve = DavinciResolveModule.get_resolve()
    prev_project = None

    def is_same_project(project1, project2):
        id1 = project1.GetUniqueId() if project1 is not None else None
        id2 = project2.GetUniqueId() if project2 is not None else None
        return id1 == id2

    if not FusionCustomData.get_init_fusion_enabled():
        return

    while True:
        curr_project = resolve.get_current_project()

        if not is_same_project(prev_project, curr_project) and curr_project is not None:
            page = resolve._resolve.GetCurrentPage()

            if page is not None:
                if page != "fusion":
                    await asyncio.sleep(3)  # even page is not None, UI may not be ready
                    page = resolve._resolve.GetCurrentPage()

                if page is not None and page != "fusion":
                    with LoadingWindow("Setup", "Opening Fusion Page..."):
                        resolve._resolve.OpenPage("fusion")
                        resolve._resolve.OpenPage(page)

                prev_project = curr_project

        if curr_project is None:
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(3)
