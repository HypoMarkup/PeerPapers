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

dep_names = ["node", "npm", "python3", "pip3", "virtualenv"]
where = list(map(lambda x: which(x), dep_names))
is_installed = list(map(lambda x: x is not None, where))
if not all(is_installed):
    print("Missing dependencies")
    print(
        f"Install: {','.join([i[0] for i in zip(dep_names, is_installed) if not i[1]])}"
    )
    exit(1)

deps = {a: b for a, b in zip(dep_names, where) if b is not None}

node_bin = deps["node"]

npm_bin = deps["npm"]

python_bin = deps["python3"]

pip_bin = deps["pip3"]

virtualenv_bin = deps["virtualenv"]
