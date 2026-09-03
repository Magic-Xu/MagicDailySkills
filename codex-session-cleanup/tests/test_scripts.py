from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SKILL_ROOT / "scripts" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inventory = load_script("cleanup_inventory", "inventory.py")
move_to_trash = load_script("cleanup_move_to_trash", "move_to_trash.py")


def create_state_database(path: Path, rows: list[tuple[object, ...]]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                cwd TEXT,
                updated_at INTEGER,
                archived INTEGER,
                title TEXT,
                source TEXT,
                thread_source TEXT,
                is_pinned INTEGER
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO threads (
                id, cwd, updated_at, archived, title, source,
                thread_source, is_pinned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


class InventoryTests(unittest.TestCase):
    def test_nested_cwd_is_mapped_to_its_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            root = base / "sessions"
            candidate = root / "2026-01-01" / "task-a"
            nested_cwd = candidate / "workspace" / "module"
            nested_cwd.mkdir(parents=True)
            database = base / "state.sqlite"
            create_state_database(
                database,
                [
                    (
                        "thread-1",
                        str(nested_cwd),
                        100,
                        1,
                        "Archived task",
                        "vscode",
                        "user",
                        0,
                    )
                ],
            )

            refs, count = inventory.load_threads(database, root)
            candidates, excluded, newer_count = inventory.scan_candidates(
                root, inventory.dt.date(2026, 1, 2), 200, refs
            )

            self.assertEqual(count, 1)
            self.assertEqual(excluded, [])
            self.assertEqual(newer_count, 0)
            self.assertEqual([ref["id"] for ref in candidates[0]["refs"]], ["thread-1"])
            self.assertEqual(candidates[0]["age_basis"], "task_updated_at")

    def test_subagent_source_json_is_detected_independent_of_whitespace(self) -> None:
        self.assertTrue(inventory.source_is_subagent('  {"subagent": {"other": "guardian"}}'))
        self.assertFalse(inventory.source_is_subagent("vscode"))

    def test_broken_keep_marker_blocks_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "sessions"
            candidate = root / "2026-01-01" / "task-a"
            candidate.mkdir(parents=True)
            os.symlink("missing-target", candidate / ".codex-keep")

            candidates, _, _ = inventory.scan_candidates(
                root, inventory.dt.date(2026, 1, 2), 200, []
            )

            self.assertIn("candidate contains .codex-keep", candidates[0]["static_blocks"])


class MoveToTrashTests(unittest.TestCase):
    def create_layout(self, base: Path, date_name: str = "2026-01-01") -> tuple[Path, Path, Path]:
        root = base / "sessions"
        candidate = root / date_name / "task-a"
        trash = base / "Trash"
        candidate.mkdir(parents=True)
        trash.mkdir()
        (candidate / "payload.txt").write_text("keep me\n", encoding="utf-8")
        return root, candidate, trash

    def test_moves_candidate_and_writes_complete_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate, trash = self.create_layout(Path(temporary).resolve())

            result = move_to_trash.move_candidates(root, [str(candidate)], trash)

            self.assertTrue(result["ok"])
            self.assertFalse(candidate.exists())
            destination = Path(result["moved"][0]["trash_path"])
            self.assertEqual((destination / "payload.txt").read_text(encoding="utf-8"), "keep me\n")
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            self.assertTrue(manifest["complete"])
            self.assertEqual(manifest["items"][0]["source"], str(candidate))

    def test_rejects_noncanonical_candidate_path_before_moving(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate, trash = self.create_layout(Path(temporary).resolve())
            noncanonical = candidate.parent / ".." / candidate.parent.name / candidate.name

            with self.assertRaisesRegex(move_to_trash.TrashMoveError, "must be canonical"):
                move_to_trash.move_candidates(root, [str(noncanonical)], trash)

            self.assertTrue(candidate.exists())

    def test_rejects_invalid_date_layer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate, trash = self.create_layout(
                Path(temporary).resolve(), date_name="2026-99-01"
            )

            with self.assertRaisesRegex(move_to_trash.TrashMoveError, "date layer is invalid"):
                move_to_trash.move_candidates(root, [str(candidate)], trash)

            self.assertTrue(candidate.exists())

    def test_rejects_broken_keep_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate, trash = self.create_layout(Path(temporary).resolve())
            os.symlink("missing-target", candidate / ".codex-keep")

            with self.assertRaisesRegex(move_to_trash.TrashMoveError, "protected"):
                move_to_trash.move_candidates(root, [str(candidate)], trash)

            self.assertTrue(candidate.exists())

    def test_rejects_relative_cleanup_root(self) -> None:
        with self.assertRaisesRegex(move_to_trash.TrashMoveError, "must be absolute"):
            move_to_trash.move_candidates(Path("sessions"), ["/tmp/task"], Path("/tmp"))


if __name__ == "__main__":
    unittest.main()
