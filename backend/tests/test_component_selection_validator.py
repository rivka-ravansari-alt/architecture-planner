import pytest

from app.core.exceptions import AIValidationError
from app.schemas.component_selection import ComponentDecision, ComponentSelectionResult
from app.validators.component_selection_validator import validate_against_categories

CATEGORY_IDS = ("compute", "api", "authentication")


def test_rejects_requirement_keys_used_as_category_ids():
    result = ComponentSelectionResult(
        selected=[
            ComponentDecision(id="compute", reason="Needed."),
            ComponentDecision(id="background_processing", reason="Needed."),
        ],
        excluded=[ComponentDecision(id="api", reason="Not needed.")],
    )

    with pytest.raises(AIValidationError, match="unknown category ids: background_processing"):
        validate_against_categories(result, CATEGORY_IDS)
