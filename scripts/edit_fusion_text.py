from fusion_text_from_srt import FusionTextFromSrt
from utils.input import ChoiceInput, SpecialInputValue


def main():
    choice_input = ChoiceInput()
    choice_input.add_choice("i", FusionTextFromSrt(), "import .srt file and generate fusion text in a new timeline")
    # choice_input.add_choice("o", "export_srt", "export .srt file from fusion text in track")
    # choice_input.add_choice("s", "copy style", "apply fusion text style to track")
    choice_input.add_choice("q", SpecialInputValue.QUIT, "quit")

    print()
    print("=============")
    print("Start script!")
    print("=============")

    choice_input.print_help()

    while True:
        action = choice_input.ask_for_input("What do you want to do?")
        
        if action == SpecialInputValue.QUIT:
            break
        else:
            action.run()

    print("=============")
    print("End script")
    print("=============")


if __name__ == "__main__":
    main()
