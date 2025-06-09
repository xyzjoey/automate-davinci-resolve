class MediaPoolItemType:
    AUDIO = "Audio"
    COMPOUND = "Compound"
    FUSION_CLIP = "Fusion"
    FUSION_COMPOSITION = "Fusion Composition"  # cannot edit keywords
    FUSION_GENERATOR = "Fusion Generator"  # cannot edit keywords
    FUSION_TITLE = "Fusion Title"  # cannot edit keywords
    GENERATOR = "Generator"  # cannot edit keywords
    VIDEO = "Video"
    VIDEO_AUDIO = "Video + Audio"

    @classmethod
    def support_keyword(cls, item_type: str):
        return item_type not in [
            MediaPoolItemType.FUSION_COMPOSITION,
            MediaPoolItemType.FUSION_GENERATOR,
            MediaPoolItemType.FUSION_TITLE,
            MediaPoolItemType.GENERATOR,
        ]

    @classmethod
    def support_extending_duration(cls, item_type: str):
        return item_type in [
            MediaPoolItemType.FUSION_COMPOSITION,
            MediaPoolItemType.FUSION_GENERATOR,
            MediaPoolItemType.FUSION_TITLE,
            MediaPoolItemType.GENERATOR,
        ]
