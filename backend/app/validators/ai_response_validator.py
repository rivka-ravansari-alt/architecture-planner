"""AI architecture response validation."""

from __future__ import annotations

import json
import re
from typing import Any

from app.config.params import (
    AI_RESPONSE_TOP_LEVEL_FIELDS,
    COMPONENT_REQUIRED_FIELDS,
    DEFAULT_DIAGRAM_TITLES,
    DIAGRAM_KEYS,
    ERR_AI_NO_JSON_OBJECT,
    ERR_AI_RESPONSE_EMPTY,
    RISK_REQUIRED_FIELDS,
    VALID_COMPONENT_TAGS,
    VALID_COMPONENT_TYPES,
    VALID_DIAGRAM_GROUPS,
    VALID_RISK_SEVERITIES,
)
from app.core.exceptions import AIValidationError
from app.services.cloud_defaults_service import CloudDefaultsService


class AIResponseValidator:
    """Validates and normalizes AI JSON architecture responses."""

    def __init__(self, cloud_defaults: CloudDefaultsService | None = None) -> None:
        self._cloud_defaults = cloud_defaults or CloudDefaultsService()

    def validate(self, raw: str) -> dict[str, Any]:
        payload = self._parse_json(raw)
        self._validate_top_level(payload)
        self._validate_components(payload)
        self._validate_architecture(payload)
        payload["diagrams"] = self._validate_diagrams(payload)
        self._validate_risks(payload)
        self._validate_string_lists(payload, "recommendations")
        self._validate_string_lists(payload, "next_steps")
        return payload

    def _parse_json(self, raw: str) -> dict[str, Any]:
        try:
            payload = json.loads(self._extract_json(raw))
        except json.JSONDecodeError as exc:
            raise AIValidationError(f"AI response is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise AIValidationError("AI response must be a JSON object.")
        return payload

    def _extract_json(self, raw: str) -> str:
        text = raw.strip()
        if not text:
            raise AIValidationError(ERR_AI_RESPONSE_EMPTY)

        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            return fence_match.group(1).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise AIValidationError(ERR_AI_NO_JSON_OBJECT)
        return text[start : end + 1]

    def _validate_top_level(self, payload: dict[str, Any]) -> None:
        for field in AI_RESPONSE_TOP_LEVEL_FIELDS:
            if field not in payload:
                raise AIValidationError(f"Missing required field: {field}")

    def _validate_components(self, payload: dict[str, Any]) -> None:
        components = payload["components"]
        if not isinstance(components, list) or not components:
            raise AIValidationError("components must be a non-empty list.")

        for index, component in enumerate(components):
            self._validate_component(component, index)

    def _validate_component(self, component: Any, index: int) -> None:
        if not isinstance(component, dict):
            raise AIValidationError(f"components[{index}] must be an object.")
        for key in COMPONENT_REQUIRED_FIELDS:
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
        if tag not in VALID_COMPONENT_TAGS:
            raise AIValidationError(
                f"components[{index}].tag must be 'required' or 'optional', got '{component['tag']}'."
            )
        component["tag"] = tag
        component["cloud_options"] = self._cloud_defaults.normalize_cloud_options(component)

    def _validate_architecture(self, payload: dict[str, Any]) -> None:
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

    def _validate_diagrams(self, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        diagrams = payload.get("diagrams")
        if not isinstance(diagrams, dict):
            raise AIValidationError("diagrams must be an object.")

        normalized: dict[str, dict[str, Any]] = {}
        for key in DIAGRAM_KEYS:
            if key not in diagrams:
                raise AIValidationError(f"Missing required field: diagrams.{key}")
            normalized[key] = self._validate_diagram(
                diagrams[key],
                field_path=f"diagrams.{key}",
                default_title=DEFAULT_DIAGRAM_TITLES[key],
            )
        return normalized

    def _validate_diagram(
        self,
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

        seen_ids = self._validate_nodes(diagram.get("nodes"), field_path)
        normalized_edges = self._validate_edges(diagram.get("edges"), field_path, seen_ids)

        return {"title": title, "nodes": seen_ids[1], "edges": normalized_edges}

    def _validate_nodes(self, nodes: Any, field_path: str) -> tuple[set[str], list[dict[str, str]]]:
        if not isinstance(nodes, list) or not nodes:
            raise AIValidationError(f"{field_path}.nodes must be a non-empty list.")

        seen_ids: set[str] = set()
        normalized_nodes: list[dict[str, str]] = []
        for index, node in enumerate(nodes):
            normalized = self._validate_node(node, field_path, index)
            node_id = normalized["id"]
            if node_id in seen_ids:
                raise AIValidationError(
                    f"{field_path}.nodes[{index}].id must be unique, got duplicate '{node_id}'."
                )
            seen_ids.add(node_id)
            normalized_nodes.append(normalized)
        return seen_ids, normalized_nodes

    def _validate_node(self, node: Any, field_path: str, index: int) -> dict[str, str]:
        if not isinstance(node, dict):
            raise AIValidationError(f"{field_path}.nodes[{index}] must be an object.")
        node_id = str(node.get("id", "")).strip()
        node_name = str(node.get("name", "")).strip()
        if not node_id:
            raise AIValidationError(f"{field_path}.nodes[{index}].id is required.")
        if not node_name:
            raise AIValidationError(f"{field_path}.nodes[{index}].name is required.")

        normalized: dict[str, str] = {"id": node_id, "name": node_name}
        group = node.get("group")
        if group is not None:
            group_value = str(group).strip().lower()
            if group_value and group_value in VALID_DIAGRAM_GROUPS:
                normalized["group"] = group_value
        return normalized

    def _validate_edges(
        self,
        edges: Any,
        field_path: str,
        seen_ids: tuple[set[str], list[dict[str, str]]],
    ) -> list[dict[str, str]]:
        node_ids, _ = seen_ids
        if not isinstance(edges, list) or not edges:
            raise AIValidationError(f"{field_path}.edges must be a non-empty list.")

        normalized_edges: list[dict[str, str]] = []
        for index, edge in enumerate(edges):
            normalized_edges.append(self._validate_edge(edge, field_path, index, node_ids))
        return normalized_edges

    def _validate_edge(
        self,
        edge: Any,
        field_path: str,
        index: int,
        node_ids: set[str],
    ) -> dict[str, str]:
        if not isinstance(edge, dict):
            raise AIValidationError(f"{field_path}.edges[{index}] must be an object.")
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        if not source or not target:
            raise AIValidationError(f"{field_path}.edges[{index}] must include source and target.")
        if source not in node_ids:
            raise AIValidationError(
                f"{field_path}.edges[{index}].source references unknown node '{source}'."
            )
        if target not in node_ids:
            raise AIValidationError(
                f"{field_path}.edges[{index}].target references unknown node '{target}'."
            )

        normalized: dict[str, str] = {"source": source, "target": target}
        label = edge.get("label")
        if label is not None and str(label).strip():
            normalized["label"] = str(label).strip()
        return normalized

    def _validate_risks(self, payload: dict[str, Any]) -> None:
        risks = payload["risks"]
        if not isinstance(risks, list):
            raise AIValidationError("risks must be a list.")
        for index, risk in enumerate(risks):
            self._validate_risk(risk, index)

    def _validate_risk(self, risk: Any, index: int) -> None:
        if not isinstance(risk, dict):
            raise AIValidationError(f"risks[{index}] must be an object.")
        for key in RISK_REQUIRED_FIELDS:
            if key not in risk or not str(risk[key]).strip():
                raise AIValidationError(f"risks[{index}] is missing {key}.")
        severity = str(risk["severity"]).strip().lower()
        if severity not in VALID_RISK_SEVERITIES:
            raise AIValidationError(
                f"risks[{index}].severity must be low, medium, or high, got '{risk['severity']}'."
            )
        risk["severity"] = severity

    def _validate_string_lists(self, payload: dict[str, Any], field: str) -> None:
        items = payload[field]
        if not isinstance(items, list) or not items:
            raise AIValidationError(f"{field} must be a non-empty list.")
        if not all(isinstance(item, str) and item.strip() for item in items):
            raise AIValidationError(f"{field} must contain non-empty strings.")
