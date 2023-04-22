from automate_davinci_resolve.davinci.context import Diff, TimelineContext, TimelineItemContext, TimelineDiff, TrackContext


class TestTimelineDiff:
    def test_same(self):
        old = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="1", items={}),
            },
        )

        diff = TimelineDiff.create(old, old)

        assert diff.diff == {}

    def test_value_changed(self):
        old = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="1", items={}),
            },
        )
        new = TimelineContext(
            id="x",
            name="z",
            video_tracks={
                1: TrackContext(index=1, name="z", items={}),
            },
        )

        diff = TimelineDiff.create(old, new)

        assert diff.diff == {
            "changed": {
                "name": Diff("x", "z"),
                "video_tracks": {1: {"name": Diff("1", "z")}},
            }
        }

    def test_added_tracks(self):
        old = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
            },
        )
        new = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"X": TimelineItemContext(id="X")}),
                2: TrackContext(index=2, name="", items={"A": TimelineItemContext(id="A")}),
                3: TrackContext(index=3, name="", items={"Y": TimelineItemContext(id="Y")}),
                4: TrackContext(index=4, name="", items={"B": TimelineItemContext(id="B")}),
                5: TrackContext(index=5, name="", items={"Z": TimelineItemContext(id="X")}),
            },
        )

        diff = TimelineDiff.create(old, new)

        assert diff.diff == {
            "added": {"video_tracks": {"root": [1, 3, 5]}},
            "changed": {
                "video_tracks": {
                    1: {"index": Diff(1, 2)},
                    2: {"index": Diff(2, 4)},
                },
            },
        }

    def test_removed_tracks(self):
        old = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
                4: TrackContext(index=4, name="", items={"D": TimelineItemContext(id="D")}),
                5: TrackContext(index=5, name="", items={"E": TimelineItemContext(id="E")}),
            },
        )
        new = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"B": TimelineItemContext(id="B")}),
                2: TrackContext(index=2, name="", items={"D": TimelineItemContext(id="D")}),
            },
        )

        diff = TimelineDiff.create(old, new)

        assert diff.diff == {
            "changed": {
                "video_tracks": {
                    2: {"index": Diff(2, 1)},
                    4: {"index": Diff(4, 2)},
                },
            },
            "removed": {"video_tracks": {"root": [1, 3, 5]}},
        }

    def test_moved_tracks(self):
        old = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B": TimelineItemContext(id="B")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
                4: TrackContext(index=4, name="", items={"D": TimelineItemContext(id="D")}),
                5: TrackContext(index=5, name="", items={"E": TimelineItemContext(id="E")}),
            },
        )
        new = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"D": TimelineItemContext(id="D")}),
                3: TrackContext(index=3, name="", items={"C": TimelineItemContext(id="C")}),
                4: TrackContext(index=4, name="", items={"B": TimelineItemContext(id="B")}),
                5: TrackContext(index=5, name="", items={"E": TimelineItemContext(id="E")}),
            },
        )

        diff = TimelineDiff.create(old, new)

        assert diff.diff == {
            "changed": {
                "video_tracks": {
                    2: {"index": Diff(2, 4)},
                    4: {"index": Diff(4, 2)},
                },
            },
        }

    def test_moved_items(self):
        old = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(index=1, name="", items={"A": TimelineItemContext(id="A")}),
                2: TrackContext(index=2, name="", items={"B1": TimelineItemContext(id="B1"), "B2": TimelineItemContext(id="B2")}),
                3: TrackContext(index=3, name="", items={"C1": TimelineItemContext(id="C1"), "C2": TimelineItemContext(id="C2")}),
                4: TrackContext(index=4, name="", items={}),
                5: TrackContext(index=5, name="", items={"E1": TimelineItemContext(id="E1"), "E2": TimelineItemContext(id="E2")}),
            },
        )
        new = TimelineContext(
            id="x",
            name="x",
            video_tracks={
                1: TrackContext(
                    index=1, name="", items={"A": TimelineItemContext(id="A"), "B1": TimelineItemContext(id="B1"), "B2": TimelineItemContext(id="B2")}
                ),
                2: TrackContext(index=2, name="", items={}),
                3: TrackContext(index=3, name="", items={}),
                4: TrackContext(index=4, name="", items={"C1": TimelineItemContext(id="C1"), "C2": TimelineItemContext(id="C2")}),
                5: TrackContext(index=5, name="", items={"E1": TimelineItemContext(id="E1")}),
                6: TrackContext(index=6, name="", items={"E2": TimelineItemContext(id="E2")}),
            },
        )

        diff = TimelineDiff.create(old, new)

        assert diff.diff == {
            "added": {
                "video_tracks": {
                    "root": [
                        3,
                        6,
                    ],
                    1: {"items": {"root": {"B1", "B2"}}},
                }
            },
            "changed": {
                "video_tracks": {
                    3: {"index": Diff(3, 4)},  # all items moved is considered as track moved
                },
            },
            "removed": {
                "video_tracks": {
                    "root": [4],
                    2: {"items": {"root": {"B1", "B2"}}},
                    5: {"items": {"root": {"E2"}}},
                }
            },
        }
