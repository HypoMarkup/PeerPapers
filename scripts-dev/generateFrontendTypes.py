from subprocess import run
from common import (
    rmdir,
    frontend_directory,
    backend_directory,
    venv_binaries,
    is_windows,
)

if __name__ == "__main__":
    frontend_generated = frontend_directory.joinpath("src").joinpath("generated")

    backend_shared = backend_directory.joinpath("shared")

    # Delete directories if they exist
    if frontend_generated.is_dir():
        rmdir(frontend_generated)
    frontend_generated.mkdir()

    # Iterate through schemas
    for i in backend_shared.iterdir():
        # $ pydantic2ts --module ./backend/api.py --output ./frontend/apiTypes.ts
        if i.is_file():
            # Generate TypeScript types
            run(
                [
                    venv_binaries.joinpath("pydantic2ts"),
                    "--module",
                    str(i),
                    "--output",
                    str(frontend_generated.joinpath(i.stem + ".d.ts")),
                    "--json2ts-cmd",
                    frontend_directory.joinpath("node_modules")
                    .joinpath(".bin")
                    .joinpath("json2ts"),
                ]
            )

            # Generate TypeScript guards
            run(
                [
                    frontend_directory.joinpath("node_modules")
                    .joinpath(".bin")
                    .joinpath("ts-auto-guard" + (".cmd" if is_windows else "")),
                    "--export-all",
                    str(frontend_generated.joinpath(i.stem + ".d.ts")),
                ],
                cwd=frontend_directory,
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
