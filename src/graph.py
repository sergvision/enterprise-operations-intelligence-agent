import re

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from .state import Case07ProductionState
from .hitl import (
    determine_human_review,
    human_decision_handler,
)
from .memory import create_memory
from .validation import (
    detect_evidence_gaps,
    validate_evidence_quality,
)
from .tools import (
    lookup_service,
    check_service_status,
    get_incident_count,
    search_knowledge_base,
)


KNOWN_SERVICES = {
    "authentication",
    "database",
    "email",
    "payment",
    "api",
}


def identify_service_deterministically(
    operational_request: str
) -> str:
    """
    Identify an explicitly mentioned enterprise service.
    """

    request = (
        operational_request
        .lower()
        .strip()
    )

    service_aliases = {
        "authentication": [
            "authentication service",
            "authentication"
        ],
        "database": [
            "database service",
            "database"
        ],
        "email": [
            "email service",
            "email"
        ],
        "payment": [
            "payment service",
            "payment"
        ],
        "api": [
            "api service",
            "api"
        ]
    }

    for service_name, aliases in service_aliases.items():
        for alias in aliases:
            if alias in request:
                return service_name

    match = re.search(
        r"\b([a-z0-9_-]+)\s+service\b",
        request
    )

    if match:
        return match.group(1)

    return ""


def conversation_message_history_node(
    state: Case07ProductionState
) -> dict:
    """
    Record the current operational request in the
    conversation message history.

    The history is kept as a simple list so the current
    Case 07 state model remains deterministic and explicit.
    """

    operational_request = state.get(
        "operational_request",
        ""
    )

    existing_messages = list(
        state.get(
            "messages",
            []
        )
    )

    if operational_request:
        existing_messages.append(
            operational_request
        )

    return {
        "messages": existing_messages
    }


def identify_service_with_context(
    operational_request: str,
    previous_service: str = ""
) -> str:
    request = (
        operational_request
        .lower()
        .strip()
    )

    previous_service = (
        previous_service
        .lower()
        .strip()
    )

    # Explicit references to the previous service/system.
    explicit_context_patterns = [
        r"\bsame service\b",
        r"\bsame system\b",
        r"\bthis service\b",
        r"\bthis system\b",
        r"\bthe same one\b",
        r"\bthe service\b",
        r"\bthe system\b",
    ]

    # Contextual follow-up questions that depend
    # on the previous operational investigation.
    contextual_follow_up_patterns = [
        r"\bwhat evidence\b",
        r"\bwhy is this happening\b",
        r"\bwhat should .*review next\b",
        r"\bwhat evidence do we have\b",
        r"\bwhat supports this assessment\b",
        r"\bwhy is this\b",
        r"\bwhat caused this\b",
        r"\bwhat should we review\b",
    ]

    has_explicit_context = any(
        re.search(
            pattern,
            request
        )
        for pattern in explicit_context_patterns
    )

    has_contextual_follow_up = any(
        re.search(
            pattern,
            request
        )
        for pattern in contextual_follow_up_patterns
    )

    if (
        previous_service
        and (
            has_explicit_context
            or has_contextual_follow_up
        )
    ):
        return previous_service

    return identify_service_deterministically(
        operational_request
    )


def identify_service_node(
    state: Case07ProductionState
) -> dict:
    operational_request = state.get(
        "operational_request",
        ""
    )

    previous_service = state.get(
        "service_name",
        ""
    )

    service_name = identify_service_with_context(
        operational_request,
        previous_service
    )

    return {
        "service_name": service_name
    }


def verify_service_node(
    state: Case07ProductionState
) -> dict:
    service_name = state.get(
        "service_name",
        ""
    )

    verification = lookup_service.invoke(
        {
            "service_name": service_name
        }
    )

    return {
        "service_verification": verification
    }


def check_service_status_node(
    state: Case07ProductionState
) -> dict:
    service_name = state.get(
        "service_name",
        ""
    )

    status = check_service_status.invoke(
        {
            "service_name": service_name
        }
    )

    return {
        "service_status": status
    }


def collect_incident_evidence_node(
    state: Case07ProductionState
) -> dict:
    service_name = state.get(
        "service_name",
        ""
    )

    incident_evidence = get_incident_count.invoke(
        {
            "service_name": service_name
        }
    )

    return {
        "incident_evidence": incident_evidence
    }


