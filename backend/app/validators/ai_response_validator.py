"""AI architecture response validation."""

from __future__ import annotations

import json
import re
from typing import Any

from app.config.params import (
    AI_RESPONSE_TOP_LEVEL_FIELDS,
    COMPONENT_REQUIRED_FIELDS,
    COMPONENT_TYPE_ALIASES,
    DEFAULT_DIAGRAM_TITLES,
    DIAGRAM_KEYS,
    ERR_AI_NO_JSON_OBJECT,
    ERR_AI_RESPONSE_EMPTY,
    IMPLEMENTATION_MODEL_LABELS,
    LEGACY_DIAGRAM_KEY_ALIASES,
    VALID_COMPONENT_TAGS,
    VALID_COMPONENT_TYPES,
    VALID_DIAGRAM_GROUPS,
    VALID_IMPLEMENTATION_MODELS,
)
from app.core.exceptions import AIValidationError
from app.services.cloud_defaults_service import CloudDefaultsService

_DEFAULT_IMPLEMENTATION_OPTIONS: dict[str, object] = {
    "recommended": "managed_service",
    "managed_service": {
        "when_to_use": "Managed platform suitable for this component at the requested scale.",
        "cost_impact": "Varies with usage and scale.",
        "pros": [],
        "cons": [],
    },
}


