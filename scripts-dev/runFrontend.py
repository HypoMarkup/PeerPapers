from subprocess import run
from common import frontend_directory,npm_bin

if __name__ == "__main__":
    run([npm_bin, "run", "dev"], cwd=frontend_directory)