def search_knowledge_evidence_node(
    state: Case07ProductionState
) -> dict:
    service_name = state.get(
        "service_name",
        ""
    )

    knowledge_evidence = search_knowledge_base.invoke(
        {
            "service_name": service_name
        }
    )

    return {
        "knowledge_evidence": knowledge_evidence
    }


def create_operational_assessment(
    state: Case07ProductionState
) -> str:
    service_name = state.get(
        "service_name",
        ""
    )

    service_status = state.get(
        "service_status",
        ""
    )

    incident_evidence = state.get(
        "incident_evidence",
        ""
    )

    knowledge_evidence = state.get(
        "knowledge_evidence",
        ""
    )

    if not service_name:
        return (
            "Assessment: No enterprise service could be identified."
        )

    if "was not found" in service_status.lower():
        return (
            f"Assessment: Service '{service_name}' "
            "could not be verified in the service status system."
        )

    if "was not found" in incident_evidence.lower():
        return (
            f"Assessment: Service '{service_name}' "
            "has no available incident-management evidence."
        )

    if "No knowledge base entries" in knowledge_evidence:
        return (
            f"Assessment: Service '{service_name}' "
            "has operational evidence but no matching "
            "knowledge-base guidance."
        )

    incident_match = re.search(
        r"^\d+$",
        incident_evidence.strip()
    )

    incident_count = (
        int(incident_match.group())
        if incident_match
        else None
    )

    if service_status == "Degraded" and incident_count is not None:
        return (
            f"Assessment: Service '{service_name}' is Degraded "
            f"with {incident_count} active incident(s). "
            "Operational review is required."
        )

    if service_status == "Operational" and incident_count == 0:
        return (
            f"Assessment: Service '{service_name}' is Operational "
            "with no active incidents reported."
        )

    if incident_count is not None and incident_count > 0:
        return (
            f"Assessment: Service '{service_name}' is "
            f"{service_status} with {incident_count} "
            "active incident(s). Further investigation is required."
        )

    return (
        f"Assessment: Service '{service_name}' "
        f"has status '{service_status}'."
    )


def evidence_validation_node(state):
    evidence_gaps = detect_evidence_gaps(state)
    validation_errors = validate_evidence_quality(state)

    return {
        "evidence_gaps": evidence_gaps,
        "evidence_validation_errors": validation_errors,
    }


def operational_assessment_node(
    state: Case07ProductionState
) -> dict:
    assessment = create_operational_assessment(
        state
    )

    return {
        "assessment": assessment
    }


def create_llm_reasoning(state):
    service_name = state.get("service_name", "")
    service_verification = state.get("service_verification", "")
    service_status = state.get("service_status", "")
    incident_evidence = state.get("incident_evidence", "")
    knowledge_evidence = state.get("knowledge_evidence", "")
    assessment = state.get("assessment", "")

    prompt = f"""
You are an enterprise operations intelligence analyst.

Analyze the operational evidence below.

Service:
{service_name}

Service verification:
{service_verification}

Service status:
{service_status}

Incident evidence:
{incident_evidence}

Knowledge evidence:
{knowledge_evidence}

Deterministic assessment:
{assessment}

Produce a concise operational reasoning statement.

Rules:
1. Use only the evidence provided above.
2. Do not invent facts.
3. Do not change service status.
4. Do not change incident counts.
5. If evidence is missing or contradictory, explicitly state that.
6. Focus on operational significance and recommended investigation direction.
"""

    client = OpenAI()

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text.strip()


def llm_reasoning_node(state):
    reasoning = create_llm_reasoning(state)

    return {
        "final_response": reasoning
    }


def evidence_validation_router(state):
    """
    Route the workflow according to evidence validation results.

    Priority:
    1. Validation errors
    2. Evidence gaps
    3. Validation passed
    """

    validation_errors = state.get(
        "evidence_validation_errors",
        []
    )

    evidence_gaps = state.get(
        "evidence_gaps",
        []
    )

    if validation_errors:
        return "validation_failed"

    if evidence_gaps:
        return "evidence_incomplete"

    return "validation_passed"


