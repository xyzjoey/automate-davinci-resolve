from enum import Enum


class CharacterLevelStylingCopyMode(Enum):
    NONE = 0
    MAP_TO_LINES = 1


class SnapMode(Enum):
    NONE = 0
    AUTO = 1


class EffectType(Enum):
    ADJUST_TEXT_STYLE = 0
    INSERT_VIDEO = 1
    INSERT_AUDIO = 2

    def get_label(self):
        if self == EffectType.ADJUST_TEXT_STYLE:
            return "Adjust Text Style"
        elif self == EffectType.INSERT_VIDEO:
            return "Insert Video"
        elif self == EffectType.INSERT_AUDIO:
            return "Insert Audio"


class EffectTypeDeprecated(Enum):
    TEXT_ANIMATION = 0
    TEXT_STYLE = 1
    TRANSITION = 2
    VISUAL_OVERLAY = 3
    VISUAL_ADJUST = 4
    CAMERA_ADJUST = 5
    SOUND_EFFECT = 6
    BACKGROUND_MUSIC = 7


class GeneratedTrackName:
    EFFECT_CONTROL = "Generated Control"
    TEXT = "Generated Text+"
    VISUAL_OVERLAY = "Generated Visual Overlay"
    VISUAL_ADJUST = "Generated Visual Adjust"
    CAMERA_ADJUST = "Generated Camera Adjust"
    SOUND_EFFECT = "Generated SE"


EFFECT_TRACK_MAP = {
    # EffectTypeDeprecated.TRANSITION: ("video", GeneratedTrackName.TRANSITION),
    EffectTypeDeprecated.VISUAL_OVERLAY: ("video", GeneratedTrackName.VISUAL_OVERLAY),
    EffectTypeDeprecated.VISUAL_ADJUST: ("video", GeneratedTrackName.VISUAL_ADJUST),
    EffectTypeDeprecated.CAMERA_ADJUST: ("video", GeneratedTrackName.CAMERA_ADJUST),
    EffectTypeDeprecated.SOUND_EFFECT: ("audio", GeneratedTrackName.SOUND_EFFECT),
    # EffectTypeDeprecated.BACKGROUND_MUSIC: ("audio", GeneratedTrackName.BACKGROUND_MUSIC),
}
