"""Validates the structured artifact boundary; it neither invokes nor implements an Agent."""
from __future__ import annotations
from typing import Any
from opportunity.judge.contracts import JudgeAssessment
from .models import SkillInvocation
class SkillOutputValidator:
    _OUTPUTS = {'opportunity.judge': JudgeAssessment}
    def validate(self, invocation: SkillInvocation, output: Any) -> Any:
        expected = self._OUTPUTS.get(invocation.skill_id)
        if expected is None: raise KeyError(f'unregistered output contract: {invocation.skill_id}')
        if not isinstance(output, expected): raise ValueError('skill output does not match its registered contract')
        return output
