"""Safely extract the pinned Zig archive into disposable action scratch."""

import hashlib
from pathlib import Path, PurePosixPath
import shutil
import tarfile


ARCHIVE_SHA256 = "473ec26806133cf4d1918caf1a410f8403a13d979726a9045b421b685031a982"
ARCHIVE_MAX_BYTES = 50 * 1024 * 1024
MEMBER_COUNT_MAX = 16_000
UNPACKED_BYTES_MAX = 350 * 1024 * 1024
ARCHIVE_PREFIX = "zig-linux-x86_64-0.14.0"


def extract_archive(archive: Path, output: Path) -> None:
    if archive.stat().st_size > ARCHIVE_MAX_BYTES:
        raise SystemExit("Zig archive exceeds the declared size limit")

    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Zig archive SHA-256 does not match the pinned toolchain")

    with tarfile.open(archive, mode="r:xz") as tar:
        members = tar.getmembers()
        total_size = sum(member.size for member in members if member.isfile())
        if len(members) > MEMBER_COUNT_MAX or total_size > UNPACKED_BYTES_MAX:
            raise SystemExit("Zig archive exceeds its member or expanded-size limit")

        normalized = []
        for member in members:
            relative = PurePosixPath(member.name)
            if (relative.is_absolute() or not relative.parts
                    or relative.parts[0] != ARCHIVE_PREFIX
                    or any(part in {"", ".", ".."} for part in relative.parts)
                    or not (member.isdir() or member.isfile())):
                raise SystemExit("Zig archive contains an unsafe or unsupported member")
            stripped = Path(*relative.parts[1:])
            if not stripped.parts:
                continue
            normalized.append((member, stripped))

        if output.exists():
            if not output.is_dir() or any(output.iterdir()):
                raise SystemExit("Bazel toolchain output directory is not empty")
        else:
            output.mkdir(parents=True, exist_ok=False)
        required = {"zig", "lib/std/std.zig"}
        found = set()
        for member, relative in normalized:
            target = output / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is None:
                raise SystemExit("Zig archive file could not be read")
            with source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination)
            target.chmod(0o755 if member.mode & 0o111 else 0o644)
            if relative.as_posix() in required:
                found.add(relative.as_posix())
        if found != required:
            raise SystemExit("Zig archive lacks the compiler or standard library")
