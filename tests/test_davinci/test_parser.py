import inspect

from automate_davinci_resolve.davinci.parser import FusionSettingParser


class TestFusionSettingParser:
    def test_tokenize(self):
        text = """
        {
            Tools = ordered() {
                Template = TextPlus {
                    CtrlWZoom = false,
                    Inputs = {
                        ShadingGradient1 = Input {
                            Value = Gradient {
                                Colors = {
                                    [0] = { 0.777326, 0.32663, 0.89, 1 },
                                    [1] = { 0.490196078431373, 0.368627450980392, 0.886274509803922, 1 }
                                }
                            },
                        },
                    },
                    ViewInfo = OperatorInfo { Pos = { 220, 49.5 } },
                },
                CharacterLevelStyling1 = StyledTextCLS {
                    Inputs = {
                        Text = Input { Value = "女巫\\n有兩瓶\\"藥水\\"，晚上可使用一瓶\\n\'解藥\'：救助被狼人襲擊的人\\n毒藥：殺人", },
                        CharacterLevelStyling = Input {
                            Value = StyledText {
                                Array = {
                                    { 102, 3, 34, Value = 0.03 }
                                }
                            },
                        },
                    },
                }
            }
        }
        """

        # print(list(FusionSettingParser.tokenize(text)))
        assert list(FusionSettingParser.tokenize(text)) == [
            "{",
            "Tools",
            "=",
            "ordered()",
            "{",
            "Template",
            "=",
            "TextPlus",
            "{",
            "CtrlWZoom",
            "=",
            "false",
            ",",
            "Inputs",
            "=",
            "{",
            "ShadingGradient1",
            "=",
            "Input",
            "{",
            "Value",
            "=",
            "Gradient",
            "{",
            "Colors",
            "=",
            "{",
            "[",
            "0",
            "]",
            "=",
            "{",
            "0.777326",
            ",",
            "0.32663",
            ",",
            "0.89",
            ",",
            "1",
            "}",
            ",",
            "[",
            "1",
            "]",
            "=",
            "{",
            "0.490196078431373",
            ",",
            "0.368627450980392",
            ",",
            "0.886274509803922",
            ",",
            "1",
            "}",
            "}",
            "}",
            ",",
            "}",
            ",",
            "}",
            ",",
            "ViewInfo",
            "=",
            "OperatorInfo",
            "{",
            "Pos",
            "=",
            "{",
            "220",
            ",",
            "49.5",
            "}",
            "}",
            ",",
            "}",
            ",",
            "CharacterLevelStyling1",
            "=",
            "StyledTextCLS",
            "{",
            "Inputs",
            "=",
            "{",
            "Text",
            "=",
            "Input",
            "{",
            "Value",
            "=",
            '"女巫\\n有兩瓶\\"藥水\\"，晚上可使用一瓶\\n\'解藥\'：救助被狼人襲擊的人\\n毒藥：殺人"',
            ",",
            "}",
            ",",
            "CharacterLevelStyling",
            "=",
            "Input",
            "{",
            "Value",
            "=",
            "StyledText",
            "{",
            "Array",
            "=",
            "{",
            "{",
            "102",
            ",",
            "3",
            ",",
            "34",
            ",",
            "Value",
            "=",
            "0.03",
            "}",
            "}",
            "}",
            ",",
            "}",
            ",",
            "}",
            ",",
            "}",
            "}",
            "}",
        ]

    def test_parse(self):
        text = """
        {
            Tools = ordered() {
                Template = TextPlus {
                    CtrlWZoom = false,
                    Inputs = {
                        ShadingGradient1 = Input {
                            Value = Gradient {
                                Colors = {
                                    [0] = { 0.777326, 0.32663, 0.89, 1 },
                                    [1] = { 0.490196078431373, 0.368627450980392, 0.886274509803922, 1 }
                                }
                            },
                        },
                    },
                    ViewInfo = OperatorInfo { Pos = { 220, 49.5 } },
                },
                CharacterLevelStyling1 = StyledTextCLS {
                    Inputs = {
                        Text = Input { Value = "女巫\\n有兩瓶\\"藥水\\"，晚上可使用一瓶\\n\'解藥\'：救助被狼人襲擊的人\\n毒藥：殺人", },
                        CharacterLevelStyling = Input {
                            Value = StyledText {
                                Array = {
                                    { 102, 3, 34, Value = 0.03 }
                                }
                            },
                        },
                    },
                }
            }
        }
        """

        data = FusionSettingParser.parse(text)
        # print(data)

        assert data == {
            "Tools": {
                "__ctor": "ordered()",
                "Template": {
                    "__ctor": "TextPlus",
                    "CtrlWZoom": "false",
                    "Inputs": {
                        "ShadingGradient1": {
                            "__ctor": "Input",
                            "Value": {
                                "__ctor": "Gradient",
                                "Colors": {
                                    0: {1: "0.777326", 2: "0.32663", 3: "0.89", 4: "1"},
                                    1: {1: "0.490196078431373", 2: "0.368627450980392", 3: "0.886274509803922", 4: "1"},
                                },
                            },
                        }
                    },
                    "ViewInfo": {"__ctor": "OperatorInfo", "Pos": {1: "220", 2: "49.5"}},
                },
                "CharacterLevelStyling1": {
                    "__ctor": "StyledTextCLS",
                    "Inputs": {
                        "Text": {"__ctor": "Input", "Value": '"女巫\\n有兩瓶\\"藥水\\"，晚上可使用一瓶\\n\'解藥\'：救助被狼人襲擊的人\\n毒藥：殺人"'},
                        "CharacterLevelStyling": {
                            "__ctor": "Input",
                            "Value": {"__ctor": "StyledText", "Array": {1: {1: "102", 2: "3", 3: "34", "Value": "0.03"}}},
                        },
                    },
                },
            }
        }

    def test_compose(self):
        text = inspect.cleandoc(
            """
        {
            Tools = ordered() {
                Template = TextPlus {
                    CtrlWZoom = false,
                    Inputs = {
                        ShadingGradient1 = Input {
                            Value = Gradient {
                                Colors = {
                                    [0] = { 0.777326, 0.32663, 0.89, 1 },
                                    [1] = { 0.490196078431373, 0.368627450980392, 0.886274509803922, 1 }
                                }
                            },
                        },
                    },
                    ViewInfo = OperatorInfo { Pos = { 220, 49.5 } },
                },
                CharacterLevelStyling1 = StyledTextCLS {
                    Inputs = {
                        Text = Input { Value = "女巫\\n有兩瓶\\"藥水\\"，晚上可使用一瓶\\n\'解藥\'：救助被狼人襲擊的人\\n毒藥：殺人", },
                        CharacterLevelStyling = Input {
                            Value = StyledText {
                                Array = {
                                    { 102, 3, 34, Value = 0.03 }
                                }
                            },
                        },
                    },
                }
            }
        }
        """
        )

        data1 = FusionSettingParser.parse(text)
        composed_text = FusionSettingParser.compose(data1)
        data2 = FusionSettingParser.parse(composed_text)

        # print()
        # print(composed_text)

        assert data1 == data2
