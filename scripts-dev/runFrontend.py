from subprocess import run
from common import frontend_directory

if __name__ == "__main__":
    run(["npm", "run", "dev"], cwd=frontend_directory)
