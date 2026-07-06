#!/usr/bin/env python3
"""
smoke_test.py — populate the progress-tracker DB with a realistic
multi-project, multi-phase, multi-agent scenario. Useful for verifying
the web viewer.

Resets the DB at PROGRESS_TRACKER_DB (default ~/.claude/progress.db).
Use PROGRESS_TRACKER_DB to point at a throwaway path for testing.

After running, start the web server and open localhost:7777.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))
import db


def reset_db():
    path = db.DEFAULT_DB
    for suffix in ("", "-shm", "-wal"):
        Path(str(path) + suffix).unlink(missing_ok=True)


def populate():
    conn = db.connect()

    # --- project 1: finance_analysis — a plan-orchestrator-style run, partially complete ---
    db.ensure_project(conn, "finance_analysis", label="Finance Analysis",
                      work_dir="/Users/me/code/finance_analysis")
    db.ensure_phase(conn, "finance_analysis", "P1", name="Config layer")
    db.ensure_phase(conn, "finance_analysis", "P2", name="Data pipeline")
    db.ensure_phase(conn, "finance_analysis", "P3", name="Analysis commands")

    # P1: planner done, implementer done
    db.init_dispatch(conn, "planner-P1", "finance_analysis", "P1", "planner", "sonnet",
                     ["read C1 contract", "draft phase plan", "write plan.md", "surface assumptions"])
    for i in range(4):
        db.start_item(conn, "planner-P1", i); db.done_item(conn, "planner-P1", i)
    db.finish_dispatch(conn, "planner-P1")

    db.init_dispatch(conn, "implementer-P1", "finance_analysis", "P1", "implementer", "sonnet",
                     ["scaffold src/finance/config.py", "load_user_config", "load_categories",
                      "load_merchants", "write tests", "lint + format"])
    for i in range(6):
        db.start_item(conn, "implementer-P1", i); db.done_item(conn, "implementer-P1", i)
    db.finish_dispatch(conn, "implementer-P1")

    # P2: planner done, implementer in-progress
    db.init_dispatch(conn, "planner-P2", "finance_analysis", "P2", "planner", "sonnet",
                     ["read C2 + C3 contracts", "draft pipeline plan", "write plan.md", "surface assumptions"])
    for i in range(4):
        db.start_item(conn, "planner-P2", i); db.done_item(conn, "planner-P2", i)
    db.finish_dispatch(conn, "planner-P2")

    db.init_dispatch(conn, "implementer-P2", "finance_analysis", "P2", "implementer", "sonnet",
                     ["sketch SQLite schema", "write CREATE TABLE statements",
                      "write insert helpers", "write idempotency tests",
                      "integration test against pipeline", "mark phase DONE"])
    db.start_item(conn, "implementer-P2", 0); db.done_item(conn, "implementer-P2", 0)
    db.start_item(conn, "implementer-P2", 1); db.done_item(conn, "implementer-P2", 1)
    db.start_item(conn, "implementer-P2", 2)  # in-progress

    # P3: planner blocked — contract drift
    db.init_dispatch(conn, "planner-P3", "finance_analysis", "P3", "planner", "opus",
                     ["read C2 at expected version", "discover contract drift", "draft plan", "write plan.md", "return"])
    db.start_item(conn, "planner-P3", 0); db.done_item(conn, "planner-P3", 0)
    db.start_item(conn, "planner-P3", 1)
    db.block_dispatch(conn, "planner-P3",
                      "C2 producer bumped version 0.2.0 → 0.3.0 mid-dispatch; re-dispatch needed")

    # --- project 2: auth-service — earlier stage, halted dispatch ---
    db.ensure_project(conn, "auth-service", label="Auth Service",
                      work_dir="/Users/me/code/auth-service")
    db.ensure_phase(conn, "auth-service", "P1", name="Password verifier")
    db.ensure_phase(conn, "auth-service", "P2", name="Token issuer")

    db.init_dispatch(conn, "planner-A1", "auth-service", "P1", "planner", "sonnet",
                     ["read K1 contract", "draft plan", "write plan.md"])
    for i in range(3):
        db.start_item(conn, "planner-A1", i); db.done_item(conn, "planner-A1", i)
    db.finish_dispatch(conn, "planner-A1")

    db.init_dispatch(conn, "implementer-A1", "auth-service", "P1", "implementer", "sonnet",
                     ["scaffold src/auth/", "argon2id verifier", "constant-time test",
                      "rate limiter", "locked-account state machine", "integration tests"])
    db.start_item(conn, "implementer-A1", 0); db.done_item(conn, "implementer-A1", 0)
    db.start_item(conn, "implementer-A1", 1); db.done_item(conn, "implementer-A1", 1)
    db.start_item(conn, "implementer-A1", 2)
    db.halt_dispatch(conn, "implementer-A1",
                     "context-budget; need re-dispatch with TestConstantTime in-progress")

    # P2 not started yet — planner pending
    db.init_dispatch(conn, "planner-A2", "auth-service", "P2", "planner", "sonnet",
                     ["read K3 contract", "draft plan", "write plan.md"])

    # --- project 3: manifold self-spec — completed ---
    db.ensure_project(conn, "manifold", label="Manifold (self-spec)",
                      work_dir="/abs/path/to/plugins/manifold/skills/manifold")
    db.ensure_phase(conn, "manifold", "spec", name="Layered spec authoring")
    db.init_dispatch(conn, "manifold-spec", "manifold", "spec", "implementer", "opus",
                     ["author L0 intent", "author L1 capabilities", "author L2 contracts",
                      "author L3 realizations", "run validate"])
    for i in range(5):
        db.start_item(conn, "manifold-spec", i); db.done_item(conn, "manifold-spec", i)
    db.finish_dispatch(conn, "manifold-spec")

    conn.close()


def main():
    print(f"populating {db.DEFAULT_DB}...")
    reset_db()
    populate()
    print(f"OK — three projects, six phases, eight dispatches written.")
    print(f"start the viewer:")
    print(f"  python3 {Path(__file__).resolve().parent.parent / 'server' / 'web_server.py'}")
    print(f"then open http://127.0.0.1:7777/")


if __name__ == "__main__":
    main()
