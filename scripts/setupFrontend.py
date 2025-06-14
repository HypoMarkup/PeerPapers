from subprocess import run
from common import frontend_directory, scripts_directory

if __name__ == "__main__":
    run(["npm", "ci"], cwd=frontend_directory)
    run(["python", "generateFrontendTypes.py"], cwd=scripts_directory)
