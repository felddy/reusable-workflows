"""Fixture library exercised by python-build.yml on every pull request.

The content is deliberately small but real: shields.io color banding for
percentage badges, mirroring the bands the coverage-badge job uses.
"""

BANDS = [
    (95.0, "brightgreen"),
    (85.0, "green"),
    (70.0, "yellow"),
    (50.0, "orange"),
    (0.0, "red"),
]


def badge_color(percent: float) -> str:
    """Return the shields.io color band for a coverage percentage."""
    if not 0.0 <= percent <= 100.0:
        raise ValueError(f"percentage out of range: {percent}")
    return next(color for floor, color in BANDS if percent >= floor)


def badge_message(percent: float) -> str:
    """Return the badge message text for a coverage percentage."""
    badge_color(percent)
    return f"{percent:.0f}%"
