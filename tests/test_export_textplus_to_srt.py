from datetime import timedelta

import pytest
import srt

from davinci_resolve_cli.davinci.clip_color import ClipColor
from davinci_resolve_cli.davinci.timeline_context import TimelineContext
from davinci_resolve_cli.entry import export_textplus_to_srt
from davinci_resolve_cli.entry.export_textplus_to_srt import SubtitleModeMap


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
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "normal"}}},
                        },
                        {
                            "start": "01:00:03:14",
                            "end": "01:00:06:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "will be trimmed"}}},
                        },
                        {
                            "start": "01:00:10:00",
                            "end": "01:00:15:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "will be merged"}}},
                        },
                    ]
                },
                2: {
                    "items": [
                        {
                            "start": "01:00:05:00",
                            "end": "01:00:11:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "replace overlap"}}},
                        },
                        {
                            "start": "01:00:12:00",
                            "end": "01:00:13:00",
                            "fusion_comps": {}, # will be ignored
                        },
                        {
                            "start": "01:00:13:00",
                            "end": "01:00:20:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "merge overlap"}}},
                            "clip_color": "Beige",
                        },
                        {
                            "start": "01:00:30:00",
                            "end": "01:00:35:00",
                            "fusion_comps": {1: {"TextPlus": {"StyledText": "ignored"}}},
                            "clip_color": "Brown",
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
        inputs = export_textplus_to_srt.Inputs(
            subtitle_path="dummy",
            merge_mode_color=ClipColor.Beige,
            ignore_mode_color=ClipColor.Brown,
        )
        process = export_textplus_to_srt.Process()
        timeline_context = TimelineContext(current_timeline)

        subtitle_infos = process.get_text_clip_infos(timeline_context, SubtitleModeMap(inputs))
        subtitles = process.get_subtitles(subtitle_infos, timeline_context.get_timecode_context())

        expected_subtitles = [
            srt.Subtitle(index=None, start=timedelta(0), end=timedelta(seconds=3, microseconds=233333), content="normal"),
            srt.Subtitle(index=None, start=timedelta(seconds=3, microseconds=233333), end=timedelta(seconds=5), content="will be trimmed"),
            srt.Subtitle(index=None, start=timedelta(seconds=5), end=timedelta(seconds=10), content="replace overlap"),
            srt.Subtitle(index=None, start=timedelta(seconds=10), end=timedelta(seconds=13), content="will be merged"),
            srt.Subtitle(index=None, start=timedelta(seconds=13), end=timedelta(seconds=15), content="will be merged\nmerge overlap"),
            srt.Subtitle(index=None, start=timedelta(seconds=15), end=timedelta(seconds=20), content="merge overlap"),
        ]

        assert subtitles == expected_subtitles
