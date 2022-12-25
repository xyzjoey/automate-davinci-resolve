from datetime import datetime, time, timedelta


class TimecodeUtils:
    @staticmethod
    def timedelta_to_frame(td: timedelta, frame_rate: float) -> int:
        return round((td.seconds + (td.microseconds / 1e+6)) * frame_rate)

    @staticmethod
    def str_to_frame(timecode: str, frame_rate: float) -> int:
        dt = datetime.strptime(timecode[:-3], "%H:%M:%S")
        frame = int(timecode[-2:])

        return int((dt.hour * 3600 + dt.minute * 60 + dt.second) * frame_rate + frame)

    @staticmethod
    def frame_to_timedelta(frame: int, frame_rate: float) -> timedelta:
        total_seconds, remain_frames = divmod(frame, frame_rate)
        hours, remain_seconds = divmod(total_seconds, 3600)
        minutes, remain_seconds = divmod(remain_seconds, 60)
        microseconds = 1e+6 * remain_frames / frame_rate

        return timedelta(hours=hours, minutes=minutes, seconds=remain_seconds, microseconds=microseconds)

    @staticmethod
    def frame_to_str(frame: int, frame_rate: float) -> str:
        total_seconds, remain_frames = divmod(frame, frame_rate)
        hours, remain_seconds = divmod(total_seconds, 3600)
        minutes, remain_seconds = divmod(remain_seconds, 60)

        t = time(hour=int(hours), minute=int(minutes), second=int(remain_seconds))

        return f"{t.strftime('%H:%M:%S')}:{remain_frames:02.0f}"


class TimecodeContext:
    def __init__(self, start_timecode: str, frame_rate: float):
        self.start_timecode_str: str = start_timecode
        self.start_timecode: int = TimecodeUtils.str_to_frame(start_timecode, frame_rate)
        self.frame_rate: float = frame_rate

    def __repr__(self):
        return f"TimecodeContext(start_timecode={self.start_timecode_str}, frame_rate={self.frame_rate})"


class Timecode:
    def __init__(self):
        self.raw_frame: int = None
        self.context: TimecodeContext = None

    @staticmethod
    def __create(raw_frame: int, timecode_context: TimecodeContext):
        timecode = Timecode()
        timecode.raw_frame = raw_frame
        timecode.context = timecode_context
        return timecode

    @classmethod
    def from_frame(cls, frame: int, timecode_context: TimecodeContext, start_timecode_applied: bool):
        raw_frame = (frame - timecode_context.start_timecode) if start_timecode_applied else frame

        return cls.__create(raw_frame, timecode_context)

    @classmethod
    def from_timedelta(cls, td: timedelta, timecode_context: TimecodeContext, start_timecode_applied: bool):
        frame = TimecodeUtils.timedelta_to_frame(td, timecode_context.frame_rate)
        
        return cls.from_frame(frame, timecode_context, start_timecode_applied)

    @classmethod
    def from_str(cls, timecode: str, timecode_context: TimecodeContext, start_timecode_applied: bool):
        frame = TimecodeUtils.str_to_frame(timecode, timecode_context.frame_rate)

        return cls.from_frame(frame, timecode_context, start_timecode_applied)

    def get_frame(self, apply_start_timecode: bool) -> int:
        final_frame = (self.raw_frame + self.context.start_timecode) if apply_start_timecode else self.raw_frame

        return final_frame

    def get_timedelta(self, apply_start_timecode: bool) -> timedelta:
        final_frame = self.get_frame(apply_start_timecode)

        return TimecodeUtils.frame_to_timedelta(final_frame, self.context.frame_rate)

    def get_str(self, apply_start_timecode: bool) -> str:
        final_frame = self.get_frame(apply_start_timecode)

        return TimecodeUtils.frame_to_str(final_frame, self.context.frame_rate)
