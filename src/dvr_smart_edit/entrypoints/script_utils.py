from ..extended_resolve import davinci_resolve_module
from ..resolve_types import PyRemoteComposition


class ScriptUtils:
    @classmethod
    def get_timeline_item_from_composition(cls, composition: PyRemoteComposition):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        # def get_uuid(comp):
        #     return str(comp).split("UUID: ")[-1].split("]")[0]

        # uuid = get_uuid(composition)

        timeline_item = timeline.find_item(lambda item: str(item.get_last_fusion_composition()) == str(composition), track_type="video")
        comp = timeline_item and timeline_item.get_last_fusion_composition()

        return timeline_item, comp

    @classmethod
    def get_tool_from_fuse_name(cls, composition: PyRemoteComposition, fuse_name: str):
        if composition is None:
            return None, None

        if composition.FindTool is None:  # happen rarely (e.g. composition=<nil> [App: 'Resolve' on 127.0.0.1, UUID: 08934f92-4270-467a-bb2d-1148505d8e26])
            print("DEBUG!!!! composition.FindTool is None")
            _, comp = ScriptUtils.get_timeline_item_from_composition(composition)
            # print(f"DEBUG!!!! comp={comp}")

            if comp is not None:
                return comp, comp.FindTool(fuse_name)

            return None, None

        return composition, composition.FindTool(fuse_name)

    @classmethod
    def find_fuse_in_timeline(cls, composition: PyRemoteComposition, fuse_name: str):
        print(f"find_fuse_in_timeline!!!! comp={composition}")
        # print(f"COMPS_Name={composition.GetAttrs()["COMPS_Name"]}")
        # print(f"COMPS_FileName={composition.GetAttrs()["COMPS_FileName"]}")
        # print(f"MediaOut1={composition.MediaOut1}")
        timeline_item, comp = ScriptUtils.get_timeline_item_from_composition(composition)

        if comp is not None:
            tool = comp.FindTool(fuse_name)

            print(f"found!!!! timeline_item={timeline_item} ({timeline_item.get_track_handle()}, {timeline_item.get_frame_range()}) comp={comp}")

        #     return timeline_item, comp, tool

        # return timeline_item, comp, None
