import apply_current_fusion_text_style_to_track
import fusion_text_from_srt
from utils.input import ChoiceInput, SpecialInputValue


def main():
    choice_input = ChoiceInput()
    choice_input.add_choice("i", fusion_text_from_srt.Process(), "import .srt file and generate fusion text in a new timeline")
    # choice_input.add_choice("o", ..., "export .srt file from fusion text in track")
    choice_input.add_choice("c", apply_current_fusion_text_style_to_track.Process(), "apply fusion text style from current clip to track")
    # choice_input.add_choice("m", ..., "apply fusion text style from media pool to track")
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
