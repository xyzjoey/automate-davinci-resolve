import asyncio
from typing import List

import aioconsole

from davinci_resolve_cli.utils import terminal_io
from davinci_resolve_cli.davinci import textplus_utils
from davinci_resolve_cli.davinci.resolve_context import ResolveContext, ResolveStatus
from davinci_resolve_cli.inputs.choice_input import ChoiceInput, ChoiceValue, Choice


class ReferenceClip:
    def __init__(self, timeline_item):
        self.timeline_item = timeline_item
        self.textplus_data = textplus_utils.get_textplus_data(timeline_item)

    def print(self):
        if self.timeline_item.GetName is None or self.timeline_item.GetName() is None:
            print("\tClip Name: (clip is deleted)")
        else:
            ResolveContext.get().print_timeline_item(self.timeline_item)

        textplus_utils.print_textplus(self.textplus_data)


class ReferenceClipOrChoiceInput(ChoiceInput):
    def __init__(self):
        super().__init__([
            Choice("p", ChoiceValue.PAUSE, "pause or resume"),
            Choice("q", ChoiceValue.QUIT, "quit"),
            Choice("?", ChoiceValue.HELP, "print help"),
            Choice("??", ChoiceValue.HELP_MORE, "print style being tracked"),
        ])

        self.track_index = None
        self.reference_clip = None

    def print_help(self):
        resolve_context = ResolveContext.get()
        track_count = resolve_context.project.GetCurrentTimeline().GetTrackCount("video")
        print(f"<int> - Video Track index (avail now: 1-{track_count}). Find clip at playhead as the new Text+ style reference for the track.")
        super().print_help()

    @classmethod
    async def ask_for_input(cls) -> "ReferenceClipOrChoiceInput":
        choice_input = cls()

        choice_name_hint = "<int>/" + "/".join(choice_input.choices.keys())
        full_prompt = f"Please enter track index to monitor [{choice_name_hint}]: "

        while True:
            with terminal_io.at_bottom():
                terminal_io.print_question(full_prompt, end="")

            choice_input.raw_value = await aioconsole.ainput()

            terminal_io.clear_bottom()

            try:
                return cls.validate(choice_input)
            except Exception as e:
                terminal_io.print_error(str(e))

    @classmethod
    def validate(cls, choice_input) -> "ReferenceClipOrChoiceInput":
        try:
            track_index = int(choice_input.raw_value)
        except:
            return super().validate(choice_input)

        resolve_context = ResolveContext.get()
        timeline_context = resolve_context.get_current_timeline_context()

        if not timeline_context.has_track("video", track_index):
            raise Exception(f"'{track_index}' is out of track range")

        timeline_item = timeline_context.get_current_item_at_track("video", track_index)

        if timeline_item is None:
            raise Exception("No clip at playhead location")

        textplus = textplus_utils.find_textplus(timeline_item)

        if textplus is None:
            raise Exception(f"Clip '{timeline_item.GetName()}' has no Text+ node in 1st fusion composition")

        choice_input.track_index = track_index
        choice_input.reference_clip = ReferenceClip(timeline_item)

        return choice_input


class MonitoredTrackInfo:
    def __init__(self, reference_clip: ReferenceClip, clip_ids: List[str]):
        self.reference_clip = reference_clip
        self.clip_ids = clip_ids


