from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


class SubprocessScraplingWorker:
    """Runs the pinned Scrapling fetcher in its project-local venv; no Core import occurs there."""
    def __init__(self, python_executable: Path, worker_script: Path, timeout_seconds: int = 30) -> None:
        self.python_executable = python_executable
        self.worker_script = worker_script
        self.timeout_seconds = timeout_seconds

    def fetch(self, target: str, parameters: dict[str, Any]) -> str:
        payload = json.dumps({"target": target, "parameters": parameters})
        environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "PATH") if key in os.environ}
        environment["PYTHONNOUSERSITE"] = "1"
        completed = subprocess.run([str(self.python_executable), str(self.worker_script)], input=payload, text=True, capture_output=True, timeout=self.timeout_seconds, env=environment, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"scrapling worker failed: {completed.stderr.strip()[:500]}")
        response = json.loads(completed.stdout)
        body = response.get("body")
        if not isinstance(body, str) or not body:
            raise RuntimeError("scrapling worker returned no body")
        return body
