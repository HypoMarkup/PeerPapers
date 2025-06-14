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
    scripts: Path = Path(__file__).parent.resolve()

    backend_shared = scripts.parent.resolve().joinpath("backend").joinpath("shared")

    frontend = scripts.parent.resolve().joinpath("frontend")

    frontend_generated = frontend.joinpath("src").joinpath("generated")

    # Delete directories if they exist
    if frontend_generated.is_dir():
        rmdir(frontend_generated)
    frontend_generated.mkdir()

    # Iterate through schemas
    for i in backend_shared.iterdir():
        # Ideally we should do checks for .json ending
        # TODO: Would be cool to preserve folder structure if we end up nesting schemas

        # $ pydantic2ts --module ./backend/api.py --output ./frontend/apiTypes.ts

        if i.is_file():
            # Generate TypeScript types
            run(
                [
                    "pydantic2ts",
                    "--module",
                    i,
                    "--output",
                    str(frontend_generated.joinpath(i.stem + ".d.ts")),
                    "--json2ts-cmd",
                    frontend.joinpath("node_modules")
                    .joinpath(".bin")
                    .joinpath("json2ts"),
                ]
            )

            # Generate TypeScript guards
            run(
                [
                    frontend.joinpath("node_modules")
                    .joinpath(".bin")
                    .joinpath("ts-auto-guard"),
                    "--export-all",
                    str(frontend_generated.joinpath(i.stem + ".d.ts")),
                ],
                cwd=frontend,
            )

            path = frontend_generated.joinpath(i.stem + ".guard.ts")
            # Add type to import of typescript guard

            # Read the file contents
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            # Replace all occurrences of 'import {' with 'import type {'
            new_content = content.replace("import {", "import type {")

            # Write the modified content back to the file
            with open(path, "w", encoding="utf-8") as file:
                file.write(new_content)
