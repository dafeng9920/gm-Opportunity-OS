from __future__ import annotations

from typing import Callable, TypeVar

from .policy import InvocationRequest

T = TypeVar("T")


class MockSandbox:
    """No-process sandbox seam for v0.1; only invokes a supplied mock callable after policy checks."""
    def execute(self, request: InvocationRequest, handler: Callable[[], T]) -> T:
        return handler()
