from typing import NamedTuple


class TrackHandle(NamedTuple):
    type: str
    index: int

    def get_short_name(self):
        if type == "subtitle":
            return f"ST{self.index}"
        else:
            return f"{self.type[0].upper()}{self.index}"
