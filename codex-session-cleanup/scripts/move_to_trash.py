#!/usr/bin/env python3
"""Atomically move verified Codex task directories into a reviewable Trash batch."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from pathlib import Path


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TrashMoveError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move verified Codex task directories into one macOS Trash batch."
    )
    parser.add_argument("--root", required=True, help="Canonical cleanup root")
    parser.add_argument(
        "--path", action="append", required=True, dest="paths", help="Exact candidate path"
    )
    return parser.parse_args()


def entity_directory(path: Path, label: str) -> os.stat_result:
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise TrashMoveError(f"{label} cannot be inspected: {path}: {exc}") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise TrashMoveError(f"{label} must be an entity directory: {path}")
    return info


def strict_descendant(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return path != root


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def path_entry_exists(path: Path) -> bool:
    return os.path.lexists(path)


def directory_size(path: Path) -> int | None:
    result = subprocess.run(
        ["du", "-sk", str(path)], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.split()[0]) * 1024
    except (IndexError, ValueError):
        return None


def find_worktree_markers(candidate: Path) -> list[str]:
    markers: list[str] = []

    def fail_walk(error: OSError) -> None:
        raise TrashMoveError(f"candidate tree cannot be fully inspected: {error}")

    for current, dirs, files in os.walk(
        candidate, followlinks=False, onerror=fail_walk
    ):
        current_path = Path(current)
        if ".git" in files:
            markers.append(str(current_path / ".git"))
        if ".git" in dirs:
            marker = current_path / ".git"
            try:
                mode = os.lstat(marker).st_mode
            except OSError:
                markers.append(str(marker))
            else:
                if not stat.S_ISDIR(mode):
                    markers.append(str(marker))
            dirs.remove(".git")
    return sorted(markers)


def validate_candidate(path_text: str, root: Path, trash_root: Path) -> dict[str, object]:
    input_path = Path(path_text)
    if not input_path.is_absolute():
        raise TrashMoveError(f"candidate path must be absolute: {path_text}")
    source_info = entity_directory(input_path, "candidate")
    source = input_path.resolve(strict=True)
    if input_path != source:
        raise TrashMoveError(f"candidate path must be canonical: {path_text}")
    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise TrashMoveError(f"candidate is outside cleanup root: {source}") from exc
    if not strict_descendant(source, root) or len(relative.parts) != 2:
        raise TrashMoveError(f"candidate is not exactly two levels below root: {source}")
    date_name, task_name = relative.parts
    if not DATE_RE.fullmatch(date_name) or not task_name:
        raise TrashMoveError(f"candidate path does not match YYYY-MM-DD/task: {source}")
    try:
        dt.date.fromisoformat(date_name)
    except ValueError as exc:
        raise TrashMoveError(f"candidate date layer is invalid: {source.parent}") from exc
    date_layer = source.parent
    entity_directory(date_layer, "candidate date layer")
    if path_entry_exists(root / ".codex-keep") or path_entry_exists(
        source / ".codex-keep"
    ):
        raise TrashMoveError(f"candidate is protected by .codex-keep: {source}")
    current_cwd = Path(os.path.realpath(os.getcwd()))
    if path_is_within(current_cwd, source):
        raise TrashMoveError(f"candidate is current working directory or its ancestor: {source}")
    markers = find_worktree_markers(source)
    if markers:
        raise TrashMoveError(f"candidate contains .git file/worktree markers: {markers}")
    if source_info.st_dev != os.lstat(trash_root).st_dev:
        raise TrashMoveError(
            f"candidate and Trash are on different filesystems; refusing copy/delete fallback: {source}"
        )
    return {
        "source": source,
        "date_name": date_name,
        "task_name": task_name,
        "device": source_info.st_dev,
        "inode": source_info.st_ino,
        "size_bytes": directory_size(source),
    }


def create_batch(trash_root: Path, now: dt.datetime | None = None) -> Path:
    timestamp = (now or dt.datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
    for _ in range(20):
        batch = trash_root / f"Codex-Session-Cleanup-{timestamp}-{secrets.token_hex(3)}"
        try:
            batch.mkdir(mode=0o700)
        except FileExistsError:
            continue
        return batch
    raise TrashMoveError("could not create a unique Trash batch directory")


def write_manifest(batch: Path, root: Path, items: list[dict[str, object]], complete: bool) -> Path:
    manifest = batch / "manifest.json"
    temporary = batch / ".manifest.json.tmp"
    payload = {
        "schema_version": 1,
        "created_at": dt.datetime.now().astimezone().isoformat(),
        "cleanup_root": str(root),
        "trash_batch": str(batch),
        "complete": complete,
        "items": items,
    }
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, manifest)
    return manifest


def move_candidates(root_input: Path, path_texts: list[str], trash_root_input: Path) -> dict[str, object]:
    if not root_input.is_absolute():
        raise TrashMoveError(f"cleanup root must be absolute: {root_input}")
    entity_directory(root_input, "cleanup root")
    root = root_input.resolve(strict=True)
    if root_input != root:
        raise TrashMoveError(f"cleanup root must be canonical: {root_input}")
    entity_directory(trash_root_input, "macOS Trash")
    trash_root = trash_root_input.resolve(strict=True)
    if len(set(path_texts)) != len(path_texts):
        raise TrashMoveError("duplicate candidate path")

    candidates = [validate_candidate(path, root, trash_root) for path in path_texts]
    canonical_sources = [str(item["source"]) for item in candidates]
    if len(set(canonical_sources)) != len(canonical_sources):
        raise TrashMoveError("duplicate canonical candidate path")
    batch = create_batch(trash_root)
    moved: list[dict[str, object]] = []
    failure: str | None = None

    for candidate in candidates:
        source = candidate["source"]
        assert isinstance(source, Path)
        try:
            current_info = entity_directory(source, "candidate before move")
            if (current_info.st_dev, current_info.st_ino) != (
                candidate["device"],
                candidate["inode"],
            ):
                raise TrashMoveError(f"candidate identity changed before move: {source}")
            if path_entry_exists(root / ".codex-keep") or path_entry_exists(
                source / ".codex-keep"
            ):
                raise TrashMoveError(f"candidate became protected before move: {source}")
            if find_worktree_markers(source):
                raise TrashMoveError(f"candidate gained a .git file/worktree marker: {source}")

            date_destination = batch / str(candidate["date_name"])
            date_destination.mkdir(mode=0o700, exist_ok=True)
            destination = date_destination / str(candidate["task_name"])
            if destination.exists() or destination.is_symlink():
                raise TrashMoveError(f"Trash destination already exists: {destination}")
            os.rename(source, destination)
            moved.append(
                {
                    "source": str(source),
                    "trash_path": str(destination),
                    "size_bytes": candidate["size_bytes"],
                }
            )
            if source.exists() or source.is_symlink():
                raise TrashMoveError(f"source still exists after move: {source}")
            entity_directory(destination, "Trash destination")
        except (OSError, TrashMoveError) as exc:
            failure = str(exc)
            break

    try:
        manifest = write_manifest(
            batch, root, moved, failure is None and len(moved) == len(candidates)
        )
    except OSError as exc:
        return {
            "ok": False,
            "trash_batch": str(batch),
            "manifest": None,
            "moved": moved,
            "unmoved": [str(item["source"]) for item in candidates[len(moved) :]],
            "error": f"moves completed but manifest could not be written: {exc}",
        }
    return {
        "ok": failure is None and len(moved) == len(candidates),
        "trash_batch": str(batch),
        "manifest": str(manifest),
        "moved": moved,
        "unmoved": [str(item["source"]) for item in candidates[len(moved) :]],
        "error": failure,
    }


def main() -> int:
    args = parse_args()
    try:
        result = move_candidates(Path(args.root), args.paths, Path.home() / ".Trash")
    except (OSError, TrashMoveError) as exc:
        result = {"ok": False, "error": str(exc), "moved": [], "unmoved": args.paths}
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
