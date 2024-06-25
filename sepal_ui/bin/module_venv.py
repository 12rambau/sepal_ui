#!/usr/bin/python3

"""Script to add a testing kernel in the local environment.

This script should be run in a module folder. From there, it will create a  new venv in the "module_venv" folder.
This venv will be named after the module repository name. All libraries specified in the requirements.txt file will be installed.
Then the script will read the "module.yaml" file (if existing) and extract, the name of the module and the entry_point file (usually "ui.ipynb").
The venv will be added to the list of usable Jupyter kernel. It will be named: "test-<name_of_the_repo>" and displayed as "(test) <name of the module>".
The kernel should automatically be added to the entry_point file.
"""

import argparse
import json
import subprocess
from pathlib import Path
from shutil import rmtree

import yaml
from colorama import Fore, init

# init colors for all plateforms
init()

# init parser
parser = argparse.ArgumentParser(description=__doc__, usage="module_venv")
parser.add_argument("--venv_prefix", default="test", help="Prefix for the virtual environment name")


def main() -> None:
    """Launch the venv creation process."""
    # read arguments (there should be none)
    args = parser.parse_args()

    # welcome the user
    print(f"{Fore.YELLOW}venv creation interface v10{Fore.RESET}")

    # check that the local folder is a module folder
    ui_file = Path.cwd() / "ui.ipynb"
    if not ui_file.is_file():
        raise Exception(f"{Fore.RED}This is not a module folder.")

    # create a venv folder
    print('create the venv directory: "module-venv"')
    venv_dir = Path.home() / "module-venv"
    venv_dir.mkdir(exist_ok=True)

    # create a venv folder associated with the current repository
    print(f'create a venv directory for the current app: "{Path.cwd().name}"')
    current_dir_venv = venv_dir / Path.cwd().name

    # empty the folder from anything already in there
    # equivalement to flushing the existing venv (it's just faster than pip)
    if current_dir_venv.is_dir():
        rmtree(current_dir_venv)

    current_dir_venv.mkdir(exist_ok=True)

    # init the venv
    print("Initializing the venv, this process will take some minutes.")

    subprocess.run(["python3", "-m", "venv", str(current_dir_venv)], cwd=Path.cwd())

    # extract python and pip from thevenv
    pip = current_dir_venv / "bin" / "pip"
    python3 = current_dir_venv / "bin" / "python3"

    base_libs = ["wheel", "ipykernel", "numpy"]

    # if we are in sepal, install earthengine-api OF fork

    if "sepal-user" in str(Path.cwd()):
        earthengine_api = "git+https://github.com/openforis/earthengine-api.git@v0.1.384#egg=earthengine-api&subdirectory=python"
        base_libs.append(earthengine_api)

    subprocess.run([str(pip), "install", "--upgrade", "pip"], cwd=Path.cwd())

    for lib in base_libs:
        subprocess.run([str(pip), "install", "--no-cache-dir", lib], cwd=Path.cwd())

    # Default installation of GDAL
    # If we are installing it as venv (usually in github actions) we need to install gdal as binary
    gdal_version = "3.8.3"

    # We assume we are in a github action runner if the path contains "home/runner/"
    if "home/runner/" not in str(Path.cwd()):
        subprocess.run(
            [str(pip), "install", "--no-cache-dir", f"GDAL=={gdal_version}"], cwd=Path.cwd()
        )
    else:
        subprocess.run(
            [
                str(pip),
                "install",
                "--no-cache-dir",
                "--find-links=https://girder.github.io/large_image_wheels",
                f"GDAL=={gdal_version}",
            ],
            cwd=Path.cwd(),
        )

    # install all the requirements
    req = Path.cwd() / "requirements.txt"
    subprocess.run(
        [
            str(pip),
            "install",
            "--no-cache-dir",
            "-r",
            str(req),
        ],
        cwd=Path.cwd(),
    )

    # search for the module.yaml file
    # it embeds name and entry point
    module_config = Path().cwd() / "module.yaml"

    if module_config.is_file():
        with module_config.open() as f:
            data = yaml.safe_load(f)
        entry_point = Path.cwd() / data["entry_point"]
        name = data["name"]

    else:
        entry_point = Path.cwd() / "ui.ipynb"
        name = Path.cwd().name

    # create the kernel from venv
    name = f"{args.venv_prefix}-{Path.cwd().name}"
    display_name = f"({args.venv_prefix}) {name}"
    subprocess.run(
        [
            str(python3),
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            name,
            "--display-name",
            display_name,
        ],
        cwd=Path.cwd(),
    )

    # change the kernel of the entrypoint to use this one instead
    with entry_point.open() as f:
        data = json.load(f)

    data["metadata"]["kernelspec"]["display_name"] = display_name
    data["metadata"]["kernelspec"]["name"] = name

    entry_point.write_text(json.dumps(data, indent=1))

    # display last message to the end user
    print(
        f'{Fore.GREEN}The test venv have been created, it can be found in the kernel list as "{display_name}". It has automatically been added to the entry point of the application: {entry_point.name}.{Fore.RESET}'
    )

    return


if __name__ == "__main__":
    main()
