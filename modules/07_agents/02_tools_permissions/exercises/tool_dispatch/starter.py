"""Dispatch allowlisted proposals through application-owned permissions."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Proposal(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    call_id: str = Field(pattern=r"^call-[0-9]+$")
    tool: Literal["lookup_exhibit", "reserve_workshop"]
    arguments: dict[str, object]


class LookupArguments(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    exhibit_id: str = Field(pattern=r"^E-[0-9]{3}$")


class ReservationArguments(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    workshop_id: str = Field(pattern=r"^W-[0-9]{3}$")
    places: int = Field(ge=1, le=4)


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    tool: str
    output: str


def dispatch_tool(
    raw_proposal: str,
    permissions: frozenset[str],
    executors: Mapping[str, Callable[[BaseModel], str]],
) -> ToolResult:
    """Validate, authorize, and invoke exactly one registered executor; see README."""
    raise NotImplementedError("Implement authorized museum tool dispatch")
