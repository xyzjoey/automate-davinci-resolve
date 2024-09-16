import itertools
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field, validator

from .action_base import ActionBase
from ..inputs.tracks import MultipleVideoTracksInput

# from ..inputs.tracks import SingleVideoTrackInput
from ...davinci import textplus_utils
from ...davinci.enums import ResolveStatus
from ...davinci.timecode import Timecode
from ...davinci.resolve_app import ResolveApp
from ...utils import log


class Inputs(BaseModel):
    pass
    # track: int
    # track: MultipleVideoTracksInput = Field([], title="Video Track")


class Action(ActionBase):
    def __init__(self):
        super().__init__(
            name="print_clip_info",
            display_name="Print Clip Info",
            description="Print information of the clip in chosen track and at current playhead position",
            required_status=ResolveStatus.TimelineOpen,
            input_model=Inputs,
        )

    def start(
        self,
        resolve_app: ResolveApp,
        input_data: Inputs,
    ):
        # track_index = input_data.track

        # if input_data.track is None:
        #     log.warning(f"[{self}] Track is not provided")

        current_timeline = resolve_app.get_current_timeline()
        timecode_settings = current_timeline.get_timecode_settings()
        # log.debug(current_timeline.timeline.GetSetting())
        log.debug(current_timeline.timeline.GetStartTimecode())
        log.debug(current_timeline.timeline.GetStartFrame())
        log.debug(Timecode.from_frame(current_timeline.timeline.GetStartFrame(), timecode_settings, True).get_str(True))
        # track = current_timeline.get_track("video", track_index)

        # for item in track.timeline_items:
        #     textplus = textplus_utils.find_textplus(item)

        #     if textplus is None:
        #         continue

        #     text = textplus.GetInput("StyledText")

        #     log.info(text)

        #     break

        # item = current_timeline.get_current_item_at_track("video", track_index)

        # if item is None:
        #     log.warning(f"[{self}] No clip found at current playhead in track {track_index}")

        # textplus = textplus_utils.find_textplus(item)

        # log.info(f"[{self}] Clip found:")
        # log.info(f"[{self}] {item.GetName()}")
        # # log.info(f"[{self}] {textplus_utils.get_textplus_data(item)}")

        # for input in textplus.GetInputList().values():
        #     input_id = input.GetAttrs("INPS_ID")

        #     if input.GetAttrs("INPS_DataType") != "Gradient":
        #         continue

        #     # if input_id != "Start" and input_id != "End":
        #     #     continue

        #     value = textplus.GetInput(input_id)

        #     log.info(f"input_id={input_id}")
        #     log.info(f"value={value}")
        #     log.info(f"input.GetExpression()={input.GetExpression()}")
        #     log.info(f"{input.GetAttrs()}")

        mask_setting_path = "C:\\Users\\User\\Downloads\\Mask.setting"
        # use Execute with python code to dump json?
        mask_setting_json_path = "C:\\Users\\User\\Downloads\\Mask.setting.json"
        # mask_setting = None

        track_index = 7

        # save settings

        # with open(mask_setting_json_path, "r", encoding="utf-8") as f:
        #     mask_setting = json.load(f)

        ref_item = current_timeline.get_track("video", track_index).timeline_items[0]
        ref_comp = ref_item.GetFusionCompByIndex(1)
        log.info(f"ref StyledText={textplus_utils.find_textplus(ref_item).GetInput('StyledText')}")
        # log.info(f"ref Save result={ref_comp.Save(mask_setting_path)}")
        log.info(f"ref_comp.Copy result={ref_comp.Copy()}")
        # ref_comp.Execute("!Py: ref_settings = comp.CopySettings(); print(ref_settings)")

        target_item = current_timeline.get_track("video", track_index).timeline_items[1]
        # target_comp = target_item.GetFusionCompByIndex(1)
        log.info(f"target AddFusionComp={target_item.AddFusionComp()}")
        target_comp = target_item.GetFusionCompByIndex(target_item.GetFusionCompCount())
        log.info(f"target StyledText={textplus_utils.find_textplus(target_item).GetInput('StyledText')}")
        target_comp.AddTool("Blur")
        # log.info(f"target DeleteFusionCompByName result={target_item.DeleteFusionCompByName('Composition 1')}")
        # log.info(f"target LoadFusionCompByName={target_item.LoadFusionCompByName('Composition 2')}")
        # target_comp = target_item.LoadFusionCompByName("Composition 2")
        # log.info(f"target_comp ImportFusionComp result={target_item.ImportFusionComp(mask_setting_path)}")
        # log.info(f"target NameList={target_item.GetFusionCompNameList()}")
        # log.info(f"target_comp LoadFusionCompByName={target_item.LoadFusionCompByName('Composition 1')}")
        # target_comp.Execute("!Py: target_settings = comp.CopySettings(); print(target_settings)")
        # target_comp.Execute("!Py: print(comp.Copy())")
        # target_comp.Execute("!Py: print(comp.Paste(ref_settings))")
        log.info(f"target_comp.Paste result={target_comp.Paste()}")

        # # create & load settings
        # for ref_node in ref_comp.FindTool("Mask").GetChildrenList().values():
        #     target_node = target_comp.FindTool(ref_node.Name)

        #     if target_node is None:
        #         target_node = target_comp.AddTool(ref_node.GetAttrs()["TOOLS_RegID"])
        #         target_node.SetAttrs({"TOOLS_Name": ref_node.Name})

        #     with tempfile.TemporaryDirectory() as temp_dir_name:
        #         temp_path = Path(f"{temp_dir_name}/temp.setting")
        #         ref_node.SaveSettings(str(temp_path))
        #         target_node.LoadSettings(str(temp_path))

        # # connect
        # for ref_node in ref_comp.FindTool("Mask").GetChildrenList().values():
        #     target_node = target_comp.FindTool(ref_node.Name)

        #     if target_node is None:
        #         log.info(f"!!!!!! cannot find {ref_node.Name}")
        #         break

        #     for i, main_input in ((i, ref_node.FindMainInput(i)) for i in itertools.count(start=1)):
        #         if main_input is None:
        #             break

        #         connected_output = main_input.GetConnectedOutput()

        #         if connected_output is not None:
        #             target_node.FindMainInput(i).ConnectTo(target_comp.FindTool(connected_output.GetTool().Name))

        #     # main_input_index = 1
        #     # main_input = ref_node.FindMainInput(main_input_index)

        #     # while main_input

        # for track in current_timeline.iter_tracks("video"):
        #     for i, item in enumerate(track.timeline_items):
        #         if not (track.index == 3 and i == 1):
        #             continue

        #         textplus = textplus_utils.find_textplus(item)

        #         if textplus is None:
        #             log.info("Cannot find Text+")
        #             continue

        #         if item.GetFusionCompCount() > 0:
        #             comp = item.GetFusionCompByIndex(1)

        #             if comp.FindTool("Mask") is not None:
        #                 log.info("Mask is alread added")
        #                 continue

        #         log.info(f"track.index={track.index} i={i} text={textplus.GetInput('StyledText')}")
        #         # log.info(f"Paste={comp.Paste()}")

        #         result = comp.Paste(mask_setting_path)
        #         log.info(f"Paste result={result}")
        #         if not result:
        #             log.info(f"Failed to paste for clip [Text={textplus.GetInput('StyledText')}, Start={Timecode.from_frame(item.GetStart(), timecode_settings, True)}]")