def evidence_recovery_router(state):
    """
    Determine the next evidence source required
    to recover incomplete or invalid evidence.
    """

    validation_errors = state.get(
        "evidence_validation_errors",
        []
    )

    evidence_gaps = state.get(
        "evidence_gaps",
        []
    )

    if validation_errors:
        return "incident_evidence"

    if "incident_evidence" in evidence_gaps:
        return "incident_evidence"

    if "knowledge_evidence" in evidence_gaps:
        return "knowledge_evidence"

    if "service_status" in evidence_gaps:
        return "service_status"

    if "service_verification" in evidence_gaps:
        return "service_verification"

    return "no_recovery_source"


def evidence_recovery_node(state):
    """
    Select the next evidence source required
    for evidence recovery.
    """

    next_source = evidence_recovery_router(
        state
    )

    return {
        "next_evidence_source": next_source
    }


def evidence_recovery_action_node(state):
    """
    Execute the evidence recovery action selected
    by the evidence recovery router.
    """

    service_name = state.get(
        "service_name",
        ""
    )

    next_source = state.get(
        "next_evidence_source",
        ""
    )

    if next_source == "incident_evidence":
        result = get_incident_count.invoke(
            {
                "service_name": service_name
            }
        )

        return {
            "incident_evidence": result
        }

    if next_source == "knowledge_evidence":
        result = search_knowledge_base.invoke(
            {
                "service_name": service_name
            }
        )

        return {
            "knowledge_evidence": result
        }

    if next_source == "service_status":
        result = check_service_status.invoke(
            {
                "service_name": service_name
            }
        )

        return {
            "service_status": result
        }

    if next_source == "service_verification":
        result = lookup_service.invoke(
            {
                "service_name": service_name
            }
        )

        return {
            "service_verification": result
        }

    return {}


def increment_recovery_attempt_node(state):
    """
    Increment the evidence recovery attempt counter.
    """

    current_attempts = int(
        state.get(
            "recovery_attempts",
            0
        )
    )

    return {
        "recovery_attempts":
            current_attempts + 1
    }


MAX_RECOVERY_ATTEMPTS = 3


def recovery_attempt_limit_router(state):
    """
    Decide whether evidence recovery may continue.

    Recovery is allowed while the current number
    of attempts is below the configured maximum.
    """

    recovery_attempts = int(
        state.get(
            "recovery_attempts",
            0
        )
    )

    if recovery_attempts >= MAX_RECOVERY_ATTEMPTS:
        return "recovery_limit_reached"

    return "recovery_allowed"


def recovery_attempt_control_node(state):
    """
    Increment the recovery attempt counter and
    return the updated counter value.
    """

    current_attempts = int(
        state.get(
            "recovery_attempts",
            0
        )
    )

    return {
        "recovery_attempts":
            current_attempts + 1
    }


def recovery_limit_outcome_node(state):
    """
    Record that the evidence recovery limit
    has been reached.
    """

    return {
        "recovery_limit_reached": True
    }



def create_recovery_aware_assessment(
    state: Case07ProductionState
) -> str:
    """
    Combine the existing operational assessment with
    explicit recovery-limit context.
    """

    base_assessment = create_operational_assessment(
        state
    )

    recovery_limit_reached = state.get(
        "recovery_limit_reached",
        False
    )

    if recovery_limit_reached:
        return (
            f"{base_assessment} "
            "Evidence recovery reached the maximum "
            "allowed number of attempts. "
            "The available evidence may be incomplete."
        )

    return base_assessment


def recovery_limit_aware_assessment_node(
    state: Case07ProductionState
) -> dict:
    """
    Produce a recovery-aware operational assessment
    while preserving the existing evidence-based
    operational assessment.
    """

    assessment = create_recovery_aware_assessment(
        state
    )

    return {
        "assessment": assessment
    }

def case07_human_review_node(
    state: Case07ProductionState
) -> dict:
    """
    Canonical Case 07 Human-in-the-Loop review node.
    """

    review_result = determine_human_review(state)

    if not review_result.get(
        "human_review_required",
        False
    ):
        return review_result

    decision = interrupt(
        {
            "type": "human_review",
            "reason": review_result[
                "human_review_reason"
            ],
            "service_name": state.get(
                "service_name",
                ""
            ),
            "service_status": state.get(
                "service_status",
                ""
            ),
            "incident_evidence": state.get(
                "incident_evidence",
                ""
            ),
            "assessment": state.get(
                "assessment",
                ""
            ),
            "expected_decisions": [
                "approved",
                "rejected",
            ],
        }
    )

    decision_state = {
        **state,
        **review_result,
        "human_decision": str(
            decision
        ),
    }

    return human_decision_handler(
        decision_state
    )


