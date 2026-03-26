from typing import TypedDict


REQUIRED_CATEGORIES = ["vital-signs", "survey", "laboratory", "procedure"]


class CompletenessScore(TypedDict):
    score: float
    missing_categories: list[str]
    present_categories: list[str]


def calculate_completeness(observations: list[dict]) -> CompletenessScore:
    """Calculate documentation completeness based on observation categories present."""
    present = set()

    for obs in observations:
        categories = obs.get("category", [])
        for cat in categories:
            codings = cat.get("coding", [])
            for coding in codings:
                code = coding.get("code")
                if code:
                    present.add(code)

    present_categories = [c for c in REQUIRED_CATEGORIES if c in present]
    missing_categories = [c for c in REQUIRED_CATEGORIES if c not in present]

    score = len(present_categories) / len(REQUIRED_CATEGORIES) if REQUIRED_CATEGORIES else 0.0

    return CompletenessScore(
        score=score,
        missing_categories=missing_categories,
        present_categories=present_categories,
    )
