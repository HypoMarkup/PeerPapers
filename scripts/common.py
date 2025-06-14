from pathlib import Path


def rmdir(directory: Path):
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


scripts_directory: Path = Path(__file__).parent.resolve()

frontend_directory = scripts_directory.parent.resolve().joinpath("frontend")

backend_directory = scripts_directory.parent.resolve().joinpath("backend")
