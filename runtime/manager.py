from __future__ import annotations

import json
from time import perf_counter
from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Any, Callable, TypeVar

from adapters.policy import CapabilityPolicy
from core.registry import ComponentRegistry

from .audit import AuditEvent, AuditLog
from .policy import InvocationRequest, PolicyEngine
from .sandbox import MockSandbox

T = TypeVar("T")


class RuntimeManager:
    """Core-owned gate: validates runtime/policy, runs sandbox callback, and audits every attempt."""
    def __init__(self, registry: ComponentRegistry, audit_log: AuditLog, policy_engine: PolicyEngine | None = None, sandbox: MockSandbox | None = None) -> None:
        self.registry = registry
        self.audit_log = audit_log
        self.policy_engine = policy_engine or PolicyEngine()
        self.sandbox = sandbox or MockSandbox()

    @staticmethod
    def _hash(value: Any) -> str:
        if is_dataclass(value):
            value = asdict(value)
        encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def invoke(self, request: InvocationRequest, policy: CapabilityPolicy, payload: dict[str, Any], handler: Callable[[], T]) -> T:
        input_hash = self._hash(payload)
        try:
            component = self.registry.get(request.runtime_id)
            runtime = self.registry.get_runtime(request.runtime_id)
            if component is None or component.type != "runtime" or component.status != "active":
                raise PermissionError("runtime is not active")
            if runtime is None or runtime.status != "available" or runtime.policy != policy.profile_name:
                raise PermissionError("runtime is not available with the requested policy")
            self.policy_engine.verify(policy, request)
        except Exception:
            self.audit_log.append(AuditEvent(caller=request.caller, adapter_id=request.adapter_id, runtime_id=request.runtime_id, input_hash=input_hash, output_hash="", decision="DENY", external_version=request.external_version))
            raise

        started = perf_counter()
        try:
            output = self.sandbox.execute(request, handler)
        except Exception:
            elapsed = int((perf_counter() - started) * 1000)
            self.audit_log.append(AuditEvent(caller=request.caller, adapter_id=request.adapter_id, runtime_id=request.runtime_id, input_hash=input_hash, output_hash="", decision="ERROR", external_version=request.external_version, execution_ms=elapsed))
            raise
        elapsed = int((perf_counter() - started) * 1000)
        self.audit_log.append(AuditEvent(caller=request.caller, adapter_id=request.adapter_id, runtime_id=request.runtime_id, input_hash=input_hash, output_hash=self._hash(output), decision="ALLOW", external_version=request.external_version, execution_ms=elapsed))
        return output


