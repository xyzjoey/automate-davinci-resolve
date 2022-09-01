from datetime import datetime, time, timedelta


class TimecodeContext:
    def __init__(self, start_timecode: str, frame_rate: float):
        self.start_timecode: int = Timecode.to_frame(start_timecode, frame_rate)
        self.frame_rate: float = frame_rate

    def create_timecode_from_frame(self, frame: int, start_timecode_is_applied: bool):
        final_frame = (frame - self.start_timecode) if start_timecode_is_applied else frame

        return Timecode(self.start_timecode, self.frame_rate, final_frame)

    def create_timecode_from_timedelta(self, td: timedelta, start_timecode_is_applied: bool):
        frame = round((td.seconds + (td.microseconds / 1e+6)) * self.frame_rate)

        if start_timecode_is_applied:
            frame -= self.start_timecode

        return Timecode(self.start_timecode, self.frame_rate, frame)

    def create_timecode_from_str(self, timecode: str, start_timecode_is_applied: bool):
        frame = Timecode.to_frame(timecode, self.frame_rate)

        if start_timecode_is_applied:
            frame -= self.start_timecode

        return Timecode(self.start_timecode, self.frame_rate, frame)


class Timecode:
    def __init__(self, start_timecode: int, frame_rate: float, frame: int):
        self.start_timecode = start_timecode
        self.frame_rate = frame_rate
        self.frame = frame

    def get_timedelta(self):
        total_seconds, remain_frames = divmod(self.frame, self.frame_rate)
        hours, remain_seconds = divmod(total_seconds, 3600)
        minutes, remain_seconds = divmod(remain_seconds, 60)
        microseconds = 1e+6 * remain_frames / self.frame_rate

        return timedelta(hours=hours, minutes=minutes, seconds=remain_seconds, microseconds=microseconds)

    def get_formatted(self, apply_start_timecode: bool):
        final_frame = self.frame + self.start_timecode if apply_start_timecode else self.frame

        total_seconds, remain_frames = divmod(final_frame, self.frame_rate)
        hours, remain_seconds = divmod(total_seconds, 3600)
        minutes, remain_seconds = divmod(remain_seconds, 60)

        t = time(hour=int(hours), minute=int(minutes), second=int(remain_seconds))

        return f"{t.strftime('%H:%M:%S')}:{remain_frames:02.0f}"

    def get_frame(self, apply_start_timecode: bool):
        final_frame = (self.frame + self.start_timecode) if apply_start_timecode else self.frame

        return final_frame

    @staticmethod
    def to_timedelta(timecode: str, frame_rate: float) -> timedelta:
        dt = datetime.strptime(timecode[:-3], "%H:%M:%S")
        frame = int(timecode[-2:])

        return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=1e+6 * frame / frame_rate)

    @staticmethod
    def to_frame(timecode: str, frame_rate: float) -> int:
        dt = datetime.strptime(timecode[:-3], "%H:%M:%S")
        frame = int(timecode[-2:])

        return int((dt.hour * 3600 + dt.minute * 60 + dt.second) * frame_rate + frame)

    @staticmethod
    def from_frame(frame, frame_rate: float) -> str:
        total_seconds, remain_frames = divmod(frame, frame_rate)
        hours, remain_seconds = divmod(total_seconds, 3600)
        minutes, remain_seconds = divmod(remain_seconds, 60)
        t = time(hour=int(hours), minute=int(minutes), second=int(remain_seconds))

        return f"{t.strftime('%H:%M:%S')}:{remain_frames :02.0f}"
