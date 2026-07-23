from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    filesystem: str = "restricted"
    network: str = "restricted"
    execution: str = "controlled"
    database: str = "no_direct_access"

    def __post_init__(self) -> None:
        if self.filesystem != "restricted":
            raise ValueError("adapter filesystem access must be restricted")
        if self.network != "restricted":
            raise ValueError("adapter network access must be restricted")
        if self.execution != "controlled":
            raise ValueError("adapter execution must be controlled")
        if self.database != "no_direct_access":
            raise ValueError("adapters may not directly access Core databases")

    @property
    def profile_name(self) -> str:
        return "restricted-v0"


RESTRICTED_POLICY = CapabilityPolicy()
