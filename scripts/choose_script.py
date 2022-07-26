import apply_textplus_style_to_track
import textplus_from_srt
from utils.input import ChoiceInput, SpecialInputValue


def main():
    choice_input = ChoiceInput()
    choice_input.add_choice("a", apply_textplus_style_to_track.Process(), "apply Text+ style from the current timeline clip to track(s)")
    choice_input.add_choice("g", textplus_from_srt.Process(), "generate Text+ in a new timeline from a .srt subtitle file")
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
