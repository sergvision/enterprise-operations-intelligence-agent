from typing import TypedDict


class Case07ProductionState(TypedDict, total=False):
    messages: list

    operational_request: str
    service_name: str
    investigation_plan: str

    service_verification: str
    service_status: str
    incident_evidence: str
    knowledge_evidence: str

    assessment: str
    final_response: str

    evidence_gaps: list[str]
    next_evidence_source: str
    evidence_validation_errors: list[str]

    human_review_required: bool
    human_review_reason: str
    human_review_status: str
    human_decision: str
    recovery_attempts: int
    recovery_limit_reached: bool
