import itertools
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta

from ..extended_resolve import davinci_resolve_module
from ..extended_resolve.constants import MediaPoolItemType
from ..extended_resolve.media_pool import MediaPool
from ..extended_resolve.media_pool_item import MediaPoolItem
from ..extended_resolve.resolve import MediaPoolItemInsertInfo
from ..extended_resolve.timecode import TimecodeUtils
from ..extended_resolve.timeline import Timeline
from ..extended_resolve.timeline_item import TimelineItem
from ..extended_resolve.track import TrackHandle
from ..utils.math import FrameRange
from .constants import EFFECT_TRACK_MAP, EffectTypeDeprecated, GeneratedTrackName
from .errors import UserError
from .smart_edit_bin import SmartEditBin
from .textplus_utilities import TextPlusUtilities
from .ui.loading_window import LoadingWindow


class KeywordMatcher:
    def __init__(self, keywords: list[str]):
        self.keywords = keywords
        self.keyword_patterns = [f"{r'\b'}{k}{r'\b'}" for k in keywords]

    def match(self, string):
        matched_keywords = []

        for keyword, pattern in zip(self.keywords, self.keyword_patterns):
            if re.search(pattern, string) is not None:
                matched_keywords.append(keyword)

        return matched_keywords


SelectedEffects = dict[EffectTypeDeprecated, MediaPoolItem]


class EffectSelector:
    def __init__(self, media_pool: MediaPool):
        self.media_pool_item_infos = []
        self.cached_candidates = {}

        for item in media_pool.iter_items():
            effect_type, support_keyword = self._get_item_type(item)
            self.media_pool_item_infos.append(
                {
                    "media_pool_item": item,
                    "effect_type": effect_type,
                    "support_keyword": support_keyword,
                }
            )

    def select(self, keywords: list[str]) -> SelectedEffects:
        keywords_tuple = tuple(keywords)
        candidates = self.cached_candidates.get(keywords_tuple)

        if candidates is None:
            candidates = self._gather_candidates(keywords)
            self.cached_candidates[keywords_tuple] = candidates

        return self._select_from_candidates(candidates)

    def _gather_candidates(self, keywords):
        keyword_matcher = KeywordMatcher(keywords)
        candidates: dict[MediaPoolItem, list[tuple[MediaPoolItem, int]]] = defaultdict(list)

        for item_info in self.media_pool_item_infos:
            item = item_info["media_pool_item"]
            effect_type = item_info["effect_type"]

            if item_info["support_keyword"]:
                matched_keywords = keyword_matcher.match(item.get_keyword())
            else:
                matched_keywords = keyword_matcher.match(item.get_clip_name())

            if matched_keywords:
                candidates[effect_type].append({"media_pool_item": item, "matched_keywords": matched_keywords})

        return candidates

    def _select_from_candidates(self, candidates):
        return {k: v[0]["media_pool_item"] for k, v in candidates.items()}  # TODO: use strategy options

    @classmethod
    def _get_item_type(cls, item: MediaPoolItem):
        item_type = item.get_clip_type()
        support_keyword = MediaPoolItemType.support_keyword(item_type)

        if item_type == MediaPoolItemType.FUSION_TITLE:
            if "text_animation" in item.folder.folder_path.get_names():
                return EffectTypeDeprecated.TEXT_ANIMATION, support_keyword
            else:
                return EffectTypeDeprecated.TEXT_STYLE, support_keyword
        elif item_type == MediaPoolItemType.AUDIO:
            duration = item.get_duration_as_timedelta()

            if duration <= timedelta(seconds=30):
                return EffectTypeDeprecated.SOUND_EFFECT, support_keyword
            else:
                return EffectTypeDeprecated.BACKGROUND_MUSIC, support_keyword
        else:
            folder_names = item.folder.folder_path.get_names()
            if "visual_adjust" in folder_names:
                return EffectTypeDeprecated.VISUAL_ADJUST, support_keyword
            elif "camera_adjust" in folder_names:
                return EffectTypeDeprecated.CAMERA_ADJUST, support_keyword
            else:
                return EffectTypeDeprecated.VISUAL_OVERLAY, support_keyword


