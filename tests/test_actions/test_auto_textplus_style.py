import pytest

from automate_davinci_resolve.app.actions import auto_textplus_style
from automate_davinci_resolve.davinci.context import TimelineDiff, Diff


class TestAutoTextplusStyle:
    @pytest.fixture(autouse=True)
    def mock_timeline(self, resolve_app):
        resolve_app.mock_current_timeline(
            {
                "tracks": {
                    "video": {
                        1: {
                            "items": [
                                {"id": "A", "fusion_comps": {1: {"TextPlus": {}}}},
                                {"id": "B", "fusion_comps": {1: {"TextPlus": {}}}},
                                {"id": "C", "fusion_comps": {1: {"TextPlus": {}}}},
                            ]
                        },
                        2: {
                            "items": [
                                {"id": "D", "fusion_comps": {1: {"TextPlus": {}}}},
                                {"id": "E", "fusion_comps": {1: {"TextPlus": {}}}},
                            ]
                        },
                    }
                }
            }
        )

    def test_basic(self, resolve_app):
        action = auto_textplus_style.Action()

        timeline = resolve_app.get_current_timeline()
        timeline_diff = TimelineDiff()
        timeline_diff.diff = {"added": {"video_tracks": {1: {"items": {"__root__": {"C"}}}}}}

        styling_contexts = action.get_applicable_items(timeline, timeline_diff, [])

        assert set(styling_contexts.keys()) == {1}
        assert [target.item.GetUniqueId() for target in styling_contexts[1].targets] == ["C"]

    def test_ignore_tracks(self, resolve_app):
        action = auto_textplus_style.Action()

        timeline = resolve_app.get_current_timeline()
        timeline_diff = TimelineDiff()
        timeline_diff.diff = {"added": {"video_tracks": {1: {"items": {"__root__": {"C"}}}}}}

        styling_contexts = action.get_applicable_items(timeline, timeline_diff, ignored_tracks=[1])

        assert len(styling_contexts) == 0

    def test_moved_tracks(self, resolve_app):
        action = auto_textplus_style.Action()

        timeline = resolve_app.get_current_timeline()
        timeline_diff = TimelineDiff()
        timeline_diff.diff = {
            "added": {
                "video_tracks": {
                    "__root__": [1],
                    1: {"items": {"__root__": {"E"}}},
                }
            },
            "changed": {"video_tracks": {1: {"index": Diff(old=1, new=2)}}},
        }

        styling_contexts = action.get_applicable_items(timeline, timeline_diff, [])

        assert set(styling_contexts.keys()) == {2}
        assert [target.item.GetUniqueId() for target in styling_contexts[2].targets] == ["E"]
