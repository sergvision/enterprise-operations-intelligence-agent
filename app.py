
from pathlib import Path
import sys
import uuid
from langgraph.types import Command

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import src.graph as graph_module


def _case07_result_payload(result: dict, thread_id: str) -> dict:
    interrupt_payload = None

    if "__interrupt__" in result:
        interrupts = result.get("__interrupt__") or []
        if interrupts:
            interrupt_payload = interrupts[0].value

    return {
        "thread_id": thread_id,
        "service_name": result.get("service_name"),
        "service_status": result.get("service_status"),
        "incident_evidence": result.get("incident_evidence"),
        "knowledge_evidence": result.get("knowledge_evidence"),
        "evidence_gaps": result.get("evidence_gaps", []),
        "evidence_validation_errors": result.get(
            "evidence_validation_errors", []
        ),
        "human_review_required": interrupt_payload is not None,
        "human_review_status": result.get("human_review_status", ""),
        "human_review": interrupt_payload,
        "human_decision": result.get("human_decision", ""),
        "assessment": result.get("assessment"),
        "final_response": result.get("final_response"),
        "messages": result.get("messages", []),
    }


def run_case07_portal_request(
    user_message: str,
    thread_id: str | None = None
) -> dict:
    if not isinstance(user_message, str):
        raise TypeError("user_message must be a string.")

    user_message = user_message.strip()

    if not user_message:
        raise ValueError("user_message cannot be empty.")

    if thread_id is None:
        thread_id = f"portal-{uuid.uuid4()}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = graph_module.case_07_graph.invoke(
        {"operational_request": user_message},
        config
    )

    payload = _case07_result_payload(result, thread_id)
    payload["user_message"] = user_message

    return payload


def run_case07_human_decision(
    thread_id: str,
    decision: str
) -> dict:
    if not isinstance(thread_id, str):
        raise TypeError("thread_id must be a string.")

    thread_id = thread_id.strip()

    if not thread_id:
        raise ValueError("thread_id cannot be empty.")

    if not isinstance(decision, str):
        raise TypeError("decision must be a string.")

    decision = decision.strip().lower()

    if not decision:
        raise ValueError("decision cannot be empty.")

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = graph_module.case_07_graph.invoke(
        Command(resume=decision),
        config
    )

    payload = _case07_result_payload(
        result,
        thread_id
    )

    messages = result.get("messages", [])

    if messages:
        payload["user_message"] = messages[0]

    else:
        payload["user_message"] = ""

    payload["human_decision"] = decision

    return payload


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description=(
            "Message submitted to the "
            "Case 07 AI Assistant."
        )
    )

    thread_id: str | None = Field(
        default=None,
        description=(
            "Conversation thread identifier."
        )
    )


class HumanDecisionRequest(BaseModel):
    thread_id: str = Field(
        ...,
        description="Conversation thread identifier."
    )
    decision: str = Field(
        ...,
        description="Human decision: approved or rejected."
    )


class ChatResponse(BaseModel):
    thread_id: str
    user_message: str
    service_name: str | None
    service_status: str | None
    incident_evidence: str | None
    knowledge_evidence: str | None
    evidence_gaps: list
    evidence_validation_errors: list
    human_review_required: bool
    human_review_status: str
    human_review: dict | None
    human_decision: str
    assessment: str | None
    final_response: str | None
    messages: list


app = FastAPI(
    title=(
        "Case 07 - Enterprise Operations "
        "Intelligence Agent"
    ),
    description=(
        "Communication Portal API for the "
        "Enterprise Operations Intelligence Agent."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": (
            "Case 07 - Enterprise Operations "
            "Intelligence Agent"
        ),
        "service": "Communication Portal API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "agent": "available",
        "graph": "canonical",
    }


@app.post(
    "/human-decision",
    response_model=ChatResponse
)
def human_decision(request: HumanDecisionRequest):
    try:
        return run_case07_human_decision(
            thread_id=request.thread_id,
            decision=request.decision,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Case 07 human decision failed: "
                f"{exc}"
            )
        )


@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    try:
        return run_case07_portal_request(
            user_message=request.message,
            thread_id=request.thread_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Case 07 Agent execution failed: "
                f"{exc}"
            )
        )
