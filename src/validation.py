VALID_STATUS_VALUES = {
    "Operational",
    "Degraded",
    "Unavailable"
}


def detect_evidence_gaps(state):
    """
    Identify evidence that is still missing from the investigation state.
    """

    evidence_gaps = []

    if not state.get("service_verification"):
        evidence_gaps.append("service_verification")

    if not state.get("service_status"):
        evidence_gaps.append("service_status")

    if not state.get("incident_evidence"):
        evidence_gaps.append("incident_evidence")

    if not state.get("knowledge_evidence"):
        evidence_gaps.append("knowledge_evidence")

    return evidence_gaps


def validate_evidence_quality(state):
    """
    Validate the structure and format of collected evidence.
    """

    validation_errors = []

    service_status = state.get("service_status", "")
    incident_evidence = state.get("incident_evidence", "")
    knowledge_evidence = state.get("knowledge_evidence", "")

    if service_status:
        status_value = service_status.strip()

        valid_status = (
            status_value in VALID_STATUS_VALUES
            or (
                status_value.startswith("Service '")
                and "was not found in the service status system."
                in status_value
            )
        )

        if not valid_status:
            validation_errors.append(
                "service_status contains an unexpected tool response."
            )

    if incident_evidence:
        incident_value = incident_evidence.strip()

        if incident_value.isdigit():
            pass
        elif incident_value.startswith("Service '") and "was not found" in incident_value:
            pass
        else:
            validation_errors.append(
                "incident_evidence has an unexpected format."
            )

    if (
        knowledge_evidence
        and "Topic:" not in knowledge_evidence
        and "No knowledge base entries" not in knowledge_evidence
    ):
        validation_errors.append(
            "knowledge_evidence has an unexpected format."
        )

    return validation_errors
