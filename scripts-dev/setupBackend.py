from subprocess import run
from common import backend_directory, venv_binaries, virtualenv_bin

if __name__ == "__main__":
    if backend_directory.joinpath("venv").is_dir():
        print("venv found")
    else:
        print("Creating venv")
        run([virtualenv_bin, "venv"], cwd=backend_directory)

    print("Activating venv")
    print("Installing dependencies")
    run(
        [
            venv_binaries.joinpath("pip"),
            "install",
            "-r",
            "requirements.txt",
        ],
        cwd=backend_directory,
    )
