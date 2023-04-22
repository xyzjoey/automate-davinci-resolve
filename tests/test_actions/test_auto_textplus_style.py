import pytest

from automate_davinci_resolve.app.actions import auto_textplus_style
from automate_davinci_resolve.app.context import InputContext
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
                                {
                                    "id": "A",
                                    "fusion_comps": {1: {"TextPlus": {"StyledText": "Item A", "Size": 10}}},
                                },
                                {
                                    "id": "B",
                                    "fusion_comps": {1: {"TextPlus": {"StyledText": "Item B", "Size": 20}}},
                                },
                                {
                                    "id": "C",
                                    "fusion_comps": {1: {"TextPlus": {"StyledText": "Item C", "Size": 30}}},
                                },
                            ]
                        },
                        2: {
                            "items": [
                                {
                                    "id": "D",
                                    "fusion_comps": {1: {"TextPlus": {"StyledText": "Item D", "Size": 40}}},
                                },
                                {
                                    "id": "E",
                                    "fusion_comps": {1: {"TextPlus": {"StyledText": "Item E", "Size": 50}}},
                                },
                            ]
                        },
                    }
                }
            }
        )

    def test_basic(self, resolve_app):
        action = auto_textplus_style.Action()
        timeline_diff = TimelineDiff()
        timeline_diff.diff = {"added": {"video_tracks": {1: {"items": {"root": {"C"}}}}}}
        input_data = auto_textplus_style.Inputs()

        action.update(
            resolve_app=resolve_app,
            timeline_diff=timeline_diff,
            input_data=input_data,
        )

        assert resolve_app.get_mocked_current_timeline()["tracks"]["video"] == {
            1: {
                "items": [
                    {
                        "id": "A",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item A", "Size": 10}}},
                    },
                    {
                        "id": "B",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item B", "Size": 20}}},
                    },
                    {
                        "id": "C",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item C", "Size": 10}}},
                    },
                ]
            },
            2: {
                "items": [
                    {
                        "id": "D",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item D", "Size": 40}}},
                    },
                    {
                        "id": "E",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item E", "Size": 50}}},
                    },
                ]
            },
        }

    def test_ignore_tracks(self, resolve_app):
        action = auto_textplus_style.Action()
        timeline_diff = TimelineDiff()
        timeline_diff.diff = {"added": {"video_tracks": {1: {"items": {"root": {"C"}}}}}}
        InputContext.set(InputContext(resolve_app.get_current_timeline().capture_context()))
        input_data = auto_textplus_style.Inputs(ignored_tracks=[1])

        action.update(
            resolve_app=resolve_app,
            timeline_diff=timeline_diff,
            input_data=input_data,
        )

        assert resolve_app.get_mocked_current_timeline()["tracks"]["video"] == {
            1: {
                "items": [
                    {
                        "id": "A",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item A", "Size": 10}}},
                    },
                    {
                        "id": "B",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item B", "Size": 20}}},
                    },
                    {
                        "id": "C",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item C", "Size": 30}}},
                    },
                ]
            },
            2: {
                "items": [
                    {
                        "id": "D",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item D", "Size": 40}}},
                    },
                    {
                        "id": "E",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item E", "Size": 50}}},
                    },
                ]
            },
        }

    def test_moved_tracks(self, resolve_app):
        action = auto_textplus_style.Action()
        timeline_diff = TimelineDiff()
        timeline_diff.diff = {
            "added": {
                "video_tracks": {
                    "root": [1],
                    1: {"items": {"root": {"E"}}},
                }
            },
            "changed": {"video_tracks": {1: {"index": Diff(old=1, new=2)}}},
        }
        InputContext.set(InputContext(resolve_app.get_current_timeline().capture_context()))
        input_data = auto_textplus_style.Inputs(ignored_tracks=[1])

        action.update(
            resolve_app=resolve_app,
            timeline_diff=timeline_diff,
            input_data=input_data,
        )

        assert resolve_app.get_mocked_current_timeline()["tracks"]["video"] == {
            1: {
                "items": [
                    {
                        "id": "A",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item A", "Size": 10}}},
                    },
                    {
                        "id": "B",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item B", "Size": 20}}},
                    },
                    {
                        "id": "C",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item C", "Size": 30}}},
                    },
                ]
            },
            2: {
                "items": [
                    {
                        "id": "D",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item D", "Size": 40}}},
                    },
                    {
                        "id": "E",
                        "fusion_comps": {1: {"TextPlus": {"StyledText": "Item E", "Size": 40}}},
                    },
                ]
            },
        }
