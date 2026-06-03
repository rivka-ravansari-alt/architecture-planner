"""Types produced when mapping AI output to the persistence layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MappedComponent:
    key: str
    name: str
    component_type: str
    reason: str
    category: str
    optional: bool
    order: int
    cloud: dict[str, list[str]]


@dataclass
class MappedRisk:
    title: str
    description: str
    severity: str