def human_review_router(
    state: Case07ProductionState
) -> str:
    """
    Route the graph after Human-in-the-Loop review.
    """

    review_status = str(
        state.get(
            "human_review_status",
            ""
        )
    ).strip().lower()

    if review_status == "rejected":
        return "rejected"

    if review_status == "invalid_decision":
        return "invalid_decision"

    return "approved"


def create_case07_builder():
    builder = StateGraph(
        Case07ProductionState
    )

    builder.add_node(
        "conversation_message_history",
        conversation_message_history_node
    )

    builder.add_node(
        "identify_service",
        identify_service_node
    )

    builder.add_node(
        "verify_service",
        verify_service_node
    )

    builder.add_node(
        "check_service_status",
        check_service_status_node
    )

    builder.add_node(
        "collect_incident_evidence",
        collect_incident_evidence_node
    )

    builder.add_node(
        "search_knowledge_evidence",
        search_knowledge_evidence_node
    )

    builder.add_node(
        "evidence_validation",
        evidence_validation_node
    )

    builder.add_node(
        "evidence_recovery",
        evidence_recovery_node
    )

    builder.add_node(
        "recovery_attempt_control",
        recovery_attempt_control_node
    )

    builder.add_node(
        "evidence_recovery_action",
        evidence_recovery_action_node
    )

    builder.add_node(
        "recovery_limit_outcome",
        recovery_limit_outcome_node
    )

    builder.add_node(
        "recovery_limit_aware_assessment",
        recovery_limit_aware_assessment_node
    )

    builder.add_node(
        "operational_assessment",
        operational_assessment_node
    )

    builder.add_node(
        "human_review",
        case07_human_review_node
    )

    builder.add_node(
        "llm_reasoning",
        llm_reasoning_node
    )

    builder.add_edge(
        START,
        "conversation_message_history"
    )

    builder.add_edge(
        "conversation_message_history",
        "identify_service"
    )

    builder.add_edge(
        "identify_service",
        "verify_service"
    )

    builder.add_edge(
        "verify_service",
        "check_service_status"
    )

    builder.add_edge(
        "check_service_status",
        "collect_incident_evidence"
    )

    builder.add_edge(
        "collect_incident_evidence",
        "search_knowledge_evidence"
    )

    builder.add_edge(
        "search_knowledge_evidence",
        "evidence_validation"
    )

    builder.add_conditional_edges(
        "evidence_validation",
        evidence_validation_router,
        {
            "validation_passed":
                "recovery_limit_aware_assessment",
            "evidence_incomplete":
                "evidence_recovery",
            "validation_failed":
                "evidence_recovery",
        }
    )

    builder.add_edge(
        "evidence_recovery",
        "recovery_attempt_control"
    )

    builder.add_conditional_edges(
        "recovery_attempt_control",
        recovery_attempt_limit_router,
        {
            "recovery_allowed":
                "evidence_recovery_action",
            "recovery_limit_reached":
                "recovery_limit_outcome",
        }
    )

    builder.add_edge(
        "evidence_recovery_action",
        "evidence_validation"
    )

    builder.add_edge(
        "recovery_limit_outcome",
        "recovery_limit_aware_assessment"
    )

    builder.add_edge(
        "recovery_limit_aware_assessment",
        "operational_assessment"
    )

    builder.add_edge(
        "operational_assessment",
        "human_review"
    )

    builder.add_conditional_edges(
        "human_review",
        human_review_router,
        {
            "approved":
                "llm_reasoning",
            "rejected":
                END,
            "invalid_decision":
                END,
        }
    )
    builder.add_edge(
        "llm_reasoning",
        END
    )

    return builder


def build_case07_graph():
    builder = create_case07_builder()

    memory = create_memory()

    return builder.compile(
        checkpointer=memory
    )


case_07_graph = build_case07_graph()



from openai import OpenAI

# ---------------------------------------------------------
# Case 07 canonical node aliases
# ---------------------------------------------------------

service_identification_node = identify_service_node

service_verification_node = verify_service_node

service_status_node = check_service_status_node

incident_evidence_node = collect_incident_evidence_node

knowledge_evidence_node = search_knowledge_evidence_node

