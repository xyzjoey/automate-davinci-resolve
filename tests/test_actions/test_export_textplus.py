from datetime import timedelta

import srt

from davinci_resolve_cli.app.actions import export_textplus
from davinci_resolve_cli.app.actions.export_textplus import SubtitleModeMap


class TestExportTextplus:
    def test_create_subtitles_from_timeline(self, resolve_app, test_settings):
        resolve_app.mock_current_timeline(
            {
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
                                    "fusion_comps": {},  # will be ignored
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
                        3: {"items": []},
                    },
                },
            }
        )

        inputs = export_textplus.Inputs(subtitle_file=f"{test_settings.resource_dir}/dummy.txt")
        action = export_textplus.Action()
        timeline = resolve_app.get_current_timeline()

        subtitle_infos = action.get_text_clip_infos(timeline, SubtitleModeMap(inputs))
        subtitles = action.get_subtitles(subtitle_infos, timeline.get_timecode_settings())

        expected_subtitles = [
            srt.Subtitle(index=None, start=timedelta(0), end=timedelta(seconds=3, microseconds=233333), content="normal"),
            srt.Subtitle(index=None, start=timedelta(seconds=3, microseconds=233333), end=timedelta(seconds=5), content="will be trimmed"),
            srt.Subtitle(index=None, start=timedelta(seconds=5), end=timedelta(seconds=10), content="replace overlap"),
            srt.Subtitle(index=None, start=timedelta(seconds=10), end=timedelta(seconds=13), content="will be merged"),
            srt.Subtitle(index=None, start=timedelta(seconds=13), end=timedelta(seconds=15), content="will be merged\nmerge overlap"),
            srt.Subtitle(index=None, start=timedelta(seconds=15), end=timedelta(seconds=20), content="merge overlap"),
        ]

        assert subtitles == expected_subtitles
