from ..extended_resolve import davinci_resolve_module
from ..resolve_types import PyRemoteComposition


class ScriptUtils:
    @classmethod
    def get_timeline_item_from_composition(cls, composition: PyRemoteComposition):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        timeline_item = timeline.find_item(lambda item: str(item._item.GetFusionCompByIndex(1)) == str(composition), track_type="video")

        return timeline_item

    @classmethod
    def get_tool_from_fuse_name(cls, composition: PyRemoteComposition, fuse_name: str):
        if composition is None:
            return None

        if composition.FindTool is None:
            # happen rarely when dragged bin clip to non playhead time (e.g. composition=<nil> [App: 'Resolve' on 127.0.0.1, UUID: 08934f92-4270-467a-bb2d-1148505d8e26])
            print("DEBUG!!!! composition.FindTool None")
            timelineItem = ScriptUtils.get_timeline_item_from_composition(composition)

            if timelineItem is not None:
                print(f"DEBUG!!!! timelineItem={timelineItem} {timelineItem.get_track_handle()} {timelineItem.get_frame_range()}")
            else:
                print(f"DEBUG!!!! timelineItem=None")
                resolve = davinci_resolve_module.get_resolve()
                timeline = resolve.get_current_timeline()
                for item in timeline.iter_items(track_type="video"):
                    comp = item._item.GetFusionCompByIndex(1)
                    print(comp)

            return timelineItem

        return composition.FindTool(fuse_name)
