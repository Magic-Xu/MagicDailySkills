#!/usr/bin/env python3
"""Read-only inventory for local Codex projectless task directories."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote


REQUIRED_COLUMNS = {
    "id",
    "cwd",
    "updated_at",
    "archived",
    "title",
    "source",
    "thread_source",
    "is_pinned",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATE_RE = re.compile(r"^state_(\d+)\.sqlite$")


class InventoryError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory old Codex task directories without modifying them."
    )
    parser.add_argument("--root", required=True, help="Absolute cleanup root")
    parser.add_argument("--cutoff", required=True, help="Exclusive local date, YYYY-MM-DD")
    parser.add_argument("--db", help="Explicit Codex state SQLite database")
    return parser.parse_args()


def connect_readonly(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(path))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def has_required_schema(path: Path) -> bool:
    try:
        with connect_readonly(path) as connection:
            rows = connection.execute("PRAGMA table_info(threads)").fetchall()
    except sqlite3.Error:
        return False
    return REQUIRED_COLUMNS.issubset({row["name"] for row in rows})


def discover_database(explicit: str | None) -> tuple[Path, list[str]]:
    if explicit:
        input_path = Path(explicit).expanduser()
        input_mode = os.lstat(input_path).st_mode
        if not stat.S_ISREG(input_mode):
            raise InventoryError(f"Codex state database must be an entity file: {input_path}")
        path = input_path.resolve(strict=True)
        if not has_required_schema(path):
            raise InventoryError(f"invalid Codex state database: {path}")
        return path, [str(path)]

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    if not codex_home.is_dir():
        raise InventoryError(f"Codex data directory not found: {codex_home}")

    candidates: list[tuple[int, Path]] = []
    for path in codex_home.iterdir():
        match = STATE_RE.fullmatch(path.name)
        if not match or path.is_symlink() or not path.is_file():
            continue
        if has_required_schema(path):
            candidates.append((int(match.group(1)), path.resolve()))

    candidates.sort(reverse=True)
    paths = [str(path) for _, path in candidates]
    if not candidates:
        raise InventoryError("no readable Codex state database with the required schema")
    if len(candidates) > 1:
        raise InventoryError(
            "multiple usable Codex state databases found; cross-check list_threads and rerun "
            f"with --db. candidates={paths}"
        )
    return candidates[0][1], paths


def parse_cutoff(value: str) -> tuple[dt.datetime, int]:
    try:
        date = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise InventoryError("--cutoff must be YYYY-MM-DD") from exc
    local_naive = dt.datetime.combine(date, dt.time.min)
    cutoff_epoch = int(local_naive.timestamp())
    cutoff = dt.datetime.fromtimestamp(cutoff_epoch).astimezone()
    return cutoff, cutoff_epoch


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


def source_is_subagent(source: object) -> bool:
    if not isinstance(source, str):
        return False
    try:
        value = json.loads(source)
    except json.JSONDecodeError:
        return False
    return isinstance(value, dict) and "subagent" in value


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


def git_markers(candidate: Path) -> tuple[list[str], list[str], list[str]]:
    worktree_files: list[str] = []
    repositories: list[str] = []
    inspection_errors: list[str] = []

    def record_walk_error(error: OSError) -> None:
        inspection_errors.append(str(error))

    for current, dirs, files in os.walk(
        candidate, followlinks=False, onerror=record_walk_error
    ):
        current_path = Path(current)
        if ".git" in files:
            marker = current_path / ".git"
            worktree_files.append(str(marker))
        if ".git" in dirs:
            marker = current_path / ".git"
            try:
                mode = os.lstat(marker).st_mode
            except OSError:
                worktree_files.append(str(marker))
            else:
                if stat.S_ISDIR(mode):
                    repositories.append(str(current_path))
                else:
                    worktree_files.append(str(marker))
            dirs.remove(".git")
    return sorted(worktree_files), sorted(repositories), sorted(inspection_errors)


def run_git(repo: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=False
    )


def inspect_repository(repo: str) -> dict[str, object]:
    status_result = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    upstream_result = run_git(
        repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    result: dict[str, object] = {
        "path": repo,
        "status_check_ok": status_result.returncode == 0,
        "dirty_or_untracked": bool(status_result.stdout.strip())
        if status_result.returncode == 0
        else None,
        "upstream": upstream_result.stdout.strip()
        if upstream_result.returncode == 0
        else None,
        "unpushed_commits": None,
    }
    if upstream_result.returncode == 0:
        ahead_result = run_git(repo, "rev-list", "--count", "@{upstream}..HEAD")
        if ahead_result.returncode == 0:
            try:
                result["unpushed_commits"] = int(ahead_result.stdout.strip())
            except ValueError:
                pass
    return result


def load_threads(database: Path, root: Path) -> tuple[list[dict[str, object]], int]:
    query = """
        SELECT id, cwd, updated_at, archived, title, source,
               thread_source, is_pinned
        FROM threads
    """
    refs: list[dict[str, object]] = []
    total = 0
    with connect_readonly(database) as connection:
        for row in connection.execute(query):
            raw_cwd = row["cwd"]
            if not raw_cwd:
                continue
            real_cwd = Path(os.path.realpath(os.path.abspath(raw_cwd)))
            if not strict_descendant(real_cwd, root):
                continue
            total += 1
            thread_source = row["thread_source"]
            source = row["source"] or ""
            is_subagent = thread_source == "subagent" or source_is_subagent(source)
            refs.append(
                {
                    "id": row["id"],
                    "cwd": raw_cwd,
                    "cwd_real": str(real_cwd),
                    "updated_at": int(row["updated_at"]),
                    "archived": bool(row["archived"]),
                    "title": row["title"],
                    "thread_source": thread_source,
                    "is_pinned": bool(row["is_pinned"]),
                    "is_subagent": is_subagent,
                }
            )
    return refs, total


def scan_candidates(
    root: Path,
    cutoff_date: dt.date,
    cutoff_epoch: int,
    refs: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, str]], int]:
    refs_by_candidate: dict[str, list[dict[str, object]]] = {}
    for ref in refs:
        cwd = Path(str(ref["cwd_real"]))
        try:
            relative = cwd.relative_to(root)
        except ValueError:
            continue
        if len(relative.parts) < 2:
            continue
        candidate = root / relative.parts[0] / relative.parts[1]
        refs_by_candidate.setdefault(str(candidate), []).append(ref)

    current_cwd = Path(os.path.realpath(os.getcwd()))
    root_keep = path_entry_exists(root / ".codex-keep")
    old_candidates: list[dict[str, object]] = []
    excluded: list[dict[str, str]] = []
    newer_count = 0

    for date_entry in sorted(root.iterdir(), key=lambda item: item.name):
        if not DATE_RE.fullmatch(date_entry.name):
            continue
        try:
            date_mode = os.lstat(date_entry).st_mode
        except OSError as exc:
            excluded.append({"path": str(date_entry), "reason": f"lstat failed: {exc}"})
            continue
        if not stat.S_ISDIR(date_mode):
            excluded.append({"path": str(date_entry), "reason": "date layer is not an entity directory"})
            continue
        try:
            directory_date = dt.date.fromisoformat(date_entry.name)
        except ValueError:
            continue

        for task_entry in sorted(date_entry.iterdir(), key=lambda item: item.name):
            try:
                task_mode = os.lstat(task_entry).st_mode
            except OSError as exc:
                excluded.append({"path": str(task_entry), "reason": f"lstat failed: {exc}"})
                continue
            if not stat.S_ISDIR(task_mode):
                if stat.S_ISLNK(task_mode):
                    excluded.append({"path": str(task_entry), "reason": "candidate is a symlink"})
                continue

            real_path = Path(os.path.realpath(task_entry))
            relative_parts: tuple[str, ...] = ()
            try:
                relative_parts = real_path.relative_to(root).parts
            except ValueError:
                pass
            path_ok = strict_descendant(real_path, root) and len(relative_parts) == 2
            task_refs = sorted(
                refs_by_candidate.get(str(real_path), []),
                key=lambda ref: (int(ref["updated_at"]), str(ref["id"])),
                reverse=True,
            )
            latest_updated_at = (
                max(int(ref["updated_at"]) for ref in task_refs) if task_refs else None
            )
            before_cutoff = (
                latest_updated_at < cutoff_epoch
                if latest_updated_at is not None
                else directory_date < cutoff_date
            )
            if not before_cutoff:
                newer_count += 1
                continue

            worktree_files, repositories, inspection_errors = git_markers(real_path)
            git_status = [inspect_repository(repo) for repo in repositories]
            static_blocks: list[str] = []
            if root_keep:
                static_blocks.append("cleanup root contains .codex-keep")
            if path_entry_exists(real_path / ".codex-keep"):
                static_blocks.append("candidate contains .codex-keep")
            if not path_ok:
                static_blocks.append("real path is not exactly two levels below root")
            if path_is_within(current_cwd, real_path):
                static_blocks.append("candidate is current working directory or its ancestor")
            if worktree_files:
                static_blocks.append("candidate contains a .git file/worktree marker")
            if inspection_errors:
                static_blocks.append("candidate tree could not be fully inspected")
            size_bytes = directory_size(real_path)
            if size_bytes is None:
                static_blocks.append("directory size could not be measured")

            old_candidates.append(
                {
                    "path": str(task_entry),
                    "real_path": str(real_path),
                    "directory_date": directory_date.isoformat(),
                    "age_basis": "task_updated_at" if task_refs else "directory_date_orphan",
                    "latest_updated_at": latest_updated_at,
                    "size_bytes": size_bytes,
                    "refs": task_refs,
                    "primary_refs": [ref for ref in task_refs if not ref["is_subagent"]],
                    "subagent_refs": [ref for ref in task_refs if ref["is_subagent"]],
                    "worktree_git_files": worktree_files,
                    "tree_inspection_errors": inspection_errors,
                    "git_repositories": git_status,
                    "static_blocks": static_blocks,
                }
            )
    return old_candidates, excluded, newer_count


def main() -> int:
    args = parse_args()
    try:
        root_input = Path(args.root).expanduser()
        if not root_input.is_absolute():
            raise InventoryError(f"cleanup root must be absolute: {root_input}")
        root_lstat = os.lstat(root_input)
        if not stat.S_ISDIR(root_lstat.st_mode):
            raise InventoryError("cleanup root must be an entity directory")
        root = root_input.resolve(strict=True)
        cutoff, cutoff_epoch = parse_cutoff(args.cutoff)
        database, database_candidates = discover_database(args.db)
        refs, indexed_ref_count = load_threads(database, root)
        candidates, excluded, newer_count = scan_candidates(
            root, cutoff.date(), cutoff_epoch, refs
        )
    except (InventoryError, OSError, sqlite3.Error) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 2

    output = {
        "ok": True,
        "schema_version": 1,
        "root": str(root),
        "cutoff": cutoff.isoformat(),
        "cutoff_epoch": cutoff_epoch,
        "database": str(database),
        "database_candidates": database_candidates,
        "indexed_refs_under_root": indexed_ref_count,
        "old_candidates": candidates,
        "newer_candidate_count": newer_count,
        "excluded_paths": excluded,
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
