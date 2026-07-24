"""Minimal deterministic runtime that produces one audited RoleArtifact per invocation."""

from __future__ import annotations

from governance.triad.contracts import RoleArtifact

from .assembler import RoleArtifactAssembler
from .contracts import RoleInvocation, TriadExecutionContext
from .runner import DeterministicRoleRunner


class RoleArtifactRuntime:
    """A local deterministic chain step; no RuntimeManager, Dispatch, or Decision Writer integration."""

    def __init__(self, runner: DeterministicRoleRunner, assembler: RoleArtifactAssembler) -> None:
        self._runner = runner
        self._assembler = assembler

    def execute(self, context: TriadExecutionContext, invocation: RoleInvocation) -> RoleArtifact:
        result = self._runner.run(context, invocation)
        return self._assembler.assemble(context, invocation, result)