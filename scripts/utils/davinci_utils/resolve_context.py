from datetime import datetime, time, timedelta

import DaVinciResolveScript


class Timecode:
    @staticmethod
    def to_timedelta(timecode: str, frame_rate: float) -> timedelta:
        dt = datetime.strptime(timecode[:-3], "%H:%M:%S")
        frame = int(timecode[-2:])

        return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=1e+6 * frame / frame_rate)

    @staticmethod
    def to_frame(timecode: str, frame_rate: float) -> int:
        dt = datetime.strptime(timecode[:-3], "%H:%M:%S")
        frame = int(timecode[-2:])

        return (dt.hour * 3600 + dt.minute * 60 + dt.second) * frame_rate + frame

    @staticmethod
    def from_frame(frame, frame_rate: float) -> str:
        total_seconds, remain_frames = divmod(frame, frame_rate)
        hours, remain_seconds = divmod(total_seconds, 3600)
        minutes, remain_seconds = divmod(remain_seconds, 60)
        t = time(hour=int(hours), minute=int(minutes), second=int(remain_seconds))

        return f"{t.strftime('%H:%M:%S')}:{remain_frames :02.0f}"

class StartTimecodeCache:
    def __init__(self):
        self.start_timecode: timedelta = None
        self.corresponding_timeline = None

    def __update(self, timeline, frame_rate):
        if timeline != self.corresponding_timeline:
            self.start_timecode = Timecode.to_timedelta(timeline.GetStartTimecode(), frame_rate)
            self.corresponding_timeline = timeline

    def get(self, timeline, frame_rate) -> timedelta:
        self.__update(timeline, frame_rate)
        return self.start_timecode


class FrameRateCache:
    def __init__(self):
        self.frame_rate: float = None
        self.corresponding_timeline = None

    def __update(self, timeline):
        if timeline != self.corresponding_timeline:
            self.frame_rate = float(timeline.GetSetting('timelineFrameRate'))
            self.corresponding_timeline = timeline

    def get(self, timeline) -> timedelta:
        self.__update(timeline)
        return self.frame_rate


