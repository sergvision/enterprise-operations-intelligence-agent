# Case 07 · Enterprise Operations Intelligence Agent

Stateful Agentic AI system for enterprise operational investigation,
evidence validation and Human-in-the-Loop decision support.

## Current recovery state

This package reconstructs the project from the uploaded
`05_LangGraph_Enterprise_AI_Service_Operations.ipynb` through
STEP 861.

The canonical graph includes controlled evidence recovery,
recovery-attempt limits, recovery-limit-aware assessment and
LLM reasoning.

## Core stack

- Python
- LangGraph
- OpenAI API
- FastAPI
- Uvicorn
- Gradio
- Pydantic

## Security

Authentication and authorization are not yet implemented.
Do not expose the educational deployment publicly as a production
service until appropriate security controls are added.

## Important

The generated `.env.example` contains no real credential.
Never commit a real OpenAI API key.
