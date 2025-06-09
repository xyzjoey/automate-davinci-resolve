from ..extended_resolve import davinci_resolve_module
from ..resolve_types import PyRemoteComposition


class ScriptUtils:
    @classmethod
    def find_composition_in_timeline(cls, composition: PyRemoteComposition):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        if timeline is None:
            return None, None

        timeline_item = timeline.find_item(lambda item: str(item.get_last_fusion_composition()) == str(composition), track_type="video")

        if timeline_item is None:
            return None, None

        comp = timeline_item.get_last_fusion_composition()

        return timeline_item, comp

    # ensure clip in timeline
    @classmethod
    def find_fuse_in_timeline(cls, composition: PyRemoteComposition, fuse_name: str):
        timeline_item, comp = ScriptUtils.find_composition_in_timeline(composition)

        if comp is not None:
            tool = comp.FindTool(fuse_name)

            return timeline_item, comp, tool

        return timeline_item, comp, None

    # does not ensure clip in timeline (e.g. fusion composition in media pool, effects library)
    @classmethod
    def find_fuse_in_composition(cls, composition: PyRemoteComposition, fuse_name: str):
        if composition.FindTool is None:  # happen rarely (e.g. composition=<nil> [App: 'Resolve' on 127.0.0.1, UUID: 08934f92-4270-467a-bb2d-1148505d8e26])
            print(f"DEBUG!!!! find_fuse_in_timeline: comp.FindTool is None, comp={composition}")
            return None

        tool = composition.FindTool(fuse_name)

        if tool is None:
            return None

        return tool
