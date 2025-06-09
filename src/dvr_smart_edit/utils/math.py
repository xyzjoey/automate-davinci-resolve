from dataclasses import dataclass


@dataclass
class FrameRange:
    start: int
    end: int  # exclusive

    @classmethod
    def is_overlapped(cls, range1: "FrameRange", range2: "FrameRange"):
        return range1.start < range2.end and range1.end > range2.start

    @classmethod
    def is_overlapped_by_percentage(cls, range1: "FrameRange", range2: "FrameRange", percentage=0.5):
        overlapped_range = FrameRange(max(range1.start, range2.start), min(range1.end, range2.end))
        overlapped_duration = overlapped_range.end - overlapped_range.start
        range1_duration = range1.end - range1.start
        range2_duration = range2.end - range2.start

        if (overlapped_duration / range1_duration >= percentage) or (overlapped_duration / range2_duration >= percentage):
            return True

        return False

    @classmethod
    def is_started_in_range(cls, range1: "FrameRange", range2: "FrameRange"):
        return range2.start <= range1.start and range1.start < range2.end
