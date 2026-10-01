def determine_human_review(state):
    """
    Determine whether the operational investigation requires
    Human-in-the-Loop review.
    """

    service_status = str(
        state.get("service_status") or ""
    ).strip()

    incident_evidence = str(
        state.get("incident_evidence") or ""
    ).strip()

    incident_count = None

    if incident_evidence.startswith("Active incidents:"):
        raw_count = incident_evidence.split(
            ":", 1
        )[1].strip()

        try:
            incident_count = int(raw_count)
        except ValueError:
            incident_count = None

    elif incident_evidence.isdigit():
        incident_count = int(incident_evidence)

    review_required = (
        service_status in {"Degraded", "Unavailable"}
        or (
            incident_count is not None
            and incident_count > 0
        )
    )

    if review_required:
        return {
            "human_review_required": True,
            "human_review_reason": (
                "Operational evidence indicates that "
                "human review is required before final decision."
            ),
            "human_review_status": "waiting_for_human"
        }

    return {
        "human_review_required": False,
        "human_review_reason": "",
        "human_review_status": ""
    }


def human_decision_handler(state):
    """
    Validate and process the human review decision.
    """

    human_decision = str(
        state.get("human_decision") or ""
    ).lower().strip()

    if human_decision == "approved":
        return {
            "human_decision": human_decision,
            "human_review_status": "approved",
            "final_response": ""
        }

    if human_decision == "rejected":
        return {
            "human_decision": human_decision,
            "human_review_status": "rejected",
            "final_response": (
                "The human reviewer rejected the automated "
                "operational decision.\n\n"
                "Automated processing has been stopped."
            )
        }

    return {
        "human_decision": human_decision,
        "human_review_status": "invalid_decision",
        "final_response": (
            "The human decision could not be validated.\n\n"
            "Expected decision: approved or rejected."
        )
    }
