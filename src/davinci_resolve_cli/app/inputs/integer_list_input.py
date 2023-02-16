from collections.abc import Iterable


class IntegerListInput:
    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            try:
                return [int(v)]
            except:
                try:
                    return [int(number) for number in eval(v)]
                except Exception as e:
                    raise Exception(f"'{v}' is not a valid integer or list of integer ({str(e)})")
        
        if isinstance(v, Iterable):
            try:
                return [int(number) for number in v]
            except Exception as e:
                raise Exception(f"'{v}' is not a valid integer or list of integer ({str(e)})")

        try:
            return [int(v)]
        except Exception as e:
            raise Exception(f"'{v}' is not a valid integer or list of integer ({str(e)})")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate
