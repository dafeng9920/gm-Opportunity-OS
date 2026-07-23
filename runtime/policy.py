from __future__ import annotations

from dataclasses import dataclass

from adapters.policy import CapabilityPolicy, RESTRICTED_POLICY


@dataclass(frozen=True, slots=True)
class InvocationRequest:
    caller: str
    adapter_id: str
    runtime_id: str
    workspace: str = "temporary_read_only"
    network: str = "none"
    allowed_hosts: tuple[str, ...] = ()
    target_host: str = ""
    database_access: bool = False
    registry_access: bool = False
    secrets_access: bool = False
    external_version: str = ""


class PolicyEngine:
    """Turns restricted-v0 into checked invocation invariants."""
    def verify(self, policy: CapabilityPolicy, request: InvocationRequest) -> None:
        if policy != RESTRICTED_POLICY:
            raise ValueError("only restricted-v0 is permitted in runtime isolation v0.1")
        if request.workspace != "temporary_read_only":
            raise PermissionError("runtime may only read a temporary workspace")
        if request.network == "none":
            pass
        elif request.network == "allowlisted":
            if not request.target_host or request.target_host not in request.allowed_hosts:
                raise PermissionError("runtime target is not in the network allowlist")
        else:
            raise PermissionError("runtime network access is not permitted")
        if request.database_access or request.registry_access or request.secrets_access:
            raise PermissionError("runtime may not access Core state or secrets")