class EffectControl:
    @classmethod
    def generate_effect_control_clips(cls):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        media_pool_item = SmartEditBin.get_or_import_effect_control()

        if media_pool_item is None:
            raise Exception(f"Failed to import clip `{SmartEditBin.ClipName.EFFECT_CONTROL}`")

        textplus_track_handle = timeline.find_track_by_name("video", "Generated Text+")

        if textplus_track_handle is None:
            raise UserError("Missing `Generated Text+` track")

        track_handle = cls._get_or_add_effect_control_track(timeline)

        with timeline.rollback_playhead_on_exit():
            old_items = list(timeline.iter_items_in_track(track_handle))
            LoadingWindow.set_message(f"Deleting {len(old_items)} clips...")
            timeline.delete_items(old_items)

            textplus_items = list(timeline.iter_items_in_track(textplus_track_handle))
            LoadingWindow.set_message(f"Inserting {len(textplus_items)} clips...")
            resolve.insert_to_timeline(
                [
                    MediaPoolItemInsertInfo(
                        media_pool_item=media_pool_item,
                        start_frame=textplus_item._item.GetStart(),
                        frames=textplus_item._item.GetDuration(),
                        track_handle=track_handle,
                    )
                    for textplus_item in textplus_items
                ]
            )

        timeline.set_track_locked(track_handle, True)

    @classmethod
    def reload_all(cls):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        media_pool_item = SmartEditBin.get_or_import_effect_control()

        if media_pool_item is None:
            raise Exception(f"Failed to import clip `{SmartEditBin.ClipName.EFFECT_CONTROL}`")

        dst_items = list(timeline.iter_items(lambda item: cls._is_effect_control_clip(item), track_type="video"))

        cls._reinsert_effect_control_clips(timeline, dst_items, media_pool_item)

    @classmethod
    def reload_clip(cls, destinated_item: TimelineItem):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()
        media_pool_item = SmartEditBin.get_or_import_effect_control()

        if media_pool_item is None:
            raise Exception(f"Failed to import clip `{SmartEditBin.ClipName.EFFECT_CONTROL}`")

        cls._reinsert_effect_control_clips(timeline, [destinated_item], media_pool_item)

    @classmethod
    def apply_effect_for_all(cls):
        resolve = davinci_resolve_module.get_resolve()
        timeline = resolve.get_current_timeline()

        track_handle = timeline.find_track_by_name("video", GeneratedTrackName.EFFECT_CONTROL)

        if track_handle is not None:
            dst_items = list(timeline.iter_items_in_track(track_handle, lambda item: cls._is_effect_control_clip(item)))

            if dst_items:
                cls._apply_effect_for_clips(dst_items)

    @classmethod
    def apply_effect_for_clip(cls, destinated_item: TimelineItem):
        cls._apply_effect_for_clips([destinated_item])

    @classmethod
    def _apply_effect_for_clips(cls, effect_control_items: list[TimelineItem]):
        resolve = davinci_resolve_module.get_resolve()
        media_pool = resolve.get_media_pool()
        timeline = resolve.get_current_timeline()

        effect_selector = EffectSelector(media_pool)
        generated_tracks = cls._get_or_add_effect_tracks(timeline)

        with timeline.temp_unlock_tracks(*generated_tracks.values()):
            LoadingWindow.set_message("Cutting overlapped clips in effect tracks...")
            cls._clear_ranges_in_tracks(
                timeline=timeline,
                track_handles=[t for t in generated_tracks.values() if t is not None],
                frame_ranges=[item.get_frame_range() for item in effect_control_items],
            )

            LoadingWindow.set_message(f"Selecting effects for {len(effect_control_items)} EffectControl clips...")
            all_selected_effects = [effect_selector.select(cls._get_keywords(item)) for item in effect_control_items]

            LoadingWindow.set_message(f"Copying Text+ style...")
            cls._apply_text_styles(timeline, effect_control_items, all_selected_effects)

            insert_infos = []

            for item, selected_effects in zip(effect_control_items, all_selected_effects):
                frame_range = item.get_frame_range()

                for effect_type in [
                    EffectTypeDeprecated.VISUAL_OVERLAY,
                    EffectTypeDeprecated.VISUAL_ADJUST,
                    EffectTypeDeprecated.CAMERA_ADJUST,
                    EffectTypeDeprecated.SOUND_EFFECT,
                ]:
                    track_handle = generated_tracks.get(effect_type)
                    media_pool_item = selected_effects.get(effect_type)
                    if track_handle is not None and media_pool_item is not None:
                        insert_infos.append(
                            MediaPoolItemInsertInfo(
                                media_pool_item=media_pool_item,
                                start_frame=frame_range.start,
                                end_frame=frame_range.end,
                                track_handle=track_handle,
                            )
                        )

            if insert_infos:
                LoadingWindow.set_message(f"Inserting {len(insert_infos)} effect clips...")
                resolve.insert_to_timeline(insert_infos)

    @classmethod
    def _apply_text_styles(cls, timeline: Timeline, effect_control_items: list[TimelineItem], all_selected_effects: list[SelectedEffects]):
        textplus_map = {}

        for item, selected_effects in zip(effect_control_items, all_selected_effects):
            src_item = selected_effects.get(EffectTypeDeprecated.TEXT_STYLE)
            dst_items = cls._find_generated_textplus_in_range(timeline, item.get_frame_range())

            if src_item is not None:
                key = src_item._item.GetUniqueId()
                textplus_map.setdefault(key, {"media_pool_item": src_item, "destinated_items": []})
                textplus_map[key]["destinated_items"].extend(dst_items)

        for map in textplus_map.values():
            TextPlusUtilities.copy_style_for_clips(map["destinated_items"], map["media_pool_item"])

    # FIXME: dont assume track per effect type
    @classmethod
    def _get_or_add_effect_tracks(cls, timeline: Timeline) -> dict[EffectTypeDeprecated, TrackHandle | None]:
        tracks = {}

        before_video_track_handle = timeline.find_track_by_name("video", GeneratedTrackName.TEXT)

        for effect_type, (track_type, track_name) in EFFECT_TRACK_MAP.items():
            track_handle = timeline.find_track_by_name(track_type, track_name)

            if track_handle is None:
                if track_type == "video" and before_video_track_handle is not None:
                    track_handle = timeline.get_or_add_track_by_name(track_type, track_name, before_video_track_handle.index)
                else:
                    track_handle = timeline.get_or_add_track_by_name(track_type, track_name)

                if track_handle is not None:
                    timeline.set_track_locked(track_handle, True)

            if track_type == "video":
                before_video_track_handle = TrackHandle("video", min(before_video_track_handle.index, track_handle.index))

            tracks[effect_type] = track_handle

        return tracks

    @classmethod
    def _merge_frame_ranges(cls, frame_ranges: list[FrameRange]):
        merged_frame_ranges = []
        pending_frame_range = frame_ranges[0]

        for frame_range in frame_ranges[1:]:
            if pending_frame_range.end == frame_range.start:
                pending_frame_range.end = frame_range.end
            else:
                merged_frame_ranges.append(pending_frame_range)
                pending_frame_range = frame_range

        merged_frame_ranges.append(pending_frame_range)

        return merged_frame_ranges

    @classmethod
    def _clear_ranges_in_tracks(
        cls,
        timeline: Timeline,
        track_handles: dict[EffectTypeDeprecated, TrackHandle | None],
        frame_ranges: list[FrameRange],
    ):
        resolve = davinci_resolve_module.get_resolve()
        merged_frame_ranges = cls._merge_frame_ranges(frame_ranges)

        items_to_delete = []
        item_insert_infos = []

        for frame_range in merged_frame_ranges:
            overlapped_items: list[TimelineItem] = []

            for track_handle in track_handles:
                overlapped_items.extend(timeline.iter_items_in_track(track_handle, lambda item: FrameRange.is_overlapped(frame_range, item.get_frame_range())))

            for item in overlapped_items:
                media_pool_item = item.get_media_pool_item()
                item_new_range = item.get_frame_range()
                source_start_frame = item._item.GetSourceStartFrame()

                if item_new_range.start < frame_range.start:
                    item_new_range.end = frame_range.start
                elif item_new_range.end > frame_range.end:
                    if media_pool_item is not None:
                        delta = frame_range.end - item_new_range.start
                        source_start_frame += TimecodeUtils.frame_to_frame(delta, timeline.get_frame_rate(), media_pool_item.get_frame_rate())
                    item_new_range.start = frame_range.end
                else:
                    item_new_range = None

                items_to_delete.append(item)

                if media_pool_item is not None and item_new_range is not None:
                    item_insert_infos.append(
                        MediaPoolItemInsertInfo(
                            media_pool_item=media_pool_item,
                            start_frame=item_new_range.start,
                            end_frame=item_new_range.end,
                            source_start_frame=source_start_frame,
                            track_handle=item.get_track_handle(),
                        )
                    )

        if items_to_delete:
            timeline.delete_items(items_to_delete, auto_unlock=False)
        if item_insert_infos:
            resolve.insert_to_timeline(item_insert_infos, auto_unlock=False)

    @classmethod
    def _find_generated_textplus_in_range(cls, timeline: Timeline, frame_range: FrameRange):
        dst_track = timeline.find_track_by_name("video", GeneratedTrackName.TEXT)
        return list(timeline.iter_items_in_track(dst_track, lambda item: FrameRange.is_started_in_range(item.get_frame_range(), frame_range)))

    @classmethod
    def _normalize_keywords(cls, keywords: list[str]):
        return [keyword.strip() for keyword in keywords if keyword.strip() != ""]

    @classmethod
    def _get_or_add_effect_control_track(cls, timeline: Timeline):
        track_handle = timeline.get_or_add_track_by_name("video", GeneratedTrackName.EFFECT_CONTROL)
        timeline.set_track_enabled(track_handle, False)

        return track_handle

    @classmethod
    def _is_effect_control_clip(cls, item: TimelineItem):
        if item._item.GetFusionCompCount() == 0:
            return False

        comp = item.get_last_fusion_composition()
        tool = comp.Template

        if tool is None:
            return False

        return tool.ID == "Fuse.EffectControl"

    @classmethod
    def _reinsert_effect_control_clips(cls, timeline: Timeline, effect_control_items: list[TimelineItem], effect_control_media_pool_item: MediaPoolItem):
        resolve = davinci_resolve_module.get_resolve()
        all_keywords = [cls._get_keywords(item) for item in effect_control_items]
        insert_infos = [
            MediaPoolItemInsertInfo(
                media_pool_item=effect_control_media_pool_item,
                start_frame=item._item.GetStart(),
                end_frame=item._item.GetEnd(),
                track_handle=item.get_track_handle(),
            )
            for item in effect_control_items
        ]

        with timeline.rollback_playhead_on_exit():
            LoadingWindow.set_message(f"Deleting {len(effect_control_items)} clips...")
            timeline.delete_items(effect_control_items)
            LoadingWindow.set_message(f"Reinserting {len(insert_infos)} clips...")
            new_timeline_items = resolve.insert_to_timeline(insert_infos)

        for i, (item, keywords) in enumerate(zip(new_timeline_items, all_keywords)):
            if item is None:
                raise UserError(f"Failed to insert clips `{SmartEditBin.ClipName.EFFECT_CONTROL}` with info {insert_infos[i]}")

            cls._set_keywords(item, keywords)

    @classmethod
    def _get_keywords(cls, effect_control_item: TimelineItem):
        comp = effect_control_item.get_last_fusion_composition()
        tool = comp.Template

        keywords_text = tool.GetInput("Keywords")
        keywords = keywords_text.split(",")
        keywords = cls._normalize_keywords(keywords)

        return keywords

    @classmethod
    def _set_keywords(cls, effect_control_item: TimelineItem, keywords: list[str]):
        comp = effect_control_item.get_last_fusion_composition()
        tool = comp.Template

        keywords = cls._normalize_keywords(keywords)
        keywords_text = ",".join(keywords)

        tool.SetInput("Keywords", keywords_text)
