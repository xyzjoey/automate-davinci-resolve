from pydantic import BaseModel
from davinci_resolve_cli.app.inputs.tracks import MultipleVideoTracksInput
from davinci_resolve_cli.gui.input_widgets.track_widgets import MultipleVideoTracksWidget, CheckboxOption
from davinci_resolve_cli.davinci.context import TimelineContext, TimelineDiff, TimelineItemContext, TrackContext


class Input(BaseModel):
    tracks: MultipleVideoTracksInput


class TestMultipleVideoTracksWidget:
    def test_update(self):
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

        tracks_widget.update(timeline_context=timeline_context, input_data=[])

        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=False),
            CheckboxOption(value=2, name="[2] ", selected=False),
            CheckboxOption(value=3, name="[3] ", selected=False),
        ]

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
        old_input_data = [1, 3]
        new_input_data = old_input_data

        tracks_widget.update(timeline_context=old_timeline_context, input_data=old_input_data)
        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=True),
            CheckboxOption(value=2, name="[2] ", selected=False),
            CheckboxOption(value=3, name="[3] ", selected=True),
        ]
        assert tracks_widget.get_data() == [1, 3]

        tracks_widget.update(timeline_context=new_timeline_context, input_data=new_input_data)
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
        old_input_data = [1, 3]
        new_input_data = old_input_data

        tracks_widget.update(timeline_context=old_timeline_context, input_data=old_input_data)
        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] 1", selected=True),
            CheckboxOption(value=2, name="[2] 2", selected=False),
            CheckboxOption(value=3, name="[3] 3", selected=True),
        ]
        assert tracks_widget.get_data() == [1, 3]

        tracks_widget.update(timeline_context=new_timeline_context, input_data=new_input_data)
        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] X", selected=True),
            CheckboxOption(value=2, name="[2] Y", selected=False),
            CheckboxOption(value=3, name="[3] Z", selected=True),
        ]
        assert tracks_widget.get_data() == [1, 3]

    def test_input_data_changed(self):
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
        old_input_data = [1, 3]
        new_input_data = [2]

        tracks_widget.update(timeline_context=old_timeline_context, input_data=old_input_data)
        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=True),
            CheckboxOption(value=2, name="[2] ", selected=False),
            CheckboxOption(value=3, name="[3] ", selected=True),
        ]
        assert tracks_widget.get_data() == [1, 3]

        tracks_widget.update(timeline_context=new_timeline_context, input_data=new_input_data)
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
        old_input_data = []
        new_input_data = []

        tracks_widget.update(timeline_context=old_timeline_context, input_data=old_input_data)
        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=False),
        ]
        assert tracks_widget.get_data() == []

        tracks_widget.update(timeline_context=new_timeline_context, input_data=new_input_data)
        assert tracks_widget.options == [
            CheckboxOption(value=1, name="[1] ", selected=False),
            CheckboxOption(value=2, name="[2] ", selected=False),
        ]
        assert tracks_widget.get_data() == []
