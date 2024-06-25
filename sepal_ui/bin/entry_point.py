#!/usr/bin/python3

"""Script to rename the kernel of a notebook to a specific name."""

import argparse
import json
from pathlib import Path

from colorama import Fore, init

init()

# init parser
parser = argparse.ArgumentParser(description=__doc__, usage="entry_point")

parser.add_argument("file", help="UI file path")

# Add a optional argument
parser.add_argument("-t", "--test", help="Either test or not (production)", action="store_true")


def main() -> None:
    """Launch the venv creation process."""
    # read arguments (there should be none)
    args = parser.parse_args()

    ui_file = args.file
    test = args.test

    # welcome the user
    print(f"{Fore.YELLOW}UI renaming process{Fore.RESET}")

    # check that the local folder is a module folder
    ui_file = Path.cwd() / ui_file
    if not ui_file.is_file():
        raise Exception(f"{Fore.RED}This is not a module folder.")

    entry_point = Path.cwd() / ui_file

    # create the kernel from venv
    prefix_name = "test-" if test else "venv-"
    prefix_display = "(test) test-" if test else " (venv) "

    name = f"{prefix_name}{Path.cwd().name}"
    display_name = f"{prefix_display}{Path.cwd().name}"

    # change the kernel of the entrypoint to use this one instead
    with entry_point.open() as f:
        data = json.load(f)

    data["metadata"]["kernelspec"]["display_name"] = display_name
    data["metadata"]["kernelspec"]["name"] = name

    entry_point.write_text(json.dumps(data, indent=1))

    # display last message to the end user
    print(
        f'{Fore.GREEN}The python kernel of {args.file} has been updated"{display_name}".{Fore.RESET}'
    )

    return


if __name__ == "__main__":
    main()
