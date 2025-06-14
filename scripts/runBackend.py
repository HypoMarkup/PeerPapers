from subprocess import run
from common import backend_directory, scripts_directory

if __name__ == "__main__":
    if not backend_directory.joinpath("venv").is_dir():
        run(["python", "setupBackend.py"], cwd=scripts_directory)

    run(
        [
            backend_directory.joinpath("venv").joinpath("bin").joinpath("fastapi"),
            "dev",
            "main.py",
        ],
        cwd=backend_directory,
    )
