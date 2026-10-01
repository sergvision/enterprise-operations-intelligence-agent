from datetime import datetime, timezone
import uuid
import json


def create_investigation_audit_record(state):
    """
    Create a structured audit record for an investigation.
    """

    return {
        "workflow": (
            "Case 07 - Enterprise Operations Intelligence Agent"
        ),
        "service_name": state.get("service_name", ""),
        "service_verification": state.get(
            "service_verification", ""
        ),
        "service_status": state.get(
            "service_status", ""
        ),
        "incident_evidence": state.get(
            "incident_evidence", ""
        ),
        "knowledge_evidence_present": bool(
            state.get("knowledge_evidence", "")
        ),
        "evidence_validation_errors": state.get(
            "evidence_validation_errors", []
        ),
        "human_review_status": state.get(
            "human_review_status", ""
        ),
        "human_decision": state.get(
            "human_decision", ""
        )
    }


def enrich_audit_event(audit_event):
    """
    Add a unique event ID and UTC timestamp.
    """

    enriched_event = dict(audit_event)

    enriched_event["event_id"] = str(uuid.uuid4())

    enriched_event["timestamp"] = (
        datetime.now(timezone.utc).isoformat()
    )

    return enriched_event


def create_enterprise_audit_event(audit_record):
    """
    Safely create an enriched enterprise audit event.
    """

    if audit_record is None:
        audit_record = {}

    event = create_investigation_audit_record(
        audit_record
    )

    return enrich_audit_event(event)


def serialize_audit_event(audit_event):
    """
    Serialize an audit event to JSON.
    """

    return json.dumps(
        audit_event,
        ensure_ascii=False,
        sort_keys=True
    )


def deserialize_audit_event(serialized_event):
    """
    Restore an audit event from JSON.
    """

    return json.loads(serialized_event)
