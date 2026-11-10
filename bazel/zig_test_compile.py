"""Compile a pinned Zig test binary in one bounded, reproducible Bazel action."""

import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

from bazel.zig_toolchain_extract import extract_archive


SOURCE_SHA256 = "97b67a17a42d5d514d56b96cc26b035a582a25a5c752e150ddb8f5f60e1cf127"
SOURCE_BYTES = 3864
MAX_TEST_BINARY_BYTES = 32 * 1024 * 1024


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("expected <zig-archive> <source.zig> <output-binary>")
    archive, source, output = (Path(argument) for argument in sys.argv[1:])
    if not archive.is_file() or not source.is_file():
        raise SystemExit("declared Zig compile inputs are missing")
    if not output.is_absolute():
        output = Path.cwd() / output
    if not output.parent.is_dir():
        raise SystemExit("declared Zig output directory is missing")

    temporary_root = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="zig-test-compile-", dir=temporary_root) as temporary:
        scratch = Path(temporary)
        toolchain = scratch / "toolchain"
        extract_archive(archive, toolchain)
        source_copy = scratch / "src" / "shlex.zig"
        source_copy.parent.mkdir()
        with source.open("rb") as stream:
            source_bytes = stream.read(SOURCE_BYTES + 1)
        if len(source_bytes) != SOURCE_BYTES:
            raise SystemExit("shlex source size does not match the pinned module")
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        if source_digest != SOURCE_SHA256:
            raise SystemExit("shlex source SHA-256 does not match the pinned module")
        source_copy.write_bytes(source_bytes)

        zig = toolchain / "zig"
        if not zig.is_file() or not os.access(zig, os.X_OK):
            raise SystemExit("extracted Zig compiler is missing or not executable")
        environment = os.environ.copy()
        environment["ZIG_LOCAL_CACHE_DIR"] = str(scratch / "local-cache")
        environment["ZIG_GLOBAL_CACHE_DIR"] = str(scratch / "global-cache")
        result = subprocess.run(
            [str(zig), "test", "--test-no-exec", "-fstrip", "-target", "x86_64-linux-musl",
             "-mcpu=baseline", source_copy.name, "-femit-bin=" + str(output)],
            cwd=source_copy.parent,
            env=environment,
            check=False,
        )
        if result.returncode:
            raise SystemExit(result.returncode)

    if not output.is_file() or not 0 < output.stat().st_size <= MAX_TEST_BINARY_BYTES:
        raise SystemExit("Zig test compilation produced no binary or exceeded its output bound")
    output.chmod(output.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


if __name__ == "__main__":
    main()
