from pathlib import Path
from os import name
from shutil import which
from sys import exit


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

is_windows = name == "nt"

venv_binaries = (
    backend_directory.joinpath("venv").joinpath("scripts")
    if is_windows
    else backend_directory.joinpath("venv").joinpath("bin")
)

#
# Dependencies
#
node_bin = which("node")

npm_bin = which("npm")

python_bin = which("python")

pip_bin = which("pip")

virtualenv_bin = which("virtualenv")

names = ["nodejs", "npm", "python", "pip", "virtualenv"]
deps = [node_bin, npm_bin, python_bin, pip_bin, virtualenv_bin]

# Checking

installed = list(map(lambda x: x is not None, deps))

if not all(installed):
    print("Missing dependencies")
    print(f"Install: {",".join([i[0] for i in zip(names, installed) if not i[1]])}")
    exit(1)

node_bin = node_bin

npm_bin = npm_bin

python_bin = python_bin

pip_bin = pip_bin

virtualenv_bin = virtualenv_bin
