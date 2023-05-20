class FusionSettingParser:
    @classmethod
    def _get_quote_end(cls, text):
        if len(text) == 0 or text[0] != '"':
            return 0

        i = 1

        while i < len(text):
            if text[i] == "\\":
                i += 1
            elif text[i] == '"':
                return i + 1

            i += 1

        return i

    @classmethod
    def tokenize(cls, text: str):
        keywords = "{}=,[]"

        i = 0

        while i < len(text):
            j = i + 1

            if text[i].isspace():
                pass
            elif text[i] in keywords:
                yield text[i]
            elif text[i] == '"':
                j = i + cls._get_quote_end(text[i:])
                yield text[i:j]
            else:
                while not (text[j].isspace() or text[j] in keywords) and j < len(text):
                    j += 1
                yield text[i:j]

            i = j

    @classmethod
    def _parse_value(cls, tokens):
        if tokens[0] == "{" or (1 < len(tokens) and tokens[1] == "{"):
            return cls._parse_table(tokens)
        else:
            return tokens[0], 1

    @classmethod
    def _parse_table(cls, tokens):
        data = {}

        i = 0

        if tokens[i] == "{":
            i += 1
        elif tokens[i + 1] == "{":
            data["__ctor"] = tokens[i]
            i += 2
        else:
            pass  # raise

        while i < len(tokens):
            j = i + 1

            if tokens[i] == ",":
                pass
            elif tokens[i] == "}":
                return data, i + 1
            elif i + 1 < len(tokens) and tokens[i + 1] == "=":
                key = tokens[i]
                value, end = cls._parse_value(tokens[i + 2 :])
                data[key] = value
                j = i + 2 + end
            elif i + 3 < len(tokens) and tokens[i] == "[" and tokens[i + 3] == "=":
                key = float(tokens[i + 1])
                value, end = cls._parse_value(tokens[i + 4 :])
                data[key] = value
                j = i + 4 + end
            else:
                key = len(data) + 1
                value, end = cls._parse_value(tokens[i:])
                data[key] = value
                j = i + end

            i = j

        return data, len(tokens)

    @classmethod
    def parse(cls, text: str):
        table, _ = cls._parse_table(list(cls.tokenize(text)))
        return table

    @classmethod
    def _compose_value(cls, data, depth: int):
        if type(data) is dict:
            return cls._compose_table(data, depth)
        else:
            return data

    @classmethod
    def _compose_table(cls, data: dict, depth: int):
        text = ""

        wrap_line = any(type(v) is dict for v in data.values())
        indent_item = "\t" * (depth + 1) if wrap_line else ""
        indent = "\t" * depth if wrap_line else ""
        space = "\n" if wrap_line else " "

        if "__ctor" in data:
            text += data["__ctor"] + " {" + space
        else:
            text += "{" + space

        for i, (k, v) in enumerate(data.items()):
            if k == "__ctor":
                pass
            elif type(k) is int:
                if k == i + 1:
                    text += f"{indent_item}{cls._compose_value(v, depth + 1)},{space}"
                else:
                    text += f"{indent_item}{k} = {cls._compose_value(v, depth + 1)},{space}"
            elif type(k) is float:
                text += f"{indent_item}[{k:g}] = {cls._compose_value(v, depth + 1)},{space}"
            else:
                text += f"{indent_item}{k} = {cls._compose_value(v, depth + 1)},{space}"

        text += indent + "}"

        return text

    @classmethod
    def compose(cls, data: dict):
        return cls._compose_table(data, depth=0)


# # reference: https://github.com/pyparsing/pyparsing/blob/master/examples/jsonParser.py
# class FusionSettingParser:
#     def __init__(self):
#         LBRACE, RBRACE, EQUAL = map(pp.Suppress, "{}=")
#         TRUE = self.make_keyword("true", True)
#         FALSE = self.make_keyword("false", False)

#         fusion_id = pp.Word(pp.alphas + "[", pp.alphanums + "_]")
#         fusion_type = pp.Word(pp.alphas, pp.alphanums + "_()")
#         fusion_number = ppc.number()
#         fusion_string = pp.QuotedString('"', multiline=True)

#         fusion_array_value = pp.Forward()
#         fusion_map_value = pp.Forward()
#         fusion_map = pp.Forward()

#         fusion_array_items = pp.delimitedList(pp.Group(fusion_array_value, aslist=True), allow_trailing_delim=True)
#         fusion_map_items = pp.delimitedList(pp.Group(fusion_id + EQUAL + fusion_map_value, aslist=True), allow_trailing_delim=True)

#         fusion_array = pp.Group(LBRACE + pp.Optional(fusion_array_items) + RBRACE, aslist=True)
#         fusion_map << pp.Optional(fusion_type) + pp.Dict(
#             LBRACE + pp.Optional(fusion_map_items) + RBRACE,
#             asdict=True,
#         )

#         fusion_array_value << (TRUE | FALSE | fusion_number | fusion_string | fusion_array | (fusion_id + EQUAL + fusion_array_value))
#         fusion_map_value << (TRUE | FALSE | fusion_number | fusion_string | fusion_array | fusion_map)

#         self.parser = fusion_map

#     def make_keyword(self, keyword_string, keyword_value):
#         return pp.Keyword(keyword_string).setParseAction(pp.replaceWith(keyword_value))

#     def parse(self, text):
#         return self.parser.parseString(text)
