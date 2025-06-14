from subprocess import run
from common import scripts_directory

if __name__ == "__main__":
    run(["python", "setupBackend.py"], cwd=scripts_directory)
    # Order actually matters
    # The frontend setup generates types which depends on the backend venv
    run(["python", "setupFrontend.py"], cwd=scripts_directory)
