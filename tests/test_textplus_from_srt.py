import inspect

import pytest
import srt

from davinci_resolve_cli.entry import textplus_from_srt
from davinci_resolve_cli.entry.textplus_from_srt import SubtitleInsertInfo


class TestTextplusFromSrt:
    @pytest.mark.mock_resolve_current_timeline({
        "setting": {"timelineFrameRate": 60.0},
    })
    def test_subtitle_insert_infos(self):
        process = textplus_from_srt.Process()

        assert process.prepare_subtitle_insert_infos([]) == []

        assert process.prepare_subtitle_insert_infos(srt.parse(inspect.cleandoc(  # copied from pypi.org/project/srt/
            """
            1
            00:00:33,843 --> 00:00:38,097
            地球上只有3%的水是淡水

            2
            00:00:38,097 --> 00:00:44,687
            可是这些珍贵的淡水中却充满了惊奇

            3
            00:00:57,908 --> 00:01:03,414
            所有陆地生命归根结底都依赖於淡水
            """
        ))) == [
            SubtitleInsertInfo(text_content="", frames=2031, is_gap_filler=True),
            SubtitleInsertInfo(text_content="地球上只有3%的水是淡水", frames=255, is_gap_filler=False),
            SubtitleInsertInfo(text_content="可是这些珍贵的淡水中却充满了惊奇", frames=395, is_gap_filler=False),
            SubtitleInsertInfo(text_content="", frames=793, is_gap_filler=True),
            SubtitleInsertInfo(text_content="所有陆地生命归根结底都依赖於淡水", frames=331, is_gap_filler=False),
        ]

        # skip overlapping subtitles
        assert process.prepare_subtitle_insert_infos(srt.parse(inspect.cleandoc(
            """
            1
            00:00:33,843 --> 00:00:38,097
            地球上只有3%的水是淡水

            2
            00:00:38,084 --> 00:00:44,687
            This is overlapping with the previous

            3
            00:00:57,908 --> 00:01:03,414
            所有陆地生命归根结底都依赖於淡水
            """
        ))) == [
            SubtitleInsertInfo(text_content="", frames=2031, is_gap_filler=True),
            SubtitleInsertInfo(text_content="地球上只有3%的水是淡水", frames=255, is_gap_filler=False),
            SubtitleInsertInfo(text_content="", frames=1188, is_gap_filler=True),
            SubtitleInsertInfo(text_content="所有陆地生命归根结底都依赖於淡水", frames=331, is_gap_filler=False),
        ]
