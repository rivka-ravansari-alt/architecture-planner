"""Validate AI architecture generation responses."""

from __future__ import annotations

import json
import re
from typing import Any

from .cloud_defaults import normalize_cloud_options
from .component_types import VALID_COMPONENT_TYPES
from .diagram_types import DEFAULT_DIAGRAM_TITLES, DIAGRAM_KEYS


class AIValidationError(ValueError):
    """Raised when the AI response is missing or invalid."""


_VALID_TAGS = frozenset({"required", "optional"})
_VALID_SEVERITIES = frozenset({"low", "medium", "high"})


def _extract_json(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise AIValidationError("AI response was empty.")

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AIValidationError("AI response did not contain a JSON object.")
    return text[start : end + 1]


def _validate_diagram(
    diagram: Any,
    *,
    field_path: str,
    default_title: str,
) -> dict[str, Any]:
    if not isinstance(diagram, dict):
        raise AIValidationError(f"{field_path} must be an object.")

    title = str(diagram.get("title") or default_title).strip()
    if not title:
        raise AIValidationError(f"{field_path}.title is required.")

    nodes = diagram.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise AIValidationError(f"{field_path}.nodes must be a non-empty list.")

    normalized_nodes: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise AIValidationError(f"{field_path}.nodes[{index}] must be an object.")
        node_id = str(node.get("id", "")).strip()
        node_name = str(node.get("name", "")).strip()
        if not node_id:
            raise AIValidationError(f"{field_path}.nodes[{index}].id is required.")
        if not node_name:
            raise AIValidationError(f"{field_path}.nodes[{index}].name is required.")
        if node_id in seen_ids:
            raise AIValidationError(
                f"{field_path}.nodes[{index}].id must be unique, got duplicate '{node_id}'."
            )
        seen_ids.add(node_id)
        normalized_nodes.append({"id": node_id, "name": node_name})

    edges = diagram.get("edges")
    if not isinstance(edges, list) or not edges:
        raise AIValidationError(f"{field_path}.edges must be a non-empty list.")

    normalized_edges: list[dict[str, str]] = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise AIValidationError(f"{field_path}.edges[{index}] must be an object.")
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        if not source or not target:
            raise AIValidationError(f"{field_path}.edges[{index}] must include source and target.")
        if source not in seen_ids:
            raise AIValidationError(
                f"{field_path}.edges[{index}].source references unknown node '{source}'."
            )
        if target not in seen_ids:
            raise AIValidationError(
                f"{field_path}.edges[{index}].target references unknown node '{target}'."
            )
        normalized_edge: dict[str, str] = {"source": source, "target": target}
        label = edge.get("label")
        if label is not None and str(label).strip():
            normalized_edge["label"] = str(label).strip()
        normalized_edges.append(normalized_edge)

    return {
        "title": title,
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }


def _validate_diagrams(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    diagrams = payload.get("diagrams")
    if not isinstance(diagrams, dict):
        raise AIValidationError("diagrams must be an object.")

    normalized: dict[str, dict[str, Any]] = {}
    for key in DIAGRAM_KEYS:
        if key not in diagrams:
            raise AIValidationError(f"Missing required field: diagrams.{key}")
        normalized[key] = _validate_diagram(
            diagrams[key],
            field_path=f"diagrams.{key}",
            default_title=DEFAULT_DIAGRAM_TITLES[key],
        )

    return normalized


def validate_ai_response(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        raise AIValidationError(f"AI response is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AIValidationError("AI response must be a JSON object.")

    for field in ("components", "architecture", "diagrams", "risks", "recommendations", "next_steps"):
        if field not in payload:
            raise AIValidationError(f"Missing required field: {field}")

    components = payload["components"]
    if not isinstance(components, list) or not components:
        raise AIValidationError("components must be a non-empty list.")

    for index, component in enumerate(components):
        if not isinstance(component, dict):
            raise AIValidationError(f"components[{index}] must be an object.")
        for key in ("name", "type", "tag", "reason"):
            if key not in component or not str(component[key]).strip():
                raise AIValidationError(f"components[{index}] is missing {key}.")
        component_type = str(component["type"]).strip().lower()
        if component_type not in VALID_COMPONENT_TYPES:
            raise AIValidationError(
                f"components[{index}].type must be one of: "
                f"{', '.join(sorted(VALID_COMPONENT_TYPES))}, got '{component['type']}'."
            )
        component["type"] = component_type
        tag = str(component["tag"]).strip().lower()
        if tag not in _VALID_TAGS:
            raise AIValidationError(
                f"components[{index}].tag must be 'required' or 'optional', got '{component['tag']}'."
            )
        component["tag"] = tag

        component["cloud_options"] = normalize_cloud_options(component)

    architecture = payload["architecture"]
    if not isinstance(architecture, dict):
        raise AIValidationError("architecture must be an object.")
    if not str(architecture.get("summary", "")).strip():
        raise AIValidationError("architecture.summary is required.")
    flow = architecture.get("flow")
    if not isinstance(flow, list) or not flow:
        raise AIValidationError("architecture.flow must be a non-empty list.")
    if not all(isinstance(step, str) and step.strip() for step in flow):
        raise AIValidationError("architecture.flow must contain non-empty strings.")

    payload["diagrams"] = _validate_diagrams(payload)

    risks = payload["risks"]
    if not isinstance(risks, list):
        raise AIValidationError("risks must be a list.")
    for index, risk in enumerate(risks):
        if not isinstance(risk, dict):
            raise AIValidationError(f"risks[{index}] must be an object.")
        for key in ("title", "description", "severity"):
            if key not in risk or not str(risk[key]).strip():
                raise AIValidationError(f"risks[{index}] is missing {key}.")
        severity = str(risk["severity"]).strip().lower()
        if severity not in _VALID_SEVERITIES:
            raise AIValidationError(
                f"risks[{index}].severity must be low, medium, or high, got '{risk['severity']}'."
            )
        risk["severity"] = severity

    for field in ("recommendations", "next_steps"):
        items = payload[field]
        if not isinstance(items, list) or not items:
            raise AIValidationError(f"{field} must be a non-empty list.")
        if not all(isinstance(item, str) and item.strip() for item in items):
            raise AIValidationError(f"{field} must contain non-empty strings.")

    return payload
