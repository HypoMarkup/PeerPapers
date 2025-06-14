from pathlib import Path
from os import name
from shutil import which


def rmdir(directory: Path):
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


scripts_directory: Path = Path(__file__).parent.resolve()

frontend_directory = scripts_directory.parent.resolve().joinpath("frontend")

backend_directory = scripts_directory.parent.resolve().joinpath("backend")

is_windows = (name == "nt")

venv_binaries = backend_directory.joinpath("venv").joinpath("scripts") if is_windows else backend_directory.joinpath("venv").joinpath("bin")

npm_bin = which("npm")