class AIResponseValidator:
    def __init__(self, cloud_defaults: CloudDefaultsService | None = None) -> None:
        self._cloud_defaults = cloud_defaults or CloudDefaultsService()

    def validate(self, raw: str) -> dict[str, Any]:
        payload = self._parse_json(raw)
        payload = self._normalize_ai_payload(payload)
        self._validate_top_level(payload)
        self._validate_components(payload)
        self._validate_architecture(payload)
        payload["diagrams"] = self._validate_diagrams(payload)
        return payload

    def validate_components(self, raw: str) -> dict[str, Any]:
        payload = self._parse_json(raw)
        payload = self._normalize_ai_payload(payload)
        if "components" not in payload:
            raise AIValidationError("Missing required field: components")
        self._validate_components(payload)
        return payload

    def validate_diagrams(self, raw: str) -> dict[str, Any]:
        payload = self._parse_json(raw)
        payload = self._normalize_ai_payload(payload)
        self._validate_architecture(payload)
        payload["diagrams"] = self._validate_diagrams(payload)
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

    def _normalize_ai_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        for component in payload.get("components", []):
            if not isinstance(component, dict):
                continue
            if "implementation_options" not in component:
                component["implementation_options"] = dict(_DEFAULT_IMPLEMENTATION_OPTIONS)

        diagram = payload.get("diagram")
        if isinstance(diagram, dict) and "diagrams" not in payload:
            payload["diagrams"] = {
                "high_level": diagram,
                "system_flow": diagram,
                "technical_architecture": diagram,
            }

        architecture = payload.get("architecture")
        if isinstance(architecture, dict):
            if not str(architecture.get("summary", "")).strip():
                architecture["summary"] = "High-level architecture for the product."
            flow = architecture.get("flow")
            if not isinstance(flow, list) or not flow:
                architecture["flow"] = [
                    "User interacts with the client.",
                    "Client sends requests to the backend.",
                    "Backend reads and writes application data.",
                ]

        payload.pop("risks", None)
        payload.pop("recommendations", None)
        payload.pop("next_steps", None)

        diagrams = payload.get("diagrams")
        if isinstance(diagrams, dict):
            diagrams.pop("technical_flow", None)
            payload["diagrams"] = self._migrate_diagram_keys(diagrams)

        return payload

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
        component_type = COMPONENT_TYPE_ALIASES.get(component_type, component_type)
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
        component["reason"] = self._cloud_defaults.default_reason_for_type(component_type)
        component["cloud_options"] = self._cloud_defaults.normalize_cloud_options(component)
        component["implementation_options"] = self._normalize_implementation_options(
            component.get("implementation_options"),
            index,
        )

    def _normalize_implementation_options(
        self,
        value: Any,
        index: int,
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise AIValidationError(
                f"components[{index}].implementation_options must be an object."
            )

        recommended = str(value.get("recommended", "")).strip().lower()
        if recommended not in VALID_IMPLEMENTATION_MODELS:
            allowed = ", ".join(sorted(VALID_IMPLEMENTATION_MODELS))
            raise AIValidationError(
                f"components[{index}].implementation_options.recommended must be one of: "
                f"{allowed}, got '{value.get('recommended')}'."
            )

        normalized: dict[str, Any] = {"recommended": recommended}
        for model in VALID_IMPLEMENTATION_MODELS:
            raw = value.get(model)
            if raw is None:
                continue
            detail = self._normalize_option_detail(raw, index, model)
            if detail:
                normalized[model] = detail

        recommended_detail = normalized.get(recommended)
        recommended_when = (
            recommended_detail.get("when_to_use", "")
            if isinstance(recommended_detail, dict)
            else ""
        )
        if not str(recommended_when).strip():
            label = IMPLEMENTATION_MODEL_LABELS.get(recommended, recommended)
            raise AIValidationError(
                f"components[{index}].implementation_options must include a non-empty "
                f"when_to_use for the recommended model ({label})."
            )

        return normalized

    def _normalize_option_detail(
        self,
        raw: Any,
        index: int,
        model: str,
    ) -> dict[str, Any] | None:
        field_path = f"components[{index}].implementation_options.{model}"

        if isinstance(raw, str):
            when_to_use = raw.strip()
            if not when_to_use:
                return None
            not_applicable = when_to_use.lower().startswith("not applicable")
            detail: dict[str, Any] = {
                "when_to_use": when_to_use,
                "cost_impact": "" if not_applicable else "Varies with usage and scale.",
                "pros": [],
                "cons": [],
            }
            if not_applicable:
                detail["not_applicable"] = True
            return detail

        if not isinstance(raw, dict):
            raise AIValidationError(f"{field_path} must be a string or object.")

        when_to_use = str(raw.get("when_to_use", "")).strip()
        if not when_to_use:
            raise AIValidationError(f"{field_path}.when_to_use is required.")

        cost_impact = str(raw.get("cost_impact", "")).strip()
        pros = self._normalize_string_list(raw.get("pros"), f"{field_path}.pros")
        cons = self._normalize_string_list(raw.get("cons"), f"{field_path}.cons")
        not_applicable = bool(raw.get("not_applicable")) or when_to_use.lower().startswith(
            "not applicable"
        )

        detail = {
            "when_to_use": when_to_use,
            "cost_impact": cost_impact,
            "pros": pros,
            "cons": cons,
        }
        if not_applicable:
            detail["not_applicable"] = True
        return detail

    @staticmethod
    def _normalize_string_list(value: Any, field_path: str) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise AIValidationError(f"{field_path} must be a list of strings.")
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

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
        node_type = node.get("type")
        if node_type is not None and str(node_type).strip():
            normalized["type"] = COMPONENT_TYPE_ALIASES.get(
                str(node_type).strip().lower(),
                str(node_type).strip().lower(),
            )
        return normalized

    def _validate_edges(
        self,
        edges: Any,
        field_path: str,
        seen_ids: tuple[set[str], list[dict[str, str]]],
    ) -> list[dict[str, str]]:
        node_ids, _ = seen_ids
        if not isinstance(edges, list):
            raise AIValidationError(f"{field_path}.edges must be a list.")

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

    @staticmethod
    def _migrate_diagram_keys(diagrams: dict[str, Any]) -> dict[str, Any]:
        migrated = dict(diagrams)
        for legacy_key, current_key in LEGACY_DIAGRAM_KEY_ALIASES.items():
            if legacy_key in migrated and current_key not in migrated:
                migrated[current_key] = migrated.pop(legacy_key)
            elif legacy_key in migrated:
                migrated.pop(legacy_key, None)
        return migrated
