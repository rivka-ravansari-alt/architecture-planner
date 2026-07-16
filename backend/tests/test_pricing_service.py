"""Unit tests for Step 4 pricing orchestration."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.schemas.auth import UserOut
from app.services.pricing_service import PricingService

AWS_LAMBDA_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    requests_per_user_per_month = max(\n"
    "        0,\n"
    "        inputs.get(\"requests_per_user_per_month\", 0)\n"
    "    )\n"
    "    monthly_requests = users * requests_per_user_per_month\n"
    "    request_sku = next(sku for sku in skus if sku[\"name\"] == \"Requests\")\n"
    "    billable_requests = max(0, monthly_requests - free_tier.get(\"requests\", 0))\n"
    "    return round(\n"
    "        (billable_requests / 1_000_000) * request_sku[\"price_per_million\"],\n"
    "        2,\n"
    "    )"
)


class FakeProjectRepository:
    def __init__(self) -> None:
        self.provider_results: list[dict] = []
        self.current_step: int | None = None
        self.created_runs: list[dict] = []
        self.stale_runs: set[str] = set()
        self.next_run_id = 1

    def find_by_id(self, project_id: str):
        if project_id != "project-1":
            return None
        return {
            "id": project_id,
            "user_id": "user-1",
            "expected_users": 1000,
            "stage": "mvp",
            "requirements": {},
        }

    def get_latest_architecture_selection(self, project_id: str):
        return {
            "id": "selection-1",
            "selected": [
                {
                    "instance_id": "inst-compute-1",
                    "category_id": "compute",
                    "name": "Compute",
                    "description": "Runs application code.",
                    "reason": "Needed for APIs.",
                },
                {
                    "instance_id": "inst-compute-2",
                    "category_id": "compute",
                    "name": "Compute",
                    "description": "Second compute instance.",
                    "reason": "Background workers.",
                },
            ],
        }

    def get_latest_global_usage_model(self, project_id: str):
        return {
            "id": "model-1",
            "selection_id": "selection-1",
            "usage_model": {
                "llm": {
                    "requests_per_user_per_month": {
                        "value": 100,
                        "reason": "Typical usage.",
                    }
                },
                "static": {"users": 1000},
            },
        }

    def mark_global_usage_model_stale(self, project_id: str, model_id: str) -> None:
        pass

    def mark_pricing_run_stale(self, project_id: str, run_id: str) -> None:
        self.stale_runs.add(run_id)

    def invalidate_downstream_artifacts(self, project_id: str) -> None:
        self.stale_runs.add("run-1")

    def create_pricing_run(self, project_id: str, run: dict) -> str:
        run_id = f"run-{self.next_run_id}"
        self.next_run_id += 1
        self.created_runs.append({"id": run_id, **run})
        return run_id

    def get_pricing_run(self, project_id: str, run_id: str):
        for run in self.created_runs:
            if run["id"] == run_id:
                return {
                    "id": run_id,
                    "selection_id": run.get("selection_id", "selection-1"),
                    "usage_model_id": run.get("usage_model_id", "model-1"),
                    "stale": run_id in self.stale_runs,
                }
        if run_id == "run-1":
            return {
                "id": run_id,
                "selection_id": "selection-1",
                "usage_model_id": "model-1",
                "stale": run_id in self.stale_runs,
            }
        return None

    def save_provider_pricing_result(
        self, project_id: str, run_id: str, provider: str, result: dict
    ) -> None:
        self.provider_results.append(
            {"project_id": project_id, "run_id": run_id, "provider": provider, **result}
        )

    def list_provider_pricing_results(self, project_id: str, run_id: str):
        return [
            {
                "provider": item["provider"],
                "status": item["status"],
                "line_items": item["line_items"],
                "monthly_total": item["monthly_total"],
                "error": item.get("error"),
            }
            for item in self.provider_results
            if item["run_id"] == run_id
        ]

    def update_pricing_run(self, project_id: str, run_id: str, fields: dict) -> None:
        pass

    def set_current_step(self, project_id: str, step: int) -> None:
        self.current_step = step

    def get_latest_pricing_run(self, project_id: str):
        if not self.provider_results and not self.created_runs:
            return None
        if self.created_runs:
            latest = self.created_runs[-1]
            run_id = latest["id"]
            return {
                "id": run_id,
                "selection_id": latest.get("selection_id", "selection-1"),
                "usage_model_id": latest.get("usage_model_id", "model-1"),
                "stale": run_id in self.stale_runs,
            }
        return {
            "id": "run-1",
            "selection_id": "selection-1",
            "usage_model_id": "model-1",
            "stale": "run-1" in self.stale_runs,
        }


class FakeMappingRepository:
    def find_by_id(self, category_id: str):
        if category_id != "compute":
            return None
        return {
            "category_id": "compute",
            "providers": {
                "aws": [
                    {
                        "service_id": "aws_lambda",
                        "priority": 1,
                        "service_type": "serverless_function",
                    }
                ],
                "azure": [
                    {
                        "service_id": "azure_functions",
                        "priority": 1,
                        "service_type": "serverless_function",
                    }
                ],
                "gcp": [
                    {
                        "service_id": "gcp_cloud_functions",
                        "priority": 1,
                        "service_type": "serverless_function",
                    }
                ],
            },
        }


class FakePricingRepository:
    SERVICES = {
        "aws_lambda": {
            "service_id": "aws_lambda",
            "to_know": {
                "llm": ["requests_per_user_per_month"],
                "static": ["users"],
            },
            "skus": [{"name": "Requests", "price_per_million": 0.2}],
            "free_tier": {"requests": 1_000_000},
            "script_calculation": AWS_LAMBDA_SCRIPT,
        },
        "azure_functions": {
            "service_id": "azure_functions",
            "to_know": {
                "llm": ["requests_per_user_per_month"],
                "static": ["users"],
            },
            "skus": [{"name": "Requests", "price_per_million": 0.2}],
            "free_tier": {"requests": 1_000_000},
            "script_calculation": AWS_LAMBDA_SCRIPT,
        },
        "gcp_cloud_functions": {
            "service_id": "gcp_cloud_functions",
            "to_know": {
                "llm": ["requests_per_user_per_month"],
                "static": ["users"],
            },
            "skus": [{"name": "Requests", "price_per_million": 0.4}],
            "free_tier": {"requests": 2_000_000},
            "script_calculation": AWS_LAMBDA_SCRIPT,
        },
    }

    def find_by_id(self, service_id: str):
        return self.SERVICES.get(service_id)


def _service(user_id: str = "user-1") -> PricingService:
    return PricingService(
        FakeProjectRepository(),
        FakeMappingRepository(),
        FakePricingRepository(),
    )


def test_generate_provider_prices_each_instance_separately():
    projects = FakeProjectRepository()
    service = PricingService(
        projects, FakeMappingRepository(), FakePricingRepository()
    )
    user = UserOut(id="user-1", email="user@example.com", name="User")

    response = service.generate_provider("project-1", "aws", user)

    assert response.run_id == "run-1"
    assert response.result.status == "completed"
    assert len(response.result.line_items) == 2
    assert {item.instance_id for item in response.result.line_items} == {
        "inst-compute-1",
        "inst-compute-2",
    }
    assert response.result.monthly_total == pytest.approx(
        sum(
            item.monthly_price
            for item in response.result.line_items
            if item.status == "priced" and item.monthly_price is not None
        )
    )
    assert projects.provider_results[0]["provider"] == "aws"
    reasons_by_instance = {
        item.instance_id: item.selection_reason
        for item in response.result.line_items
    }
    assert reasons_by_instance == {
        "inst-compute-1": "Needed for APIs.",
        "inst-compute-2": "Background workers.",
    }
    for item in response.result.line_items:
        assert item.calculation_summary
        assert item.calculation_summary[-1].startswith("Price: $")


def test_generate_provider_returns_skipped_line_item_when_pricing_missing():
    class MappingWithAuth(FakeMappingRepository):
        def find_by_id(self, category_id: str):
            if category_id == "authentication":
                return {
                    "category_id": "authentication",
                    "providers": {
                        "aws": [{"service_id": "aws_cognito", "priority": 1}],
                    },
                }
            return super().find_by_id(category_id)

    class SelectionWithAuth(FakeProjectRepository):
        def get_latest_architecture_selection(self, project_id: str):
            return {
                "id": "selection-1",
                "selected": [
                    {
                        "instance_id": "inst-auth-1",
                        "category_id": "authentication",
                        "name": "Authentication",
                        "description": "User auth.",
                        "reason": "Required for sign-in.",
                    }
                ],
            }

    service = PricingService(
        SelectionWithAuth(), MappingWithAuth(), FakePricingRepository()
    )
    user = UserOut(id="user-1", email="user@example.com", name="User")

    response = service.generate_provider("project-1", "aws", user)

    assert response.result.status == "completed"
    assert len(response.result.line_items) == 1
    item = response.result.line_items[0]
    assert item.component_name == "Authentication"
    assert item.status == "skipped"
    assert item.selection_reason == "Required for sign-in."
    assert item.skip_reason is not None
    assert "aws_cognito" in item.skip_reason
    assert response.result.monthly_total == 0


AWS_COGNITO_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    authentication_methods = inputs.get(\"authentication_methods\", []) or []\n"
    "    sms_per_user = max(0, inputs.get(\"sms_verifications_per_user_per_month\", 0))\n"
    "    mau_sku = next(sku for sku in skus if sku[\"name\"] == \"Monthly Active User\")\n"
    "    sms_sku = next(sku for sku in skus if sku[\"name\"] == \"SMS Verification\")\n"
    "    free_mau = free_tier.get(\"monthly_active_users\", 0)\n"
    "    billable_mau = max(0, users - free_mau)\n"
    "    mau_cost = billable_mau * mau_sku[\"price_per_mau\"]\n"
    "    sms_cost = 0\n"
    "    if \"sms\" in authentication_methods:\n"
    "        monthly_sms = users * sms_per_user\n"
    "        sms_cost = monthly_sms * sms_sku[\"price_per_sms\"]\n"
    "    return round(mau_cost + sms_cost, 2)"
)


def test_generate_provider_refreshes_authentication_methods_for_sms_pricing():
    """Stale usage models missing authentication_methods still price SMS."""

    class MappingWithAuth(FakeMappingRepository):
        def find_by_id(self, category_id: str):
            if category_id == "authentication":
                return {
                    "category_id": "authentication",
                    "providers": {
                        "aws": [{"service_id": "aws_cognito", "priority": 1}],
                    },
                }
            return super().find_by_id(category_id)

    class ProjectWithSmsAuth(FakeProjectRepository):
        def find_by_id(self, project_id: str):
            project = super().find_by_id(project_id)
            assert project is not None
            return {
                **project,
                "expected_users": 10_000,
                "requirements": {
                    "authentication": {
                        "enabled": True,
                        "authentication_methods": ["sms", "google"],
                    }
                },
            }

        def get_latest_architecture_selection(self, project_id: str):
            return {
                "id": "selection-1",
                "selected": [
                    {
                        "instance_id": "inst-auth-1",
                        "category_id": "authentication",
                        "name": "Authentication",
                        "description": "User auth.",
                        "reason": "Required for sign-in.",
                    }
                ],
            }

        def get_latest_global_usage_model(self, project_id: str):
            return {
                "id": "model-1",
                "selection_id": "selection-1",
                "usage_model": {
                    "llm": {},
                    # Stale: generated before authentication_methods existed.
                    "static": {"users": 10_000, "stage": "mvp"},
                },
            }

    class PricingWithCognito(FakePricingRepository):
        SERVICES = {
            **FakePricingRepository.SERVICES,
            "aws_cognito": {
                "service_id": "aws_cognito",
                "to_know": {
                    "llm": ["sms_verifications_per_user_per_month"],
                    "static": ["users", "authentication_methods"],
                },
                "skus": [
                    {
                        "name": "Monthly Active User",
                        "price_per_mau": 0.015,
                    },
                    {
                        "name": "SMS Verification",
                        "price_per_sms": 0.05,
                    },
                ],
                "free_tier": {"monthly_active_users": 10_000},
                "script_calculation": AWS_COGNITO_SCRIPT,
            },
        }

    service = PricingService(
        ProjectWithSmsAuth(), MappingWithAuth(), PricingWithCognito()
    )
    user = UserOut(id="user-1", email="user@example.com", name="User")

    response = service.generate_provider("project-1", "aws", user)

    assert response.result.status == "completed"
    assert len(response.result.line_items) == 1
    item = response.result.line_items[0]
    assert item.status == "priced"
    assert item.monthly_price == 500.0
    assert any("sms" in line.lower() for line in (item.calculation_summary or []))


def test_generate_provider_rejects_unknown_provider():
    service = _service()
    user = UserOut(id="user-1", email="user@example.com", name="User")

    with pytest.raises(BadRequestError):
        service.generate_provider("project-1", "oracle", user)


def test_get_latest_pricing_returns_saved_run():
    projects = FakeProjectRepository()
    service = PricingService(
        projects, FakeMappingRepository(), FakePricingRepository()
    )
    user = UserOut(id="user-1", email="user@example.com", name="User")

    service.generate_provider("project-1", "aws", user)
    run = service.get_latest_pricing("project-1", user)

    assert run.run_id == "run-1"
    assert len(run.providers) == 3
    assert run.providers[0].status == "completed"
    assert run.providers[1].status == "pending"


def test_get_latest_pricing_requires_existing_run():
    service = _service()
    user = UserOut(id="user-1", email="user@example.com", name="User")

    with pytest.raises(NotFoundError):
        service.get_latest_pricing("project-1", user)


def test_get_latest_pricing_ignores_stale_run():
    projects = FakeProjectRepository()
    projects.stale_runs.add("run-1")
    projects.provider_results.append(
        {
            "run_id": "run-1",
            "provider": "aws",
            "status": "completed",
            "line_items": [],
            "monthly_total": 10.0,
        }
    )
    service = PricingService(
        projects, FakeMappingRepository(), FakePricingRepository()
    )
    user = UserOut(id="user-1", email="user@example.com", name="User")

    with pytest.raises(NotFoundError, match="No pricing run exists"):
        service.get_latest_pricing("project-1", user)


def test_generate_provider_creates_new_run_when_run_id_is_stale():
    projects = FakeProjectRepository()
    projects.stale_runs.add("run-1")
    service = PricingService(
        projects, FakeMappingRepository(), FakePricingRepository()
    )
    user = UserOut(id="user-1", email="user@example.com", name="User")

    response = service.generate_provider("project-1", "aws", user, run_id="run-1")

    assert response.run_id == "run-1"
    assert len(projects.created_runs) == 1
    assert projects.created_runs[0]["stale"] is False
    assert projects.created_runs[0]["selection_id"] == "selection-1"
