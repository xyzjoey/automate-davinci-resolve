import inspect

import pytest
import srt

from davinci_resolve_cli.entry import import_textplus_from_srt
from davinci_resolve_cli.entry.import_textplus_from_srt import SubtitleInsertInfo


class TestTextplusFromSrt:
    @pytest.mark.mock_resolve_project({
        "setting": {"timelineFrameRate": 60.0},
    })
    def test_subtitle_insert_infos(self):
        action = import_textplus_from_srt.Action()

        assert action.prepare_subtitle_insert_context([]).infos == []

        assert action.prepare_subtitle_insert_context(srt.parse(inspect.cleandoc(  # copied from pypi.org/project/srt/
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
        ))).infos == [
            SubtitleInsertInfo(text_content=None, frames=2031),
            SubtitleInsertInfo(text_content="地球上只有3%的水是淡水", frames=255),
            SubtitleInsertInfo(text_content="可是这些珍贵的淡水中却充满了惊奇", frames=395),
            SubtitleInsertInfo(text_content=None, frames=793),
            SubtitleInsertInfo(text_content="所有陆地生命归根结底都依赖於淡水", frames=331),
        ]

        # skip overlapping subtitles
        assert action.prepare_subtitle_insert_context(srt.parse(inspect.cleandoc(
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
        ))).infos == [
            SubtitleInsertInfo(text_content=None, frames=2031),
            SubtitleInsertInfo(text_content="地球上只有3%的水是淡水", frames=255),
            SubtitleInsertInfo(text_content=None, frames=1188),
            SubtitleInsertInfo(text_content="所有陆地生命归根结底都依赖於淡水", frames=331),
        ]
