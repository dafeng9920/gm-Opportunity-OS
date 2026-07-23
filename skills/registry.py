"""SQLite source of truth for Skill Package registrations."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .contracts.models import SkillPackage, SkillStatus
class SkillRegistry:
    def __init__(self, database: Path | str) -> None:
        self._db=sqlite3.connect(database); self._db.row_factory=sqlite3.Row
        self._db.execute('CREATE TABLE IF NOT EXISTS skill_packages (skill_id TEXT, version TEXT, name TEXT, responsibility TEXT, input_contract TEXT, output_contract TEXT, allowed_actions TEXT, forbidden_actions TEXT, minimal_prompt TEXT, status TEXT, PRIMARY KEY(skill_id, version))')
    def register(self, package: SkillPackage) -> None:
        self._db.execute('INSERT INTO skill_packages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (package.skill_id, package.version, package.name, package.responsibility, package.input_contract, package.output_contract, '\n'.join(package.allowed_actions), '\n'.join(package.forbidden_actions), package.minimal_prompt, package.status.value)); self._db.commit()
    def get(self, skill_id: str, version: str) -> SkillPackage | None:
        row=self._db.execute('SELECT * FROM skill_packages WHERE skill_id=? AND version=?',(skill_id,version)).fetchone()
        if not row:return None
        item=dict(row); return SkillPackage(item['skill_id'],item['name'],item['version'],item['responsibility'],item['input_contract'],item['output_contract'],tuple(item['allowed_actions'].split('\n')),tuple(item['forbidden_actions'].split('\n')),item['minimal_prompt'],SkillStatus(item['status']))
    def list(self) -> list[SkillPackage]:
        rows=self._db.execute('SELECT * FROM skill_packages ORDER BY skill_id, version').fetchall(); return [self.get(row['skill_id'],row['version']) for row in rows]
