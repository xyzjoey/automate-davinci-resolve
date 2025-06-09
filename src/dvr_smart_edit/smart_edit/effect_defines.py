from dataclasses import asdict, dataclass, field
from pprint import pprint

from .constants import EffectType


@dataclass
class EffectTrackSettings:
    track_name: str = ""
    track_name_default: str = ""
    effect_type: EffectType = EffectType.INSERT_VIDEO
    media_pool_filter_by_keyword: list[str] = field(default_factory=list)
    media_pool_filter_by_folder: list[str] = field(default_factory=list)


@dataclass
class EffectControlTrackSettings:
    track_name: str = ""
    track_name_default: str = ""
    effect_tracks: list[EffectTrackSettings] = field(default_factory=list)


@dataclass
class EffectTracksSettings:
    effect_control_tracks: list[EffectControlTrackSettings]

    def as_dict(self):
        return asdict(self)

    @staticmethod
    def from_lua_like_table(table: dict):
        return EffectTracksSettings(
            effect_control_tracks=[
                EffectControlTrackSettings(
                    **{k: v for k, v in effect_control_track_data.items() if k != "effect_tracks"},
                    effect_tracks=[
                        EffectTrackSettings(
                            **effect_track_data,
                        )
                        for effect_track_data in effect_control_track_data.get("effect_tracks", {}).values()
                    ],
                )
                for effect_control_track_data in table.get("effect_control_tracks", {}).values()
            ]
        )


DEFAULT_EFFECT_TRACKS_SETTINGS = EffectTracksSettings(
    effect_control_tracks=[
        EffectControlTrackSettings(
            track_name="Effect Control",
            track_name_default="Effect Control 1",
            effect_tracks=[
                EffectTrackSettings(
                    track_name="Generated Text+",
                    track_name_default="Effect 1",
                    effect_type=EffectType.ADJUST_TEXT_STYLE,
                ),
                EffectTrackSettings(
                    track_name="Generated Visual Effect",
                    track_name_default="Effect 2",
                    effect_type=EffectType.INSERT_VIDEO,
                ),
                EffectTrackSettings(
                    track_name="Generated SE",
                    track_name_default="Effect 3",
                    effect_type=EffectType.INSERT_AUDIO,
                    media_pool_filter_by_keyword=["se"],
                ),
            ],
        )
    ]
)
