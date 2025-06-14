from subprocess import run
from common import scripts_directory

if __name__ == "__main__":
    run(["python", "setupBackend"], cwd=scripts_directory)
    # Order actually matters
    # The frontend setup generates types which depends on the backend venv
    run(["python", "setupFrontend"], cwd=scripts_directory)
