"""
Error envelope for the manifold MCP surface.

Per the audit, every MCP tool error returns the same shape:

    {"error": {
        "code": "NODE_NOT_FOUND",
        "message": "No node 'C.3' in project 'manifold'.",
        "retry": "no",
        "suggest": ["list_nodes(project_id='manifold', layer='contracts')"],
        "context": {"project_id": "manifold", "node_id": "C.3"}
    }}

Codes are frozen at v0.1.0; additions are additive, renames are breaking.
"""
from typing import Optional, Any


# ============================================================
# Stable code enum (frozen for v0.1.0)
# ============================================================

# A node was looked up that doesn't exist (or is soft-deleted and not requested).
NODE_NOT_FOUND = "NODE_NOT_FOUND"

# A project_id was used that isn't registered.
PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"

# update_node / transition_target with mismatched expected_revision_id.
STALE_REVISION = "STALE_REVISION"

# create_node references a parent that doesn't exist (or is soft-deleted).
PARENT_NOT_FOUND = "PARENT_NOT_FOUND"

# transition_target with disallowed state machine transition.
INVALID_TRANSITION = "INVALID_TRANSITION"

# import on a path that isn't a v0.2 spec dir.
NOT_A_SPEC_REPO = "NOT_A_SPEC_REPO"

# Another validation is in flight for the same project.
VALIDATION_IN_PROGRESS = "VALIDATION_IN_PROGRESS"

# A batch raised partway through; the transaction was rolled back.
BATCH_FAILED = "BATCH_FAILED"

# Reserved for future shared-deployment rate limiting.
RATE_LIMITED = "RATE_LIMITED"

# Caller forgot to pass actor, or passed an empty string.
MISSING_ACTOR = "MISSING_ACTOR"

# create_node when a node with this id already exists.
NODE_ALREADY_EXISTS = "NODE_ALREADY_EXISTS"

# Caller passed an unknown tool name to tools/call.
UNKNOWN_TOOL = "UNKNOWN_TOOL"

# Caller passed invalid arguments (wrong shape, missing required field).
INVALID_ARGUMENTS = "INVALID_ARGUMENTS"

# A read function couldn't satisfy a required prerequisite.
VALIDATION_NOT_FOUND = "VALIDATION_NOT_FOUND"

# Catch-all for unexpected exceptions in the server itself.
INTERNAL_ERROR = "INTERNAL_ERROR"


RETRY_NO = "no"
RETRY_WITH_BACKOFF = "with_backoff"
RETRY_WITH_NEW_ARGS = "with_new_args"


# ============================================================
# Envelope builder
# ============================================================

def envelope(code: str, message: str, *,
             retry: str = RETRY_NO,
             suggest: Optional[list[str]] = None,
             context: Optional[dict] = None) -> dict:
    """Build a standard error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "retry": retry,
            "suggest": list(suggest or []),
            "context": dict(context or {}),
        }
    }


# ============================================================
# Exception → envelope mapping
# ============================================================

def from_writes_exception(exc: Exception, *,
                          project_id: Optional[str] = None,
                          node_id: Optional[str] = None) -> dict:
    """Map writes.* exception types to the standard envelope.

    Unknown exceptions fall through to INTERNAL_ERROR.
    """
    from manifold import writes
    name = type(exc).__name__
    msg = str(exc)
    ctx: dict[str, Any] = {}
    if project_id:
        ctx["project_id"] = project_id
    if node_id:
        ctx["node_id"] = node_id

    if isinstance(exc, writes.NodeAlreadyExists):
        return envelope(NODE_ALREADY_EXISTS, msg, retry=RETRY_NO, context=ctx)
    if isinstance(exc, writes.NodeNotFound):
        return envelope(NODE_NOT_FOUND, msg, retry=RETRY_NO,
                         suggest=[f"list_nodes(project_id={project_id!r})"] if project_id else [],
                         context=ctx)
    if isinstance(exc, writes.ProjectNotFound):
        return envelope(PROJECT_NOT_FOUND, msg, retry=RETRY_NO,
                         suggest=["list_projects()"], context=ctx)
    if isinstance(exc, writes.StaleRevision):
        ctx["current_revision_id"] = getattr(exc, "current_revision_id", None)
        return envelope(STALE_REVISION, msg, retry=RETRY_WITH_NEW_ARGS,
                         suggest=[f"peek_node(project_id={project_id!r}, node_id={node_id!r})"]
                                 if project_id and node_id else [],
                         context=ctx)
    if isinstance(exc, writes.MissingActor):
        return envelope(MISSING_ACTOR, msg, retry=RETRY_WITH_NEW_ARGS, context=ctx)
    if isinstance(exc, writes.InvalidTransition):
        return envelope(INVALID_TRANSITION, msg, retry=RETRY_WITH_NEW_ARGS, context=ctx)
    if isinstance(exc, writes.BatchFailed):
        return envelope(BATCH_FAILED, msg, retry=RETRY_NO, context=ctx)
    if isinstance(exc, writes.WritesError):
        # Catch-all for other manifold-specific write errors.
        return envelope(INTERNAL_ERROR, f"{name}: {msg}", retry=RETRY_NO, context=ctx)

    return envelope(INTERNAL_ERROR, f"{name}: {msg}", retry=RETRY_NO, context=ctx)


def not_found_envelope(kind: str, project_id: Optional[str] = None,
                       node_id: Optional[str] = None,
                       validation_id: Optional[int] = None) -> dict:
    """Build a NOT_FOUND envelope for a read tool that returned None."""
    ctx: dict[str, Any] = {}
    if project_id is not None:
        ctx["project_id"] = project_id
    if node_id is not None:
        ctx["node_id"] = node_id
    if validation_id is not None:
        ctx["validation_id"] = validation_id

    if kind == "node":
        return envelope(NODE_NOT_FOUND, f"node not found in project {project_id!r}: {node_id!r}",
                         retry=RETRY_NO,
                         suggest=[f"list_nodes(project_id={project_id!r})",
                                  f"resolve_node(project_id={project_id!r}, query=...)"],
                         context=ctx)
    if kind == "project":
        return envelope(PROJECT_NOT_FOUND, f"project not found: {project_id!r}",
                         retry=RETRY_NO,
                         suggest=["list_projects()"], context=ctx)
    if kind == "validation":
        return envelope(VALIDATION_NOT_FOUND, f"validation not found: {validation_id}",
                         retry=RETRY_NO,
                         suggest=[f"list_validations(project_id={project_id!r})"]
                                 if project_id else ["list_validations()"],
                         context=ctx)
    return envelope(INTERNAL_ERROR, f"unknown kind: {kind}", retry=RETRY_NO, context=ctx)
