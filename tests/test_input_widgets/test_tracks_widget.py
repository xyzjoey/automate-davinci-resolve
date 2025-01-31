from pydantic import BaseModel

from automate_davinci_resolve.app.inputs.tracks import MultipleVideoTracksInput
from automate_davinci_resolve.davinci.context import (
    TimelineContext,
    TimelineDiff,
    TimelineItemContext,
    TrackContext,
)
from automate_davinci_resolve.gui.input_widgets.track_widgets import (
    CheckboxOption,
    MultipleVideoTracksWidget,
)


class Input(BaseModel):
    tracks: MultipleVideoTracksInput


class TestMultipleVideoTracksWidget:
    def test_create_options(self):
        tracks_widget = MultipleVideoTracksWidget("name", master=None)
        timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={}),
                2: TrackContext(index=2, name="", items={}),
                3: TrackContext(index=3, name="", items={}),
            },
        )

        assert tracks_widget.options == []

        tracks_widget.update(timeline_context=timeline_context, timeline_diff=None)

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=False),
            CheckboxOption(value=2, name="[2] ", selected=False),
            CheckboxOption(value=3, name="[3] ", selected=False),
        ]

    def test_toggle(self):
        tracks_widget = MultipleVideoTracksWidget("name", master=None)
        old_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
            },
        )

        tracks_widget.update(timeline_context=old_timeline_context, timeline_diff=None)
        tracks_widget.toggle(1)
        tracks_widget.toggle(3)

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=True),
            CheckboxOption(value=2, name="[2] ", selected=False),
            CheckboxOption(value=3, name="[3] ", selected=True),
        ]
        assert tracks_widget.get_data() == [1, 3]

    def test_track_added(self):
        tracks_widget = MultipleVideoTracksWidget("name", master=None)
        old_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
            },
        )
        new_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
                4: TrackContext(index=4, name="", items={}),
            },
        )
        timeline_diff = TimelineDiff.create(old_timeline_context, new_timeline_context)

        tracks_widget.update(timeline_context=old_timeline_context, timeline_diff=None)
        tracks_widget.toggle(1)
        tracks_widget.toggle(3)
        tracks_widget.update(timeline_context=new_timeline_context, timeline_diff=timeline_diff)

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=True),
            CheckboxOption(value=2, name="[2] ", selected=False),
            CheckboxOption(value=3, name="[3] ", selected=True),
            CheckboxOption(value=4, name="[4] ", selected=False),
        ]
        assert tracks_widget.get_data() == [1, 3]

    def test_track_renamed(self):
        tracks_widget = MultipleVideoTracksWidget("name", master=None)
        old_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="1", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="2", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="3", items={"C": TimelineItemContext(id="C")}),
            },
        )
        new_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="X", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="Y", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="Z", items={"C": TimelineItemContext(id="C")}),
            },
        )
        timeline_diff = TimelineDiff.create(old_timeline_context, new_timeline_context)

        tracks_widget.update(timeline_context=old_timeline_context, timeline_diff=None)
        tracks_widget.toggle(1)
        tracks_widget.toggle(3)
        tracks_widget.update(timeline_context=new_timeline_context, timeline_diff=timeline_diff)

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] X", selected=True),
            CheckboxOption(value=2, name="[2] Y", selected=False),
            CheckboxOption(value=3, name="[3] Z", selected=True),
        ]
        assert tracks_widget.get_data() == [1, 3]

    def test_track_removed(self):
        tracks_widget = MultipleVideoTracksWidget("name", master=None)
        old_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
            },
        )
        new_timeline_context = TimelineContext(
            id="",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"B": TimelineItemContext(id="B")}),
                2: TrackContext(index=2, name="", items={"C": TimelineItemContext(id="C")}),
            },
        )
        timeline_diff = TimelineDiff.create(old_timeline_context, new_timeline_context)

        tracks_widget.update(timeline_context=old_timeline_context, timeline_diff=None)
        tracks_widget.toggle(1)
        tracks_widget.toggle(3)
        tracks_widget.update(timeline_context=new_timeline_context, timeline_diff=timeline_diff)

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=False),
            CheckboxOption(value=2, name="[2] ", selected=True),
        ]
        assert tracks_widget.get_data() == [2]

    def test_timeline_changed(self):
        tracks_widget = MultipleVideoTracksWidget("name", master=None)
        old_timeline_context = TimelineContext(
            id="timeline1",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
            },
        )
        new_timeline_context = TimelineContext(
            id="timeline12",
            name="",
            video_tracks={
                1: TrackContext(index=1, name="", items={"B": TimelineItemContext(id="B")}),
                2: TrackContext(index=2, name="", items={"C": TimelineItemContext(id="C")}),
            },
        )
        timeline_diff = TimelineDiff.create(old_timeline_context, new_timeline_context)

        tracks_widget.update(timeline_context=old_timeline_context, timeline_diff=None)
        tracks_widget.update(timeline_context=new_timeline_context, timeline_diff=timeline_diff)

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=False),
            CheckboxOption(value=2, name="[2] ", selected=False),
        ]
        assert tracks_widget.get_data() == []
