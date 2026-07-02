"""Safely evaluate catalog pricing formulas against usage variables and SKUs."""

from __future__ import annotations

import ast
import operator
from typing import Any

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class FormulaEvaluationError(ValueError):
    pass


class FormulaEvaluator:
    def evaluate_formula(
        self,
        formula: dict[str, str],
        *,
        usage: dict[str, float],
        skus: dict[str, dict[str, Any]],
    ) -> tuple[float, dict[str, float]]:
        variables: dict[str, float] = dict(usage)
        for role, sku in skus.items():
            if role not in variables:
                variables[role] = self.quantity_for_role(role, usage, sku)
        variables.update(self._sku_variables(skus))
        term_costs: dict[str, float] = {}

        for key, expression in formula.items():
            if key == "total":
                continue
            term_costs[key] = self._eval_expression(expression, variables)
            variables[key] = term_costs[key]

        total_expr = formula.get("total")
        if total_expr:
            total = self._eval_expression(total_expr, variables)
        else:
            total = sum(term_costs.values())

        return max(0.0, total), term_costs

    def billable_quantity(self, quantity: float, sku: dict[str, Any]) -> tuple[float, float]:
        free_tier = sku.get("free_tier_amount")
        if free_tier is None:
            return quantity, 0.0
        try:
            free_amount = float(free_tier)
        except (TypeError, ValueError):
            return quantity, 0.0
        applied = min(quantity, free_amount)
        return max(0.0, quantity - free_amount), applied

    def quantity_for_role(
        self,
        role: str,
        usage: dict[str, float],
        sku: dict[str, Any] | None = None,
    ) -> float:
        from app.services.pricing.usage_profile import ROLE_USAGE_VARIABLE

        if role in usage:
            return usage[role]

        variable = ROLE_USAGE_VARIABLE.get(role)
        if variable and variable in usage:
            return usage[variable]

        usage_unit = str((sku or {}).get("usage_unit", "")).lower()
        description = str((sku or {}).get("description", "")).lower()
        haystack = f"{role} {description} {usage_unit}"

        if any(token in usage_unit for token in ("hour", "hr", "h")):
            return 730.0
        if any(token in usage_unit for token in ("month", "mo")):
            return 1.0
        if any(token in haystack for token in ("per request", "requests", "api call", "operation")):
            return usage.get("monthly_requests", 0.0)
        if any(token in haystack for token in ("gib", "gb", "gigabyte", "storage", "stored", "byte", "lrs", "grs", "zrs", "blob")):
            return usage.get("storage_gib", 0.0)
        if any(token in haystack for token in ("egress", "transfer", "network", "cdn", "outbound")):
            return usage.get("egress_gb", 0.0)
        if any(token in haystack for token in ("vcpu", "cpu", "core")):
            return usage.get("monthly_vcpu_hours", 0.0)
        if "memory" in haystack or "ram" in haystack:
            return usage.get("monthly_memory_gib_hours", 0.0)
        if any(token in haystack for token in ("duration", "gb-second", "gb second")):
            return usage.get("monthly_gb_seconds", 0.0)
        if any(token in haystack for token in ("execution", "invoke", "lambda", "function")):
            return usage.get("monthly_executions", 0.0)
        if any(token in haystack for token in ("token", "inference", "prediction")):
            return usage.get("monthly_tokens", 0.0)
        if any(token in haystack for token in ("auth", "mau", "identity", "signin", "login")):
            return usage.get("monthly_auth_events", 0.0)
        if any(token in haystack for token in ("host", "app", "instance", "unit", "node", "plan")):
            return 1.0

        return usage.get("monthly_requests", 0.0)

    def _sku_variables(self, skus: dict[str, dict[str, Any]]) -> dict[str, float]:
        variables: dict[str, float] = {}
        for role, sku in skus.items():
            price = sku.get("unit_price_usd")
            if price is None:
                continue
            variables[f"skus_{role}_unit_price_usd"] = float(price)
        return variables

    def _eval_expression(self, expression: str, variables: dict[str, float]) -> float:
        normalized = expression.replace("skus.", "skus_").replace(".unit_price_usd", "_unit_price_usd")
        try:
            tree = ast.parse(normalized, mode="eval")
            result = self._eval_node(tree.body, variables)
            return float(result)
        except (SyntaxError, KeyError, TypeError, ZeroDivisionError) as exc:
            raise FormulaEvaluationError(str(exc)) from exc

    def _eval_node(self, node: ast.AST, variables: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise KeyError(node.id)
            return float(variables[node.id])
        if isinstance(node, ast.BinOp):
            op = _BINARY_OPS.get(type(node.op))
            if op is None:
                raise FormulaEvaluationError(f"Unsupported operator: {type(node.op)}")
            return op(self._eval_node(node.left, variables), self._eval_node(node.right, variables))
        if isinstance(node, ast.UnaryOp):
            op = _UNARY_OPS.get(type(node.op))
            if op is None:
                raise FormulaEvaluationError(f"Unsupported unary operator: {type(node.op)}")
            return op(self._eval_node(node.operand, variables))
        raise FormulaEvaluationError(f"Unsupported expression node: {type(node)}")
