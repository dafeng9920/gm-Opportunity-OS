from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4
class SkillStatus(StrEnum): IMPLEMENTED='implemented'; DEPRECATED='deprecated'; DISABLED='disabled'
def now() -> str: return datetime.now(UTC).isoformat()
@dataclass(frozen=True, slots=True)
class SkillPackage:
    skill_id: str
    name: str
    version: str
    responsibility: str
    input_contract: str
    output_contract: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    minimal_prompt: str
    status: SkillStatus = SkillStatus.IMPLEMENTED
    def __post_init__(self) -> None:
        if not all((self.skill_id, self.name, self.version, self.responsibility, self.input_contract, self.output_contract, self.minimal_prompt)): raise ValueError('skill package identity and contracts are required')
        if not self.allowed_actions or not self.forbidden_actions: raise ValueError('skill package must declare allowed and forbidden actions')
@dataclass(frozen=True, slots=True)
class SkillInvocation:
    skill_id: str
    input_reference: str
    task_id: str
    context_refs: tuple[str, ...]
    runtime_policy: str
    created_at: str = field(default_factory=now)
    id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self) -> None:
        if not all((self.id, self.skill_id, self.input_reference, self.task_id, self.runtime_policy, self.created_at)): raise ValueError('invocation fields are required')
