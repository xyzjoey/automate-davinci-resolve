import inspect

import srt

from automate_davinci_resolve.app.actions import import_textplus
from automate_davinci_resolve.app.actions.import_textplus import SubtitleInfo


class TestImportTextplus:
    def test_empty(self, resolve_app):
        resolve_app.mock_current_project({"setting": {"timelineFrameRate": 60.0}})
        action = import_textplus.Action()

        assert action.prepare_subtitle_infos([]) == []

    def test_basic(self, resolve_app):
        resolve_app.mock_current_project({"setting": {"timelineFrameRate": 60.0}})
        action = import_textplus.Action()

        assert (
            action.prepare_subtitle_infos(
                srt.parse(
                    inspect.cleandoc(  # from pypi.org/project/srt/
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
                    )
                ),
            )
            == [
                SubtitleInfo(text_content="地球上只有3%的水是淡水", record_frame=218031, frames=255),
                SubtitleInfo(text_content="可是这些珍贵的淡水中却充满了惊奇", record_frame=218286, frames=395),
                SubtitleInfo(text_content="所有陆地生命归根结底都依赖於淡水", record_frame=219474, frames=331),
            ]
        )

    def test_overlap(self, resolve_app):
        resolve_app.mock_current_project({"setting": {"timelineFrameRate": 60.0}})
        action = import_textplus.Action()

        # skip overlapping subtitles
        assert (
            action.prepare_subtitle_infos(
                srt.parse(
                    inspect.cleandoc(
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
                    )
                ),
            )
            == [
                SubtitleInfo(text_content="地球上只有3%的水是淡水", record_frame=218031, frames=255),
                SubtitleInfo(text_content="所有陆地生命归根结底都依赖於淡水", record_frame=219474, frames=331),
            ]
        )
