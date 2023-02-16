from pydantic import BaseModel, FilePath
import srt


class _FilePath(BaseModel):
    file_path: FilePath


class SubtitleFileInput:
    def __init__(self, file_path: FilePath):
        self.file_path = file_path
        self.parsed: list[srt.Subtitle] = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        # TODO use Validator on pydantic v2 available
        # https://github.com/pydantic/pydantic/blob/main/docs/blog/pydantic-v2.md#validation-without-a-model-thumbsup
        file_path = _FilePath(file_path=v).file_path

        try:
            # log.info(f"Parsing subtitles from '{v.get()}'...")

            with file_path.open(encoding="utf-8") as f:
                subtitles = list(srt.parse(f.read()))

                # log.info(f"Parsed {len(subtitles)} subtitles")

                result_data = cls(file_path)
                result_data.parsed = subtitles

                return result_data

        except Exception as e:
            raise ValueError(f"Failed to parse subtitle file: {e}")
