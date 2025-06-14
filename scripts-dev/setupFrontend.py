from subprocess import run
from common import frontend_directory, scripts_directory, npm_bin, python_bin

if __name__ == "__main__":
    run([npm_bin, "ci"], cwd=frontend_directory)
    run([python_bin, "generateFrontendTypes.py"], cwd=scripts_directory)
