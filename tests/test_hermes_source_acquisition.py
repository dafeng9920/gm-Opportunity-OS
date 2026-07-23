import json
import unittest
from pathlib import Path


class HermesSourceAcquisitionTests(unittest.TestCase):
    def test_pinned_source_and_lock_exist_without_execution(self) -> None:
        lock_path = Path("evaluations/hermes/source-lock.json")
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        self.assertEqual(lock["tag"], "v2026.7.20")
        self.assertEqual(lock["commit"], "3ef6bbd201263d354fd83ec55b3c306ded2eb72a")
        self.assertEqual(lock["license"], "MIT")
        self.assertEqual(len(lock["hash"]), 64)
        self.assertTrue(Path(lock["archive"]).is_file())
        self.assertTrue(Path(lock["source_directory"]).is_dir())
        self.assertEqual(lock["execution"], "not executed")