class Process:
    def __init__(self):
        self.resolve_context = ResolveContext.get()
        self.monitored_track_infos = {}
        self.styling_task = None
        self.paused = False

    def print_monitored_track_info(self, print_style=False):
        current_timeline = self.resolve_context.project.GetCurrentTimeline()
        track_infos = self.monitored_track_infos.get(current_timeline.GetUniqueId(), {})

        if len(track_infos) > 0:
            print(f"Monitoring {len(track_infos)} tracks (video track {sorted(track_infos.keys())}) in current timeline '{current_timeline.GetName()}'")
        else:
            print(f"Monitoring {len(track_infos)} tracks in current timeline '{current_timeline.GetName()}'")

        if print_style:
            for track_index, info in track_infos.items():
                track_name = self.resolve_context.project.GetCurrentTimeline().GetTrackName("video", track_index)
                print(f"Video track {track_index} '{track_name}' reference clip: ")
                info.reference_clip.print()

    def update_monitored_tracks_on_track_moved(self, timeline, new_track_contexts: dict):
        timeline_id = timeline.GetUniqueId()
        track_infos = self.monitored_track_infos.get(timeline_id)

        if track_infos is None:
            return

        tracks_to_check = {track_index: set(info.clip_ids) for track_index, info in sorted(track_infos.items())}
        avail_tracks = {track_index: set([item.GetUniqueId() for item in track_context.timeline_items]) for track_index, track_context in new_track_contexts.items()}
        moved_tracks = {}
        lost_tracks = []

        # check for unmoved tracks
        for track_index, old_clip_ids in list(dict(tracks_to_check).items()):  # avoid RuntimeError: dictionary changed size during iteration
            if track_index not in avail_tracks:
                continue

            new_clip_ids = avail_tracks[track_index]
            clip_exist = old_clip_ids & new_clip_ids

            if clip_exist:
                tracks_to_check.pop(track_index)
                avail_tracks.pop(track_index)

        # check for moved tracks
        for track_index, clip_ids in list(dict(tracks_to_check).items()):
            for other_track_index, other_clip_ids in avail_tracks.items():
                clip_exist = clip_ids & other_clip_ids

                if clip_exist:
                    moved_tracks[track_index] = other_track_index
                    tracks_to_check.pop(track_index)
                    avail_tracks.pop(other_track_index)
                    break

        # check for unmoved tracks (empty track)
        for track_index, old_clip_ids in list(dict(tracks_to_check).items()):
            if track_index not in avail_tracks:
                continue

            new_clip_ids = avail_tracks[track_index]

            if len(new_clip_ids) == 0:
                tracks_to_check.pop(track_index)
                avail_tracks.pop(track_index)

        # lost track
        lost_tracks = list(tracks_to_check.keys())

        # update
        for track_index in lost_tracks:
            track_infos.pop(track_index)

        self.monitored_track_infos[timeline_id] = {moved_tracks.get(track_index, track_index): info for track_index, info in track_infos.items()}

        # print
        if moved_tracks:
            terminal_io.print_info("Detected track(s) moved:")
            for old, new in moved_tracks.items():
                terminal_io.print_info(f"\t{old} --> {new}")
        
        if lost_tracks:
            terminal_io.print_info(f"Detected lost track(s): {lost_tracks}")

    def update_monitored_tracks(self, timeline, track_context, reference_clip):
        timeline_id = timeline.GetUniqueId()
        
        track_info = MonitoredTrackInfo(reference_clip=reference_clip, clip_ids=[item.GetUniqueId() for item in track_context.timeline_items])
        
        self.monitored_track_infos.setdefault(timeline_id, {})
        self.monitored_track_infos[timeline_id][track_context.index] = track_info

        print(f"New reference clip is used for video track {track_context.index} '{track_context.name}':")
        track_info.reference_clip.print()

    async def maintain_track_styles(self):
        while True:
            resolve_status = self.resolve_context.update()

            if resolve_status != ResolveStatus.TimelineAvail:
                terminal_io.print_warning("Detect Davinci Resolve project closed. Pause monitoring.")
                self.paused = True
                break

            timeline_context = self.resolve_context.get_current_timeline_context()
            timeline = timeline_context.timeline
            timeline_id = timeline.GetUniqueId()
            track_count = timeline.GetTrackCount("video")

            new_track_contexts = {track_index: timeline_context.get_track_context("video", track_index) for track_index in range(1, track_count + 1)}
            new_track_contexts = {k: v for k, v in new_track_contexts.items() if v is not None}

            self.update_monitored_tracks_on_track_moved(timeline, new_track_contexts)

            track_infos = self.monitored_track_infos.get(timeline_id, {})

            for track_index, track_info in track_infos.items():
                new_clip_ids = [item.GetUniqueId() for item in new_track_contexts[track_index].timeline_items]
                newly_added_clip_ids = set(new_clip_ids) - set(track_info.clip_ids)

                if len(newly_added_clip_ids) > 0:
                    terminal_io.print_info(f"Detected new clip(s) in video track {track_index}.")
                    textplus_utils.apply_textplus_style_to(new_track_contexts[track_index], track_info.reference_clip.textplus_data, filter_if=lambda item: not item.GetUniqueId() in newly_added_clip_ids)

                track_info.clip_ids = new_clip_ids

            await asyncio.sleep(0.25)

    async def start_maintain_track_styles(self):
        self.styling_task = asyncio.create_task(self.maintain_track_styles())

    async def stop_maintain_track_styles(self):
        if self.styling_task is not None:
            self.styling_task.cancel()

            try:
                await self.styling_task
            except asyncio.CancelledError:
                pass

            self.styling_task = None

    async def run(self):
        if self.resolve_context.update() != ResolveStatus.TimelineAvail:
            terminal_io.print_error("Davinci Resolve project is not opened")
            return

        while True:
            choice_input = await ReferenceClipOrChoiceInput.ask_for_input()

            await self.stop_maintain_track_styles()

            if self.resolve_context.update() != ResolveStatus.TimelineAvail:
                terminal_io.print_error("Davinci Resolve project is not opened. Paused.")
                continue
            elif choice_input.get_value() == ChoiceValue.HELP:
                self.print_monitored_track_info()
                choice_input.print_help()
            elif choice_input.get_value() == ChoiceValue.HELP_MORE:
                self.print_monitored_track_info(print_style=True)
            elif choice_input.get_value() == ChoiceValue.QUIT:
                terminal_io.print_warning("Stop monitoring Text+ style")
                break
            elif choice_input.get_value() == ChoiceValue.PAUSE:
                if self.paused:
                    terminal_io.print_warning("Resume monitoring Text+ style")
                    self.paused = False
                else:
                    terminal_io.print_info("Pause monitoring Text+ style")
                    self.paused = True
                    continue
            else:
                timeline_context = self.resolve_context.get_current_timeline_context()
                track_context = timeline_context.get_track_context("video", choice_input.track_index)

                self.update_monitored_tracks(timeline_context.timeline, track_context, choice_input.reference_clip)
                textplus_utils.apply_textplus_style_to(track_context, choice_input.reference_clip.textplus_data, print_progress=True)

            await self.start_maintain_track_styles()

    async def main(self):
        await self.run()


if __name__ == "__main__":
    asyncio.run(Process().main())
