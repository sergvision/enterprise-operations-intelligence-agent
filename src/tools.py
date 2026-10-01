from langchain_core.tools import tool


SERVICE_REGISTRY = {
    "email": {
        "status": "Registered",
        "owner": "Messaging Operations"
    },
    "database": {
        "status": "Registered",
        "owner": "Data Platform Operations"
    },
    "authentication": {
        "status": "Registered",
        "owner": "Identity Operations"
    },
    "payment": {
        "status": "Registered",
        "owner": "Payment Operations"
    },
    "api": {
        "status": "Registered",
        "owner": "API Platform Operations"
    }
}


SERVICE_STATUS = {
    "email": "Operational",
    "database": "Operational",
    "authentication": "Degraded",
    "payment": "Operational",
    "api": "Operational"
}


INCIDENT_COUNTS = {
    "email": 0,
    "database": 1,
    "authentication": 3,
    "payment": 0,
    "api": 2
}


KNOWLEDGE_BASE = {
    "authentication": [
        {
            "topic": "Authentication incidents",
            "content": (
                "Authentication incidents should be investigated using "
                "incident records, affected-user scope, authentication "
                "logs, recent configuration changes, and dependency health."
            )
        },
        {
            "topic": "Authentication escalation",
            "content": (
                "Multiple active authentication incidents should be "
                "reviewed by the Identity Operations team."
            )
        }
    ],
    "database": [
        {
            "topic": "Database incidents",
            "content": (
                "Database incidents should be investigated using "
                "incident records, database health metrics, "
                "recent changes, and dependency information."
            )
        }
    ],
    "email": [
        {
            "topic": "Email incidents",
            "content": (
                "Email service incidents should be investigated using "
                "message delivery metrics, incident records, "
                "recent changes, and service dependencies."
            )
        }
    ],
    "payment": [
        {
            "topic": "Payment incidents",
            "content": (
                "Payment service incidents should be investigated using "
                "transaction errors, recent changes, "
                "and dependency health."
            )
        }
    ],
    "api": [
        {
            "topic": "API incidents",
            "content": (
                "API incidents should be investigated using "
                "request errors, latency metrics, incident records, "
                "recent deployments, and dependency health."
            )
        }
    ]
}


@tool
def lookup_service(service_name: str) -> str:
    """Verify whether an enterprise service exists in the service registry."""

    service = service_name.lower().strip()

    if service not in SERVICE_REGISTRY:
        return (
            f"Service '{service_name}' was not found "
            "in the enterprise service registry."
        )

    record = SERVICE_REGISTRY[service]

    return (
        f"Service '{service}' is registered. "
        f"Operational owner: {record['owner']}."
    )


@tool
def check_service_status(service_name: str) -> str:
    """Return the current educational service status."""

    service = service_name.lower().strip()

    if service not in SERVICE_STATUS:
        return (
            f"Service '{service_name}' was not found "
            "in the service status system."
        )

    return SERVICE_STATUS[service]


@tool
def get_incident_count(service_name: str) -> str:
    """Return the number of active incidents for a service."""

    service = service_name.lower().strip()

    if service not in INCIDENT_COUNTS:
        return (
            f"Service '{service_name}' was not found "
            "in the incident management system."
        )

    return str(INCIDENT_COUNTS[service])


@tool
def search_knowledge_base(service_name: str) -> str:
    """Search the deterministic educational enterprise knowledge base."""

    service = service_name.lower().strip()

    entries = KNOWLEDGE_BASE.get(service, [])

    if not entries:
        return (
            f"No knowledge base entries were found for "
            f"service '{service_name}'."
        )

    results = []

    for entry in entries:
        results.append(
            f"Topic: {entry['topic']}\n"
            f"Content: {entry['content']}"
        )

    return "\n\n".join(results)
