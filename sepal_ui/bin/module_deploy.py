#!/usr/bin/python3

"""
script to update the requirements file with the currently used libs

The script should be launched from a module directory.
It will parse all the files and extract the differnet librairies used in the module. They will be added to the requirements.txt
file using the versions used in the current local installation.
Some troubleshouting are handled by the script:
-  the earthengine-api will be forced to use the openforis fork to be compatible with SEPAL
-  pyproj and pygdal version will be forced to the version set in SEPAl as well
-  sepal-ui version will be bound to the one available when calling the script
Once the file have been created, please check it manually and make sure that there are no visible issues. PLease report any incompatibility to the developer
so taht they can be added to the troubleshoot function.
"""

from pathlib import Path
import subprocess
import argparse

from colorama import init, Fore, Style
import sepal_ui

# init colors for all plateforms
init()

# init parser
parser = argparse.ArgumentParser(description=__doc__, usage="module_deploy")


def write_reqs(file):
    """
    write the requirements in the requirements file

    Args:
        file (pathlib.Path): the requirements file
    """

    with file.open("a") as f:
        f.write("\n")
        f.write("\n# custom libs")
        f.write("\n")

    # ################## not working for no reason #############################
    # add the custom libs
    # command = ["pipreqs", '--print', str(Path.cwd()), '>>', str(req_file)]
    # res = subprocess.run(command, cwd=Path.cwd())
    # ##########################################################################

    # until I understand use a proxy tmp file
    tmp_file = Path.cwd() / "req_tmp.txt"
    subprocess.run(
        ["pipreqs", "--savepath", str(tmp_file), str(Path.cwd())], cwd=Path.cwd()
    )

    # add the libs in the final file
    with file.open("a") as dst:
        dst.write(tmp_file.read_text())

    # remove the tmp file
    tmp_file.unlink()

    return


def clean_dulpicate(file):
    """
    remove the requirements that are already part of the default installation

    Args:
        file (pathlib.Path): the requirements file
    """

    # already available libs
    libs = ["wheel", "Cython", "pybind11", "GDAL", "pyproj", "sepal_ui"]

    text = file.read_text().split("\n")

    # search for the custom line index
    idx = text.index("# custom libs")

    final_text = text[:idx]
    for line in text[idx:]:
        if any(lib in line for lib in libs):
            lib = next(lb for lb in libs if lb in line)
            print(
                f"Removing {Style.BRIGHT}{lib}{Style.NORMAL} from reqs, duplicated from default."
            )
            continue
        final_text.append(line)

    file.write_text("\n".join(final_text))

    return


def clean_troubleshouting(file):
    """
    the pipreqs is creating the file based on the import statements in .py files
    some libs doesn't have the same name as the pip command we are replacing/deleting the known one

    Args:
        file (pathlib.Path): the requirements file
    """

    text = file.read_text().split("\n")

    # search for the custom line index
    idx = text.index("# custom libs")

    final_text = text[:idx]
    for line in text[idx:]:

        # ee is imported as ee but the real name of the lib is earthengine-api
        # gdal and osgeo are part of pygdal
        # we use a specific version of earthengine in SEPAl, let's stick to it
        if "ee" in line:
            print(
                f"Removing {Style.BRIGHT}ee{Style.NORMAL} from reqs, included in sepal_ui."
            )
            continue
        elif any(lib in line for lib in ["osgeo", "gdal"]):
            print(
                f"Removing {Style.BRIGHT}'osgeo & gdal'{Style.NORMAL} from reqs, included in GDAL."
            )
            continue
        elif "earthengine_api" in line:
            print(
                f"Removing {Style.BRIGHT}earthengine_api{Style.NORMAL} from reqs, included in sepal_ui."
            )
            continue

        # if I'm here nothing needed to be removed
        final_text.append(line)

    file.write_text("\n".join(final_text))

    return


def freeze_sepal_ui(file):
    """
    set the sepal version to the currently used sepal-ui version

    Args:
        file (pathlib.Path): the requirements file
    """

    text = file.read_text().split("\n")

    # search for the sepal_ui line
    idx, _ = next(
        (i, l) for i, l in enumerate(text) if "#" not in l and "sepal_ui" in l
    )

    text[idx] = f"sepal_ui=={sepal_ui.__version__}"

    file.write_text("\n".join(text))

    print(
        f"sepal_ui version have been freezed to  {Style.BRIGHT}{sepal_ui.__version__}{Style.NORMAL}"
    )

    return


def clean_custom(file):
    """
    remove the previous custom installation and requirements
    to start the process from a blank page

    Args:
        file (pathlib.Path): the requirements file
    """

    text = file.read_text().split("\n")

    # search for the custom line index
    try:
        idx = text.index("# custom libs")

        # remove everything after it
        file.write_text("\n".join(text[: idx - 1]))

        print("the previously set custom requirements have been cleaned from the file")

    except ValueError:
        pass

    return


def main():

    # parse agruments
    parser.parse_args()

    # welcome the user
    print(f"{Fore.YELLOW}sepal-ui module deployment tool{Fore.RESET}")

    print("Export the env configuration of your module...")

    # check that the local folder is a module folder
    ui_file = Path.cwd() / "ui.ipynb"
    if not ui_file.is_file():
        raise Exception(f"{Fore.RED}This is not a module folder.")

    # add the requirements to the requirements.txt file
    req_file = Path.cwd() / "requirements.txt"

    # clean the already existing custom installation
    # if it was done manually nothing will be removed
    clean_custom(req_file)

    # write the new requirements
    write_reqs(req_file)

    # clean the requirement file from known troubleshoutings
    clean_dulpicate(req_file)
    clean_troubleshouting(req_file)

    # set the sepal version
    freeze_sepal_ui(req_file)

    # exit message
    print(f'{Fore.GREEN}The "requirements.txt" file have been updated.{Fore.RESET}')
    print(
        f"{Fore.YELLOW}The tool does not cover every possible configuration so don't forget to check the final file before pushing to release.{Fore.RESET}"
    )


if __name__ == "__main__":
    main()