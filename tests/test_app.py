from davinci_resolve_cli.davinci.enums import ResolveStatus
from davinci_resolve_cli.davinci.context import TrackContext, TimelineItemContext
from davinci_resolve_cli.app.context import InputContext


class TestApp:
    def test_resolve_down(self, app):
        assert app.context.resolve_context.resolve_status == ResolveStatus.Unavailable

        app.update()

        assert app.context.resolve_context.resolve_status == ResolveStatus.Unavailable

    def test_resolve_up(self, resolve_app, app):
        resolve_app.mock_current_timeline({})

        assert app.context.resolve_context.resolve_status == ResolveStatus.Unavailable

        app.update()

        assert app.context.resolve_context.resolve_status == ResolveStatus.TimelineOpened

    def test_update_context(self, resolve_app, app):
        resolve_app.mock_current_timeline({"tracks": {"video": {1: {"items": [{"id": "A"}]}}}})

        assert app.context.resolve_context.timeline_context is None
        assert InputContext.get() is None

        app.update()

        assert app.context.resolve_context.timeline_context.video_tracks == {1: TrackContext(index=1, name=None, items={"A": TimelineItemContext(id="A")})}
        assert InputContext.get().timeline_context.video_tracks == {1: TrackContext(index=1, name=None, items={"A": TimelineItemContext(id="A")})}

    def test_update_context_on_start(self, resolve_app, app):
        resolve_app.mock_current_timeline({"tracks": {"video": {1: {"items": [{"id": "A"}]}}}})

        assert app.context.resolve_context.timeline_context is None
        assert InputContext.get() is None

        app.start_action("auto_textplus_style", {})

        assert app.context.resolve_context.timeline_context.video_tracks == {1: TrackContext(index=1, name=None, items={"A": TimelineItemContext(id="A")})}
        assert InputContext.get().timeline_context.video_tracks == {1: TrackContext(index=1, name=None, items={"A": TimelineItemContext(id="A")})}
