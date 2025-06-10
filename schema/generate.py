from pathlib import Path
from subprocess import run


def rmdir(directory: Path):
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


if __name__ == "__main__":
    schema: Path = Path(__file__).parent.resolve()

    # Make sure quick type is installed
    # Assume if node_modules folder exists then quicktype is installed
    if not schema.joinpath("node_modules").is_dir():
        run(["npm", "ci"], cwd=schema)

    common: Path = schema.joinpath("common")

    backend_generated = (
        schema.parent.resolve().joinpath("backend").joinpath("generated")
    )

    frontend_generated = (
        schema.parent.resolve()
        .joinpath("frontend")
        .joinpath("src")
        .joinpath("generated")
    )

    # Delete directories if they exist
    if backend_generated.is_dir():
        rmdir(backend_generated)
    backend_generated.mkdir()

    if frontend_generated.is_dir():
        rmdir(frontend_generated)
    frontend_generated.mkdir()

    # Iterate through schemas
    for i in common.iterdir():
        # Ideally we should do checks for .json ending
        # TODO: Would be cool to preserve folder structure if we end up nesting schemas

        if i.is_file():
            # Python
            run(
                [
                    schema.joinpath("node_modules")
                    .joinpath(".bin")
                    .joinpath("quicktype"),
                    "--src-lang",
                    "schema",
                    i,
                    "--just-types",
                    "--pydantic-base-model",
                    "--out",
                    backend_generated.joinpath(i.stem + ".py"),
                ]
            )
            # TypeScript
            run(
                [
                    schema.joinpath("node_modules")
                    .joinpath(".bin")
                    .joinpath("quicktype"),
                    "--src-lang",
                    "schema",
                    i,
                    "--prefer-unions",
                    "--out",
                    frontend_generated.joinpath(i.stem + ".ts"),
                ]
            )
