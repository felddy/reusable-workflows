"""Tests for the badge banding fixture library."""

# Third-Party Libraries
import pytest

# First-Party Libraries
from rw_dogfood import badge_color, badge_message


@pytest.mark.parametrize(
    "percent,color",
    [
        (100.0, "brightgreen"),
        (95.0, "brightgreen"),
        (94.9, "green"),
        (85.0, "green"),
        (84.9, "yellow"),
        (70.0, "yellow"),
        (69.9, "orange"),
        (50.0, "orange"),
        (49.9, "red"),
        (0.0, "red"),
    ],
)
def test_badge_color_bands(percent: float, color: str) -> None:
    """Each band boundary maps to its color."""
    assert badge_color(percent) == color


@pytest.mark.parametrize("percent", [-0.1, 100.1])
def test_badge_color_rejects_out_of_range(percent: float) -> None:
    """Out-of-range percentages raise."""
    with pytest.raises(ValueError, match="out of range"):
        badge_color(percent)


def test_badge_message_rounds() -> None:
    """Messages render as whole percentages."""
    assert badge_message(87.6) == "88%"


def test_badge_message_validates() -> None:
    """Messages reuse the range validation."""
    with pytest.raises(ValueError, match="out of range"):
        badge_message(101.0)
