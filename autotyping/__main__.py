import argparse
import os
import sys

from autotyping.autotyping import AutotypeCommand

from libcst.codemod import (
    CodemodContext,
    gather_files,
    parallel_exec_transform_with_prettyprint,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    AutotypeCommand.add_args(parser)
    parser.add_argument("path", nargs="+")
    args = parser.parse_args()

    kwargs = vars(args)
    del args

    path = kwargs.pop("path")

    bases = list(map(os.path.abspath, path))
    root = os.path.commonpath(bases)
    root = os.path.dirname(root) if os.path.isfile(root) else root

    # Based on:
    # https://github.com/Instagram/LibCST/blob/36e791ebe5f008af91a2ccc6be4900e69fad190d/libcst/tool.py#L593
    files = gather_files(bases, include_stubs=True)
    try:
        result = parallel_exec_transform_with_prettyprint(
            AutotypeCommand(CodemodContext(), **kwargs), files, repo_root=root
        )
    except KeyboardInterrupt:
        print("Interrupted!", file=sys.stderr)
        return 2

    print(
        f"Finished codemodding {result.successes + result.skips + result.failures} files!",
        file=sys.stderr,
    )
    print(f" - Transformed {result.successes} files successfully.", file=sys.stderr)
    print(f" - Skipped {result.skips} files.", file=sys.stderr)
    print(f" - Failed to codemod {result.failures} files.", file=sys.stderr)
    print(f" - {result.warnings} warnings were generated.", file=sys.stderr)
    return 1 if result.failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
