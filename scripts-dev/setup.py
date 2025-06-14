from subprocess import run
from common import scripts_directory, python_bin

if __name__ == "__main__":
    run([python_bin, "setupBackend.py"], cwd=scripts_directory)
    # Order actually matters
    # The frontend setup generates types which depends on the backend venv
    run([python_bin, "setupFrontend.py"], cwd=scripts_directory)
