"""Enforces diagram visibility rules by architecture detail level."""

from __future__ import annotations

import re
from typing import Any

from app.config.params import (
    COMPONENT_TYPE_ALIASES,
    DEFAULT_DIAGRAM_TITLES,
    DIAGRAM_EXCLUDED_TYPES,
    DIAGRAM_KEYS,
    MAIN_ARCHITECTURE_COMPONENT_TYPES,
    SUPPORTING_INFRASTRUCTURE_COMPONENT_TYPES,
)


class DiagramRulesService:
    def apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        components = payload.get("components")
        diagrams = payload.get("diagrams")
        if not isinstance(components, list) or not isinstance(diagrams, dict):
            return payload

        diagrams = self._migrate_diagram_keys(diagrams)
        payload["diagrams"] = diagrams

        component_index = self._build_component_index(components)
        normalized: dict[str, dict[str, Any]] = {}

        for key in DIAGRAM_KEYS:
            diagram = diagrams.get(key)
            if not isinstance(diagram, dict):
                continue
            if key == "technical_architecture":
                normalized[key] = self._prepare_technical_diagram(diagram, component_index)
            else:
                excluded = DIAGRAM_EXCLUDED_TYPES.get(key, frozenset())
                normalized[key] = self._filter_diagram(diagram, component_index, excluded)

        payload["diagrams"] = self._ensure_all_diagrams(normalized, component_index)
        return payload

    def _ensure_all_diagrams(
        self,
        diagrams: dict[str, dict[str, Any]],
        component_index: dict[str, str],
    ) -> dict[str, dict[str, Any]]:
        result = dict(diagrams)
        fallback = (
            result.get("technical_architecture")
            or result.get("high_level")
            or result.get("system_flow")
        )
        if not fallback:
            return result

        for key in DIAGRAM_KEYS:
            if key in result:
                continue
            title = DEFAULT_DIAGRAM_TITLES[key]
            clone = {
                "title": title,
                "nodes": [dict(node) for node in fallback.get("nodes", [])],
                "edges": [dict(edge) for edge in fallback.get("edges", [])],
            }
            if key == "technical_architecture":
                result[key] = self._prepare_technical_diagram(clone, component_index)
            else:
                excluded = DIAGRAM_EXCLUDED_TYPES.get(key, frozenset())
                result[key] = self._filter_diagram(clone, component_index, excluded)
        return result

    def _prepare_technical_diagram(
        self,
        diagram: dict[str, Any],
        component_index: dict[str, str],
    ) -> dict[str, Any]:
        nodes: list[dict[str, str]] = []
        for node in diagram.get("nodes", []):
            if not isinstance(node, dict):
                continue
            normalized = dict(node)
            component_type = self._resolve_node_type(normalized, component_index)
            if (
                component_type in SUPPORTING_INFRASTRUCTURE_COMPONENT_TYPES
                and not normalized.get("group")
            ):
                normalized["group"] = "operations"
            nodes.append(normalized)

        edges = self._filter_edges(diagram.get("edges", []), {node["id"] for node in nodes})
        return {
            "title": str(diagram.get("title") or DEFAULT_DIAGRAM_TITLES["technical_architecture"]).strip(),
            "nodes": nodes,
            "edges": edges,
        }

    def _filter_diagram(
        self,
        diagram: dict[str, Any],
        component_index: dict[str, str],
        excluded_types: frozenset[str],
    ) -> dict[str, Any]:
        kept_nodes: list[dict[str, str]] = []
        kept_ids: set[str] = set()

        for node in diagram.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = str(node.get("id", "")).strip()
            if not node_id:
                continue
            component_type = self._resolve_node_type(node, component_index)
            if component_type in excluded_types:
                continue
            kept_nodes.append(dict(node))
            kept_ids.add(node_id)

        edges = self._filter_edges(diagram.get("edges", []), kept_ids)
        return {
            "title": str(diagram.get("title") or "").strip() or DEFAULT_DIAGRAM_TITLES.get("high_level", ""),
            "nodes": kept_nodes,
            "edges": edges,
        }

    def _filter_edges(self, edges: Any, kept_ids: set[str]) -> list[dict[str, str]]:
        if not isinstance(edges, list):
            return []
        filtered: list[dict[str, str]] = []
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = str(edge.get("source", "")).strip()
            target = str(edge.get("target", "")).strip()
            if source not in kept_ids or target not in kept_ids:
                continue
            normalized: dict[str, str] = {"source": source, "target": target}
            label = edge.get("label")
            if label is not None and str(label).strip():
                normalized["label"] = str(label).strip()
            filtered.append(normalized)
        return filtered

    def _build_component_index(self, components: list[dict[str, Any]]) -> dict[str, str]:
        index: dict[str, str] = {}
        for component in components:
            if not isinstance(component, dict):
                continue
            component_type = self._normalize_type(str(component.get("type", "")).strip().lower())
            name = str(component.get("name", "")).strip().lower()
            if name:
                index[name] = component_type
            slug = self._slugify(name)
            if slug:
                index[slug] = component_type
        return index

    def _resolve_node_type(self, node: dict[str, Any], component_index: dict[str, str]) -> str:
        explicit = node.get("type")
        if explicit is not None:
            return self._normalize_type(str(explicit).strip().lower())

        node_id = str(node.get("id", "")).strip().lower()
        node_name = str(node.get("name", "")).strip().lower()
        for key in (node_id, node_name, self._slugify(node_name), self._slugify(node_id)):
            if key and key in component_index:
                return component_index[key]
        return self._infer_type_from_name(node_name or node_id)

    @staticmethod
    def _normalize_type(component_type: str) -> str:
        if not component_type:
            return ""
        return COMPONENT_TYPE_ALIASES.get(component_type, component_type)

    @staticmethod
    def _slugify(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    @staticmethod
    def _infer_type_from_name(name: str) -> str:
        if not name:
            return ""
        if re.search(r"\b(end\s+)?user\b", name) or name == "user":
            return "user"
        if "admin" in name and "panel" in name:
            return "admin_panel"
        if "mobile" in name:
            return "mobile_app"
        if "cdn" in name or "content delivery" in name:
            return "cdn"
        if "load balancer" in name or "load balancing" in name:
            return "load_balancer"
        if "api gateway" in name or name == "api" or "api layer" in name:
            return "api_gateway"
        if "secret" in name or "vault" in name or "key management" in name:
            return "secrets"
        if "config" in name or "parameter store" in name:
            return "config"
        if "monitor" in name or "observability" in name or "metrics" in name:
            return "monitoring"
        if "log" in name:
            return "logging"
        if "trace" in name or "tracing" in name:
            return "tracing"
        if "alert" in name or "on-call" in name or "on call" in name:
            return "alerting"
        if "cache" in name and "cdn" not in name:
            return "cache"
        if "search" in name or "elasticsearch" in name or "opensearch" in name:
            return "search"
        if "queue" in name:
            return "queue"
        if "worker" in name or "background" in name:
            return "worker"
        if "database" in name or "data store" in name:
            return "database"
        if "object storage" in name or "blob" in name or "file storage" in name:
            return "object_storage"
        if "payment" in name or "billing" in name or "stripe" in name:
            return "payment"
        if "notification" in name or "push" in name:
            return "notification"
        if "analytic" in name or "dashboard" in name or "report" in name:
            return "analytics"
        if "ai" in name or "llm" in name or "openai" in name or "bedrock" in name:
            return "ai_provider"
        if "external" in name or "third-party" in name or "third party" in name:
            return "external_api"
        if "web" in name or "client" in name or "frontend" in name:
            return "web_app"
        if "service" in name and "api" not in name:
            return "service"
        if name in MAIN_ARCHITECTURE_COMPONENT_TYPES:
            return name
        return ""

    @staticmethod
    def _migrate_diagram_keys(diagrams: dict[str, Any]) -> dict[str, Any]:
        from app.config.params import LEGACY_DIAGRAM_KEY_ALIASES

        migrated = dict(diagrams)
        for legacy_key, current_key in LEGACY_DIAGRAM_KEY_ALIASES.items():
            if legacy_key in migrated and current_key not in migrated:
                migrated[current_key] = migrated.pop(legacy_key)
            elif legacy_key in migrated:
                migrated.pop(legacy_key, None)
        return migrated
