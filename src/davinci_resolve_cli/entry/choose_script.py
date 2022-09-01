import asyncio

import apply_textplus_style_to_track
import textplus_from_srt
import monitor_and_apply_textplus_track_style
import export_srt_from_textplus
from davinci_resolve_cli.inputs.choice_input import ChoiceInput, ChoiceValue, Choice


async def main():
    # TODO use subparser
    choices = [
        Choice("a", apply_textplus_style_to_track.Process(), "apply Text+ style from the current timeline clip to track(s)"),
        Choice("e", export_srt_from_textplus.Process(), "export all Text+ content to a subtitle file"),
        Choice("g", textplus_from_srt.Process(), "generate Text+ in a new timeline from a .srt subtitle file"),
        Choice("m", monitor_and_apply_textplus_track_style.Process(), "monitor and apply Text+ track style continuously"),
        Choice("q", ChoiceValue.QUIT, "quit"),
        Choice("?", ChoiceValue.HELP, "print help"),
    ]

    print()
    print("=============")
    print("Start script!")
    print("=============")

    while True:
        choice_input = ChoiceInput.ask_for_input("What do you want to do?", choices)
        
        if choice_input.get_value() == ChoiceValue.HELP:
            choice_input.print_help()
        elif choice_input.get_value() == ChoiceValue.QUIT:
            break
        else:
            process = choice_input.get_value()
            if asyncio.iscoroutinefunction(process.run):
                await process.run()
            else:
                process.run()

    print("=============")
    print("End script")
    print("=============")


if __name__ == "__main__":
    asyncio.run(main())
