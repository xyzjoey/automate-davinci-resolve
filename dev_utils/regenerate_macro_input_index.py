from argparse import ArgumentParser

from pathlib import Path
import re


def main():
    argparser = ArgumentParser()
    argparser.add_argument("input_path", type=Path)
    argparser.add_argument("output_path", type=Path)
    args = argparser.parse_args()

    macro_text = args.input_path.read_text()

    i = 1

    def replace_input_index(match):
        nonlocal i
        result = f"Input{i}"
        i += 1
        return result

    new_macro_text = re.sub(r"Input\d+", replace_input_index, macro_text)

    args.output_path.write_text(new_macro_text)


if __name__ == "__main__":
    main()
