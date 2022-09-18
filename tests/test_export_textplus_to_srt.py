from datetime import timedelta

import pytest
import srt

from davinci_resolve_cli.davinci.timeline_context import TimelineContext
from davinci_resolve_cli.entry import export_textplus_to_srt


class TestExportSrt:
    @pytest.mark.mock_resolve_current_timeline({
        "setting": {"timelineFrameRate": 60.0},
        "start_timecode": "01:00:00:00",
        "tracks": {
            "video": {
                1: {
                    "items": [
                        {
                            "start": "01:00:00:00",
                            "end": "01:00:03:14",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "ABC"}}},
                        },
                        {
                            "start": "01:00:03:14",
                            "end": "01:00:06:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "DEF"}}},
                        },
                        {
                            "start": "01:00:10:00",
                            "end": "01:00:15:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "GHI"}}},
                        },
                    ]
                },
                2: {
                    "items": [
                        {
                            "start": "01:00:05:00",
                            "end": "01:00:11:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "XYZ"}}},
                        },
                        {
                            "start": "01:00:12:00",
                            "end": "01:00:13:00",
                            "fusion_comps": {},
                        },
                    ]
                },
                3: {
                    "items": []
                },
            },
        },
    })
    def test_create_subtitles_from_timeline(self, current_timeline):
        process = export_textplus_to_srt.Process()

        subtitles = process.create_subtitles_from_timeline(TimelineContext(current_timeline))

        expected_subtitles = [
            srt.Subtitle(index=None, start=timedelta(0), end=timedelta(seconds=3, microseconds=233333), content='ABC', proprietary='video track 1'),
            srt.Subtitle(index=None, start=timedelta(seconds=3, microseconds=233333), end=timedelta(seconds=6), content='DEF', proprietary='video track 1'),
            srt.Subtitle(index=None, start=timedelta(seconds=10), end=timedelta(seconds=15), content='GHI', proprietary='video track 1'),
            srt.Subtitle(index=None, start=timedelta(seconds=5), end=timedelta(seconds=11), content='XYZ', proprietary='video track 2'),
        ]

        assert subtitles == expected_subtitles
