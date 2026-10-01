from langgraph.checkpoint.memory import InMemorySaver


def create_memory():
    """
    Create the checkpoint memory used by the Case 07 workflow.

    The current implementation uses in-memory checkpoint storage.
    Production deployment should replace this with durable external
    persistence.
    """
    return InMemorySaver()


case_07_memory = create_memory()
