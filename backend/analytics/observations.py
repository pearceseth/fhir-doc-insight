from typing import TypedDict


class CategoryCounts(TypedDict):
    vital_signs: int
    survey: int
    laboratory: int
    procedure: int
    other: int


class EncounterTypeDensity(TypedDict):
    encounter_type: str
    counts: CategoryCounts
    total: int


def get_observation_category(observation: dict) -> str:
    """Extract the primary category from an observation."""
    categories = observation.get("category", [])
    for cat in categories:
        codings = cat.get("coding", [])
        for coding in codings:
            code = coding.get("code")
            if code in ["vital-signs", "survey", "laboratory", "procedure"]:
                return code
    return "other"


def calculate_observation_density(
    encounters: list[dict], observations_by_encounter: dict[str, list[dict]]
) -> list[EncounterTypeDensity]:
    """Calculate observation density grouped by encounter type."""
    type_data: dict[str, CategoryCounts] = {}

    for encounter in encounters:
        encounter_id = encounter.get("id")
        enc_class = encounter.get("class", {})
        encounter_type = enc_class.get("code", "unknown") if isinstance(enc_class, dict) else "unknown"

        if encounter_type not in type_data:
            type_data[encounter_type] = CategoryCounts(
                vital_signs=0, survey=0, laboratory=0, procedure=0, other=0
            )

        observations = observations_by_encounter.get(encounter_id, [])
        for obs in observations:
            category = get_observation_category(obs)
            if category == "vital-signs":
                type_data[encounter_type]["vital_signs"] += 1
            elif category == "survey":
                type_data[encounter_type]["survey"] += 1
            elif category == "laboratory":
                type_data[encounter_type]["laboratory"] += 1
            elif category == "procedure":
                type_data[encounter_type]["procedure"] += 1
            else:
                type_data[encounter_type]["other"] += 1

    result = []
    for enc_type, counts in type_data.items():
        total = sum(counts.values())
        result.append(
            EncounterTypeDensity(encounter_type=enc_type, counts=counts, total=total)
        )

    return result
