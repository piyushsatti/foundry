"""node_ref URI helpers — project_id/node_id (L23)."""


def format_node_ref(project_id: str, node_id: str) -> str:
    return f"{project_id}/{node_id}"


def parse_node_ref(ref: str) -> tuple[str, str]:
    """Parse `project_id/node_id`. Rejects bare node_id."""
    ref = (ref or "").strip()
    if not ref or "/" not in ref:
        raise ValueError(
            f"node_ref must be project_id/node_id, got {ref!r}"
        )
    project_id, node_id = ref.split("/", 1)
    project_id = project_id.strip()
    node_id = node_id.strip()
    if not project_id or not node_id:
        raise ValueError(
            f"node_ref must be project_id/node_id, got {ref!r}"
        )
    return project_id, node_id
