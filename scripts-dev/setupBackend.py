from subprocess import run
from common import backend_directory

if __name__ == "__main__":
    if backend_directory.joinpath("venv").is_dir():
        print("venv found")
    else:
        print("Creating venv")
        run(["virtualenv", "venv"], cwd=backend_directory)

    print("Activating venv")
    print("Installing dependencies")
    run(
        [
            backend_directory.joinpath("venv").joinpath("bin").joinpath("pip"),
            "install",
            "-r",
            "requirements.txt",
        ],
        cwd=backend_directory,
    )
