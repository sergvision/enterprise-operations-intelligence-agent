
from pathlib import Path
import sys
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr
import app as portal_app


def create_session_thread():
    return f"portal-ui-{uuid.uuid4()}"


def portal_chat(message, history, thread_id):
    if not message or not message.strip():
        return history, "", thread_id, "", gr.update(visible=False)

    if not thread_id:
        thread_id = create_session_thread()

    result = portal_app.run_case07_portal_request(
        user_message=message,
        thread_id=thread_id
    )

    history = history or []

    human_review_required = result.get(
        "human_review_required",
        False
    )

    if human_review_required:
        review = result.get("human_review") or {}

        service_name = review.get("service_name", "")
        service_status = review.get("service_status", "")
        incident_evidence = review.get("incident_evidence", "")
        reason = review.get("reason", "")

        review_text = (
            "HUMAN REVIEW REQUIRED\n\n"
            f"Service: {service_name}\n"
            f"Status: {service_status}\n"
            f"Incident evidence: {incident_evidence}\n\n"
            f"Reason: {reason}\n\n"
            "Please approve or reject the operational decision."
        )

        history.append({
            "role": "user",
            "content": message
        })

        history.append({
            "role": "assistant",
            "content": review_text
        })

        return (
            history,
            "",
            thread_id,
            review_text,
            gr.update(visible=True)
        )

    assistant_response = result.get("final_response")

    if not assistant_response:
        assistant_response = (
            "The Case 07 Agent did not return a final response."
        )

    history.append({
        "role": "user",
        "content": message
    })

    history.append({
        "role": "assistant",
        "content": assistant_response
    })

    return (
        history,
        "",
        thread_id,
        "",
        gr.update(visible=False)
    )


def portal_human_decision(
    decision,
    history,
    thread_id
):
    if not thread_id:
        return (
            history,
            "",
            gr.update(visible=False)
        )

    result = portal_app.run_case07_human_decision(
        thread_id=thread_id,
        decision=decision
    )

    assistant_response = result.get("final_response")

    if not assistant_response:
        assistant_response = (
            "The Case 07 Agent did not return a final response."
        )

    history = history or []

    history.append({
        "role": "assistant",
        "content": assistant_response
    })

    return (
        history,
        "",
        gr.update(visible=False)
    )


with gr.Blocks(
    title="AI Assistant 07"
) as demo:

    gr.Markdown(
        "# AI Assistant 07"
    )

    gr.Markdown(
        "Enterprise Operations Intelligence Agent"
    )

    chatbot = gr.Chatbot(
        label="AI Assistant 07",
        height=520,    )

    message_box = gr.Textbox(
        label="Operational Request",
        placeholder="Enter your operational question...",
        lines=3
    )

    send_button = gr.Button(
        "Send"
    )

    review_box = gr.Textbox(
        label="Human Review",
        lines=8,
        interactive=False,
        visible=False
    )

    with gr.Row(
        visible=False
    ) as review_controls:

        approve_button = gr.Button(
            "Approve"
        )

        reject_button = gr.Button(
            "Reject"
        )

    thread_state = gr.State(
        value=""
    )

    send_button.click(
        portal_chat,
        inputs=[
            message_box,
            chatbot,
            thread_state
        ],
        outputs=[
            chatbot,
            message_box,
            thread_state,
            review_box,
            review_controls
        ]
    )

    message_box.submit(
        portal_chat,
        inputs=[
            message_box,
            chatbot,
            thread_state
        ],
        outputs=[
            chatbot,
            message_box,
            thread_state,
            review_box,
            review_controls
        ]
    )

    approve_button.click(
        lambda history, thread_id:
            portal_human_decision(
                "approved",
                history,
                thread_id
            ),
        inputs=[
            chatbot,
            thread_state
        ],
        outputs=[
            chatbot,
            review_box,
            review_controls
        ]
    )

    reject_button.click(
        lambda history, thread_id:
            portal_human_decision(
                "rejected",
                history,
                thread_id
            ),
        inputs=[
            chatbot,
            thread_state
        ],
        outputs=[
            chatbot,
            review_box,
            review_controls
        ]
    )


if __name__ == "__main__":
    demo.launch(share=True)

