from typing import Literal, TypedDict


class MedicationReconciliation(TypedDict):
    total_requests: int
    administered: int
    status: Literal["complete", "incomplete"]


def calculate_medication_reconciliation(
    medication_requests: list[dict], medication_administrations: list[dict]
) -> MedicationReconciliation:
    """Calculate medication reconciliation status for an encounter."""
    total_requests = len(medication_requests)
    administered = len(medication_administrations)

    if total_requests == 0:
        status: Literal["complete", "incomplete"] = "complete"
    elif administered >= total_requests:
        status = "complete"
    else:
        status = "incomplete"

    return MedicationReconciliation(
        total_requests=total_requests,
        administered=administered,
        status=status,
    )
