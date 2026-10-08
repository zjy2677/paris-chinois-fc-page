"""Validation and authorization coverage for player attributes."""

import pytest
from app.players.schemas import AttributeInput
from pydantic import ValidationError


@pytest.mark.parametrize("level", [0, 6, -1, 1.5, True, "3", None])
def test_invalid_level(level):
    with pytest.raises(ValidationError):
        AttributeInput(label="Passing", kind="strength", level=level)


@pytest.mark.parametrize("level", range(1, 6))
def test_valid_levels_and_trim(level):
    tag = AttributeInput(label="  Passing  ", kind="strength", level=level)
    assert tag.label == "Passing"
    assert tag.level == level


@pytest.mark.parametrize(
    "changes", [{"label": "   "}, {"label": "x" * 81}, {"kind": "other"}, {"player_id": "ignored"}]
)
def test_invalid_attribute(changes):
    with pytest.raises(ValidationError):
        AttributeInput(**({"label": "Passing", "kind": "strength", "level": 3} | changes))