class ResolveContext:
    instance = None

    def __init__(self):
        # resolve object
        self.resolve = None
        self.project_manager = None
        self.project = None
        self.media_storage = None
        self.media_pool = None

        # cache
        self.start_timecode_cache = StartTimecodeCache()
        self.frame_rate_cache = FrameRateCache()

        self.update()

    @classmethod
    def get(cls) -> "ResolveContext":
        if cls.instance is None:
            cls.instance = ResolveContext()
        return cls.instance

    def update(self):
        if self.resolve is None or not dir(self.resolve):
            self.resolve = DaVinciResolveScript.scriptapp("Resolve")

            assert self.resolve is not None, "Failed to load DaVinci Resolve script app. Please check external scripting setting in davinci and environment variables. If settings are correct but still failed, please try restart davinci resolve."

        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        self.media_storage = self.resolve.GetMediaStorage()
        self.media_pool = self.project.GetMediaPool()

    def print_timeline_item(self, timeline_item):
        print(f"\tClip Name: {timeline_item.GetName()}")
        print(f"\tStart: {self.frame_to_timecode(timeline_item.GetStart())}")
        print(f"\tEnd: {self.frame_to_timecode(timeline_item.GetEnd())}")

    def get_unique_timeline_name(self, name) -> str:
        timeline_names = [self.project.GetTimelineByIndex(i + 1).GetName() for i in range(self.project.GetTimelineCount())]

        new_name = name
        index = 0

        while new_name in timeline_names:
            index += 1
            new_name = f"{name} {index}"

        return new_name

    def create_timeline(self, desired_name):
        actual_name = self.get_unique_timeline_name(desired_name)

        timeline = self.media_pool.CreateEmptyTimeline(actual_name)

        assert timeline is not None, "Failed to create timeline"
        assert self.project.SetCurrentTimeline(timeline), "Failed to set current timeline (timeline={timeline})"

        return actual_name, timeline

    def iter_media_pool_items(self):
        folder_stacks = [[self.media_pool.GetRootFolder()]]

        while folder_stacks != [[]]:
            current_path = [folders[0] for folders in folder_stacks]
            current_folder = folder_stacks[-1][0]

            for media_pool_item in current_folder.GetClipList():
                yield media_pool_item, current_path

            subfolders = list(current_folder.GetSubFolderList())

            if len(subfolders) > 0:
                folder_stacks.append(subfolders)
            else:
                folder_stacks[-1].pop(0)

                while len(folder_stacks[-1]) == 0 and len(folder_stacks) > 1:
                    folder_stacks.pop()
                    folder_stacks[-1].pop(0)

    def get_media_pool_item(self, path: str):
        tokens = path.split("/")
        folder_names = tokens[:-1]
        clip_name = tokens[-1]

        current_folder = self.media_pool.GetRootFolder() if path.startswith("/") else self.media_pool.GetCurrentFolder()

        for folder_name in folder_names:
            if folder_name == "":
                continue

            subfolder = next((f for f in current_folder.GetSubFolderList() if f.GetName() == folder_name), None)

            if subfolder is None:
                raise Exception(f"Folder '{folder_name}' does not exist under '{current_folder.GetName()}'")

            current_folder = subfolder

        clip = next((clip for clip in current_folder.GetClipList() if clip.GetClipProperty("Clip Name") == clip_name), None)

        if clip is None:
            raise Exception(f"Clip '{clip_name}' does not exist under folder '{current_folder.GetName()}'")

        return clip

    def add_folder_if_not_exist(self, folder, name):
        subfolders = folder.GetSubFolderList()
        subfolder_with_same_name = next((subfolder for subfolder in subfolders if subfolder.GetName() == name), None)

        if subfolder_with_same_name is not None:
            return subfolder_with_same_name
        else:
            new_folder = self.media_pool.AddSubFolder(folder, name)
            return new_folder

    def is_valid_track_index(self, track_type, track_index):
        timeline = self.project.GetCurrentTimeline()
        track_count = timeline.GetTrackCount(track_type)

        return 1 <= track_index and track_index <= track_count

    def find_current_timeline_item_at_track(self, track_type, track_index):
        timeline = self.project.GetCurrentTimeline()
        current_timecode = timeline.GetCurrentTimecode()
        current_frame = self.timecode_to_frame(current_timecode)
        timeline_items = timeline.GetItemListInTrack(track_type, track_index)

        for timeline_item in timeline_items:
            if timeline_item.GetStart() <= current_frame and current_frame < timeline_item.GetEnd():
                return timeline_item

        return None

    def timecode_to_timedelta(self, timecode: str, unapply_start_timecode) -> timedelta:
        frame_rate = self.frame_rate_cache.get(self.project.GetCurrentTimeline())
        td = Timecode.to_timedelta(timecode, frame_rate)

        if unapply_start_timecode:
            start_timecode = self.start_timecode_cache.get(self.project.GetCurrentTimeline(), frame_rate)
            td -= start_timecode

        return td

    def timedelta_to_timecode(self, td: timedelta, apply_start_timecode) -> str:
        frame_rate = self.frame_rate_cache.get(self.project.GetCurrentTimeline())

        if apply_start_timecode:
            start_timecode = self.start_timecode_cache.get(self.project.GetCurrentTimeline(), frame_rate)
            td += start_timecode

        hours, rem = divmod(td.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        t = time(hour=hours, minute=minutes, second=seconds)

        return f"{t.strftime('%H:%M:%S')}:{td.microseconds * frame_rate / 1e+6 :02.0f}"

    def timedelta_to_frame(self, td: timedelta) -> int:
        frame_rate = self.frame_rate_cache.get(self.project.GetCurrentTimeline())

        return round((td.seconds + (td.microseconds / 1e+6)) * frame_rate)

    def timecode_to_frame(self, timecode: str) -> int:
        frame_rate = self.frame_rate_cache.get(self.project.GetCurrentTimeline())
        frame = Timecode.to_frame(timecode, frame_rate)

        return frame

    def frame_to_timecode(self, frame: int) -> str:
        frame_rate = self.frame_rate_cache.get(self.project.GetCurrentTimeline())
        timecode = Timecode.from_frame(frame, frame_rate)

        return timecode
