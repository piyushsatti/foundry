"""
manifold CLI dispatch.

Subcommands: import, show, edit, snapshot, dump, restore, serve, status,
export, validate, next-leaves, spec-audit, drift-report, version, config.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _actor() -> str:
    try:
        return f"human:{os.getlogin()}"
    except OSError:
        return f"human:{os.environ.get('USER', 'unknown')}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="manifold",
        description="manifold — DB-canonical specification framework.",
    )
    parser.add_argument("--db", default=None,
                         help="Path to the manifold DB (overrides MANIFOLD_DB envvar).")
    parser.add_argument(
        "--idea", default=None,
        choices=["foundry", "chronicler", "hailey"],
        help="Use the SQLite file registered for this idea (~/.claude/<idea>.db).",
    )
    sub = parser.add_subparsers(dest="cmd")

    p_import = sub.add_parser("import", help="Import a v0.2 spec dir into the DB.")
    p_import.add_argument("repo", help="Path to repo containing specs/")
    p_import.add_argument("--project-id", default="",
                          help="Override project_id (default: spec.yaml name or repo basename).")

    p_show = sub.add_parser("show", help="Show a node's frontmatter + body as markdown.")
    p_show.add_argument("project")
    p_show.add_argument("node")

    p_edit = sub.add_parser("edit", help="Edit a node's body in $EDITOR; save creates a revision.")
    p_edit.add_argument("project")
    p_edit.add_argument("node")
    p_edit.add_argument("--reason", required=True,
                        choices=["correction", "evolution", "clarification",
                                 "refactor", "pivot", "other"],
                        help="Why this edit happened (required when body changes).")

    p_snap = sub.add_parser("snapshot", help="Take a VACUUM INTO backup to a sibling file.")

    p_dump = sub.add_parser("dump", help="Lossless NDJSON dump of all tables.")
    p_dump.add_argument("path")

    p_restore = sub.add_parser("restore", help="Rebuild the DB from a dump (DB must not exist).")
    p_restore.add_argument("path")

    p_serve = sub.add_parser("serve", help="Start the web server (HTML + JSON API).")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=7779)
    p_serve.add_argument("--verbose", action="store_true")
    p_serve.add_argument("--pidfile", default="",
                          help="Write the server PID to this file on startup; "
                               "remove on shutdown.")

    p_init_ideas = sub.add_parser(
        "init-ideas",
        help="Create separate DB files for foundry, chronicler, and hailey.",
    )
    p_init_ideas.add_argument(
        "--repo", default=None,
        help="Foundry repo root for ai-foundry project_root (default: checkout).",
    )
    p_init_ideas.add_argument(
        "--ideas", default=None,
        help="Comma-separated subset (default: foundry,chronicler,hailey).",
    )
    p_init_ideas.add_argument(
        "--force-config", action="store_true",
        help="Rewrite ~/.claude/manifold.json even if ideas registry exists.",
    )

    p_idea = sub.add_parser("idea", help="List per-idea DB paths from config.")
    idea_sub = p_idea.add_subparsers(dest="idea_cmd")
    idea_sub.add_parser("list", help="Show registered ideas and db paths.")
    p_idea_path = idea_sub.add_parser("path", help="Print db path for one idea.")
    p_idea_path.add_argument("idea_id", choices=["foundry", "chronicler", "hailey"])

    p_seed_demo = sub.add_parser(
        "seed-demo",
        help="Seed Acme Checkout demo graph (brief, diagrams, portfolio links).",
    )
    p_seed_demo.add_argument(
        "--archive-legacy", action="store_true",
        help="Archive old experimental projects (chronicler, obs-gin, etc.).",
    )
    p_seed_demo.add_argument(
        "--force", action="store_true",
        help="Re-run seed steps even if acme-checkout already exists.",
    )

    p_seed_chronicler = sub.add_parser(
        "seed-chronicler",
        help="Seed rich Chronicler showcase graph (visualization testing).",
    )
    p_seed_chronicler.add_argument(
        "--force", action="store_true",
        help="Replace existing chronicler graph (purge + re-seed).",
    )

    p_init_foundry = sub.add_parser(
        "init-foundry",
        help="Purge all projects and seed ai-foundry dogfood graph (clean slate).",
    )
    p_init_foundry.add_argument(
        "--repo", default=None,
        help="Repo root for project_root + drift (default: foundry checkout).",
    )
    p_init_foundry.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be removed without writing.",
    )

    p_stat = sub.add_parser("status",
                              help="Check if a manifold serve is running.")
    p_stat.add_argument("--pidfile", default="",
                         help="Path to the pidfile (defaults to $MANIFOLD_PIDFILE "
                              "or ~/.claude/manifold.pid).")

    p_export = sub.add_parser("export",
                                help="Export a project to an on-disk v0.2-style spec tree.")
    p_export.add_argument("project")
    p_export.add_argument("out_dir",
                            help="Output directory (must not already contain specs/).")

    p_val = sub.add_parser("validate", help="Run validation on a project.")
    p_val.add_argument("project")
    p_val.add_argument("--with-verdicts", action="store_true",
                       help="Also run verdict checks (automated/python_assertion/human).")
    p_val.add_argument("--with-targets", action="store_true",
                       help="Also run target-state checks (cycle + stale planned).")
    p_val.add_argument("--force", action="store_true",
                       help="Bypass the verdict cache; recompute every node.")

    p_next = sub.add_parser("next-leaves",
                              help="List leaf nodes ready to be worked on (target_status planned/in_progress/unset).")
    p_next.add_argument("project_id", help="Project ID to query.")
    p_next.add_argument("--layer", default=None,
                         help="Filter by layer name.")
    p_next.add_argument("--verbose", "-v", action="store_true",
                         help="Also list cross-blocked leaves and their blockers.")
    p_next.add_argument("--repo", default=None,
                         help="Checkout path; when set, run ephemeral verdict checks and "
                              "show COMPUTED column (same engine as drift-report).")

    p_audit = sub.add_parser("spec-audit",
                             help="Audit spec revision discipline (change_reason, rationale).")
    p_audit.add_argument("project_id", help="Project ID to audit.")
    p_audit.add_argument("--since", default=None,
                         help="Only include revisions on or after this ISO timestamp.")
    p_audit.add_argument("--include-other", action="store_true", default=True,
                         help="Include change_reason='other' revisions (default: on).")

    p_drift = sub.add_parser(
        "drift-report",
        help="Report spec↔code drift (verdict failures + unverified realizations).",
    )
    p_drift.add_argument("project_id", help="Project ID to report on.")
    p_drift.add_argument("--repo", default=None,
                         help="Override spec_config.project_root for checks.")
    p_drift.add_argument("--layer", default=None,
                         help="Layer to scan (default: bottom layer in spec_config).")
    p_drift.add_argument("--all-layers", action="store_true",
                         help="Scan all layers instead of bottom layer only.")
    p_drift.add_argument("--force", action="store_true",
                         help="Bypass verdict cache; recompute every node.")
    p_drift.add_argument("--format", choices=["text", "md"], default="text",
                         help="Output format (default: text).")
    p_drift.add_argument("--verbose", action="store_true",
                         help="Include satisfied nodes in text output.")

    p_portfolio = sub.add_parser(
        "portfolio-report",
        help="Roll up company themes and linked team nodes (Topic H).",
    )
    p_portfolio.add_argument("--theme", default=None,
                             help="Filter to one theme node id (e.g. T.1).")
    p_portfolio.add_argument("--format", choices=["text", "md"], default="text",
                             help="Output format (default: text).")

    p_diagram = sub.add_parser(
        "diagram-view",
        help="Bounded diagram or mindmap view-model (Topic K — Mermaid export).",
    )
    p_diagram.add_argument("project_id", help="Project ID.")
    p_diagram.add_argument(
        "--named-view", default=None,
        help="Catalog view id (blockers, mindmap-flow, …) — overrides --view/--type.",
    )
    p_diagram.add_argument(
        "--view", choices=["diagram", "mindmap"], default="diagram",
        help="View kind (default: diagram).",
    )
    p_diagram.add_argument(
        "--type", default="blockers",
        help="diagram: blockers|decomposition|trajectory; mindmap: flow|decomposition.",
    )
    p_diagram.add_argument("--focus", default=None, help="Focus node id.")
    p_diagram.add_argument("--trajectory-id", default=None,
                           help="Required when --type trajectory.")
    p_diagram.add_argument("--format", choices=["text", "md"], default="text",
                           help="Output format (default: text).")

    p_render = sub.add_parser(
        "render",
        help="Stitched narrative or table at chosen audience (Topic H).",
    )
    p_render.add_argument(
        "subject", choices=["portfolio", "project"],
        help="Render scope: portfolio theme rollup or project status-brief.",
    )
    p_render.add_argument(
        "project_id", nargs="?", default=None,
        help="Project ID (required when subject is project).",
    )
    p_render.add_argument(
        "--template", required=True,
        help="Template id: quarter-roadmap (portfolio) or status-brief (project).",
    )
    p_render.add_argument("--theme", default=None,
                          help="Filter portfolio to one theme node id.")
    p_render.add_argument("--format", choices=["md"], default="md",
                          help="Output format (v1: md only).")

    p_version = sub.add_parser("version",
                                 help="Print manifold version and install location.")

    p_config = sub.add_parser("config", help="Manage the machine-local config file.")
    config_sub = p_config.add_subparsers(dest="config_cmd")
    config_sub.add_parser("path", help="Print the resolved config file path.")
    config_sub.add_parser("show", help="Show effective settings and their sources.")
    p_config_init = config_sub.add_parser(
        "init",
        help="Write a config file seeded from current effective values.",
    )
    p_config_init.add_argument(
        "--force", action="store_true",
        help="Overwrite an existing config file.",
    )

    p_traj = sub.add_parser(
        "trajectory",
        help="Propose, preview (impact), and accept spec evolution paths (Topic J).",
    )
    traj_sub = p_traj.add_subparsers(dest="traj_cmd")

    p_traj_propose = traj_sub.add_parser(
        "propose",
        help="Create a draft trajectory (no graph writes).",
    )
    p_traj_propose.add_argument("project_id")
    p_traj_propose.add_argument(
        "--target-brief-file", required=True,
        help="Path to markdown target brief.",
    )
    p_traj_propose.add_argument(
        "--legs-file", required=True,
        help="JSON array of {leg_kind, payload, node_ref?} legs.",
    )
    p_traj_propose.add_argument(
        "--proposed-by", default=None,
        help="Actor id (default: human:$USER).",
    )

    p_traj_show = traj_sub.add_parser(
        "show",
        help="Show trajectory legs + impact preview (plan before apply).",
    )
    p_traj_show.add_argument("trajectory_id")
    p_traj_show.add_argument(
        "--legs", default=None,
        help="Comma-separated leg seq numbers to include in preview (default: all pending).",
    )
    p_traj_show.add_argument(
        "--format", choices=["json", "md"], default="md",
    )

    p_traj_accept = traj_sub.add_parser(
        "accept",
        help="Apply pending legs to the graph (accept = apply).",
    )
    p_traj_accept.add_argument("trajectory_id")
    p_traj_accept.add_argument(
        "--legs", default=None,
        help="Comma-separated leg seq numbers to accept (default: all pending).",
    )
    p_traj_accept.add_argument(
        "--actor", default=None,
        help="Actor for writes (default: human:$USER).",
    )

    p_traj_reject = traj_sub.add_parser(
        "reject",
        help="Mark a draft trajectory rejected (discard without applying legs).",
    )
    p_traj_reject.add_argument("trajectory_id")
    p_traj_reject.add_argument(
        "--actor", default=None,
        help="Actor for the rejection event (default: human:$USER).",
    )

    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 2

    if args.cmd == "trajectory" and getattr(args, "traj_cmd", None) is None:
        p_traj.print_help()
        return 2

    if args.cmd == "idea" and getattr(args, "idea_cmd", None) is None:
        p_idea.print_help()
        return 2

    # --idea / --db overrides MANIFOLD_DB for the rest of this invocation
    if args.idea and not args.db:
        from manifold import idea_registry
        os.environ["MANIFOLD_DB"] = str(idea_registry.resolve_idea_db(args.idea))
    elif args.db:
        os.environ["MANIFOLD_DB"] = args.db

    if args.cmd == "trajectory":
        return _cmd_trajectory(args)

    if args.cmd == "idea":
        return _cmd_idea(args)

    dispatch = {
        "import":       _cmd_import,
        "show":         _cmd_show,
        "edit":         _cmd_edit,
        "snapshot":     _cmd_snapshot,
        "dump":         _cmd_dump,
        "restore":      _cmd_restore,
        "serve":        _cmd_serve,
        "seed-demo":    _cmd_seed_demo,
        "seed-chronicler": _cmd_seed_chronicler,
        "init-foundry": _cmd_init_foundry,
        "init-ideas":   _cmd_init_ideas,
        "validate":     _cmd_validate,
        "status":       _cmd_status,
        "export":       _cmd_export,
        "next-leaves":  _cmd_next_leaves,
        "spec-audit":   _cmd_spec_audit,
        "drift-report": _cmd_drift_report,
        "portfolio-report": _cmd_portfolio_report,
        "diagram-view": _cmd_diagram_view,
        "render":       _cmd_render,
        "version":      _cmd_version,
        "config":       _cmd_config,
    }
    return dispatch[args.cmd](args)


def _cmd_version(args) -> int:
    """Print manifold version, schema version, and install location."""
    from pathlib import Path
    from manifold import config
    install = Path(__file__).parent.parent.resolve()
    print(f"manifold {config.MANIFOLD_VERSION}")
    print(f"  schema_version: {config.SCHEMA_VERSION}")
    print(f"  install:        {install}")
    print(f"  db (resolved):  {config.db_path()}")
    return 0


def _cmd_config(args) -> int:
    """Dispatch config sub-subcommands: path / show / init."""
    from manifold import config
    sub = getattr(args, "config_cmd", None)

    if sub == "path":
        p = config.config_path()
        exists = "exists" if p.exists() else "does not exist"
        print(f"{p}  ({exists})")
        return 0

    if sub == "show":
        settings = config.effective_settings()
        cfg_path = config.config_path()
        cfg_exists = "exists" if cfg_path.exists() else "does not exist"

        col_w = 18
        val_w = 40
        print(f"{'db_path':<{col_w}} {str(settings['db_path']['value']):<{val_w}} ({settings['db_path']['source']})")

        judge_val = settings["judge_command"]["value"] or "(unset)"
        print(f"{'judge_command':<{col_w}} {judge_val:<{val_w}} ({settings['judge_command']['source']})")
        print(f"  note: a per-project spec_config.judge_command may override this at validation time")

        print(f"{'snapshot_interval':<{col_w}} {settings['snapshot_interval']['value']:<{val_w}} ({settings['snapshot_interval']['source']})")
        print(f"{'config path':<{col_w}} {str(cfg_path):<{val_w}} ({cfg_exists})")

        unknown = settings.get("unrecognized")
        if unknown:
            print()
            print("Unrecognized keys in config file (possible typos):")
            for k, v in unknown.items():
                print(f"  {k!r}: {v!r}")
        return 0

    if sub == "init":
        p = config.config_path()
        result = config.config_init(p, force=getattr(args, "force", False))
        if result["ok"]:
            print(f"OK: config written to {result['path']}")
            return 0
        else:
            print(result["message"], file=sys.stderr)
            return 1

    # No sub-subcommand given; print help for the config group
    print("Usage: manifold config {path,show,init}")
    print("  path  — print resolved config file path")
    print("  show  — show effective settings and their sources")
    print("  init  — write config file seeded from current effective values")
    return 2


def _cmd_seed_demo(args) -> int:
    from manifold import db, demo_seed, schema

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        if args.archive_legacy:
            archived = demo_seed.archive_legacy_projects(conn)
            if archived:
                print(f"Archived {len(archived)} legacy project(s): {', '.join(archived)}")
        result = demo_seed.seed_acme_checkout_demo(
            conn, actor=_actor(), force=args.force,
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Demo: {result['status']} — {result['main_project']} ({result['nodes']['acme-checkout']} nodes)")
    print(f"Theme: portfolio/{result['theme_id']}")
    print()
    print("Open after `manifold serve`:")
    for name, url in result["urls"].items():
        print(f"  {name}: {url}")
    if result["status"] == "already_seeded" and not args.force:
        print()
        print("(Already seeded. Use --force to add missing nodes, or --archive-legacy to hide old projects.)")
    return 0


def _cmd_seed_chronicler(args) -> int:
    from manifold import chronicler_seed, db, schema

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        result = chronicler_seed.seed_chronicler(
            conn, actor=_actor(), force=args.force,
        )
        conn.commit()
    finally:
        conn.close()

    counts = result.get("node_counts") or {}
    total = result.get("total_nodes", sum(counts.values()))
    print(f"Chronicler showcase: {result['status']} — {total} nodes across {len(counts)} projects")
    for pid, n in sorted(counts.items()):
        print(f"  {pid}: {n} nodes")
    print()
    print("Visualization links (after `manifold --idea chronicler serve`):")
    for name, url in result.get("urls", {}).items():
        print(f"  {name}: {url}")
    focus = result.get("visualization_focus") or {}
    if focus:
        print()
        print("Suggested focus nodes:")
        for k, v in focus.items():
            print(f"  {k}: {v}")
    if result["status"] == "already_seeded" and not args.force:
        print()
        print("(Already seeded. Use --force to purge and rebuild the showcase graph.)")
    return 0


def _cmd_init_foundry(args) -> int:
    from pathlib import Path

    from manifold import db, foundry_seed, schema

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parents[3]

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        if args.dry_run:
            ids = [r["project_id"] for r in conn.execute("SELECT project_id FROM projects")]
            print("Would remove projects:", ", ".join(ids) or "(none)")
            print(f"Would seed: {foundry_seed.PROJECT_ID} @ {repo}")
            return 0
        result = foundry_seed.init_foundry_db(conn, repo_root=repo, actor=_actor())
        conn.commit()
    finally:
        conn.close()

    removed = result.get("removed_projects") or []
    print(f"Removed {len(removed)} project(s): {', '.join(removed) or '(none)'}")
    print(f"Seeded {result['project_id']} — {result['node_count']} nodes")
    if result.get("theme_id"):
        print(f"Theme: portfolio/{result['theme_id']}")
    print(f"Repo:  {result['repo_root']}")
    print()
    print("Open after `manifold serve`:")
    for name, url in result["urls"].items():
        print(f"  {name}: {url}")
    return 0


def _cmd_init_ideas(args) -> int:
    from pathlib import Path

    from manifold import idea_registry

    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parents[3]
    ideas = None
    if args.ideas:
        ideas = [s.strip() for s in args.ideas.split(",") if s.strip()]

    result = idea_registry.init_all_ideas(repo_root=repo, ideas=ideas, actor=_actor())
    if args.force_config:
        cfg = idea_registry.write_ideas_config(force=True)
        result["config"] = cfg

    print("Per-idea databases:")
    for item in result["ideas"]:
        print(f"  {item['idea_id']:10}  {item['db_path']}  "
              f"({item['project_id']}, {item['node_count']} nodes)")
    cfg = result.get("config") or {}
    print()
    if cfg.get("action") == "kept_existing":
        print(cfg.get("message", ""))
    else:
        print(f"Config: {cfg.get('path')}  default_idea={cfg.get('default_idea', 'foundry')}")
    print()
    print("Use one idea at a time:")
    print("  manifold --idea foundry serve")
    print("  manifold --idea chronicler next-leaves chronicler")
    print()
    print("Foundry links (after `manifold --idea foundry serve`):")
    foundry = next(i for i in result["ideas"] if i["idea_id"] == "foundry")
    for name, url in foundry.get("urls", {}).items():
        print(f"  {name}: {url}")
    return 0


def _cmd_idea(args) -> int:
    from manifold import config, idea_registry

    if args.idea_cmd == "list":
        cfg = config.load_config()
        ideas_cfg = cfg.get("ideas") or idea_registry.ideas_config_map()
        default = cfg.get("default_idea") or idea_registry.DEFAULT_IDEA
        print(f"default_idea: {default}")
        print(f"db_path (resolved): {config.db_path()}")
        print()
        for spec in idea_registry.list_ideas():
            entry = ideas_cfg.get(spec.idea_id, {})
            path = entry.get("db_path") or f"~/.claude/{spec.db_filename}"
            pid = entry.get("project_id") or spec.project_id
            print(f"  {spec.idea_id:10}  {path}  project_id={pid}")
        return 0

    if args.idea_cmd == "path":
        print(idea_registry.resolve_idea_db(args.idea_id))
        return 0

    return 2


def _cmd_serve(args) -> int:
    import sys
    from pathlib import Path
    web_pkg = Path(__file__).resolve().parents[3] / "apps" / "manifold-web"
    if str(web_pkg) not in sys.path:
        sys.path.insert(0, str(web_pkg))
    from manifold_web import web
    pidfile = (args.pidfile or os.environ.get("MANIFOLD_PIDFILE") or "").strip()
    if pidfile:
        try:
            Path(pidfile).parent.mkdir(parents=True, exist_ok=True)
            Path(pidfile).write_text(str(os.getpid()), encoding="utf-8")
        except OSError as exc:
            print(f"FAIL: could not write pidfile {pidfile}: {exc}",
                   file=sys.stderr)
            return 4

        import atexit
        def _cleanup_pidfile():
            try:
                Path(pidfile).unlink(missing_ok=True)
            except OSError:
                pass
        atexit.register(_cleanup_pidfile)
    return web.serve(host=args.host, port=args.port, verbose=args.verbose)


def _default_pidfile() -> Path:
    return Path.home() / ".claude" / "manifold.pid"


def _cmd_export(args) -> int:
    from manifold import db, schema, exporter
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        result = exporter.export_project(
            conn, args.project, Path(args.out_dir).resolve())
        conn.commit()
    except FileExistsError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 3
    finally:
        conn.close()
    print(f"OK: exported {result['project_id']!r}")
    print(f"     nodes: {result['nodes_exported']}")
    print(f"     out:   {result['out_dir']}/specs/")
    return 0


def _cmd_status(args) -> int:
    raw = (args.pidfile or os.environ.get("MANIFOLD_PIDFILE") or "").strip()
    p = Path(raw) if raw else _default_pidfile()
    if not p.is_file():
        print(f"stopped: no pidfile at {p}")
        return 1
    try:
        pid = int(p.read_text(encoding="utf-8").strip())
    except (ValueError, OSError) as exc:
        print(f"stale: pidfile {p} unreadable: {exc}")
        return 2
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        print(f"stale: pid {pid} not running; pidfile {p}")
        return 2
    except PermissionError:
        # Process exists but owned by another user; treat as running.
        print(f"running: pid {pid} (pidfile {p}, not owned by us)")
        return 0
    print(f"running: pid {pid} (pidfile {p})")
    return 0


def _cmd_import(args) -> int:
    from manifold import db, schema, importer
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        result = importer.import_project(
            conn, Path(args.repo).resolve(),
            project_id=args.project_id or None,
            actor=_actor(),
        )
    finally:
        conn.close()
    print(f"OK: imported project {result['project_id']!r}")
    print(f"     nodes: {result['nodes_imported']}")
    print(f"     revisions: {result['revisions_imported']}")
    return 0


def _cmd_show(args) -> int:
    from manifold import db, schema, queries
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        node = queries.get_node(conn, args.project, args.node)
        if node is None:
            print(f"FAIL: node {args.project}:{args.node} not found", file=sys.stderr)
            return 3
        print(f"# {node['node_id']} — {node['title']}")
        print()
        print(f"_(layer: {node['layer']}, kind: {node['kind']}, "
              f"target_status: {node.get('target_status') or '-'})_")
        print()
        print(node["body"])
    finally:
        conn.close()
    return 0


def _cmd_edit(args) -> int:
    from manifold import db, schema, queries, writes
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        node = queries.get_node(conn, args.project, args.node)
        if node is None:
            print(f"FAIL: node {args.project}:{args.node} not found", file=sys.stderr)
            return 3
        editor = os.environ.get("EDITOR", "vi")
        tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
        tmp_path = Path(tmp.name)
        try:
            tmp.write((node["body"] or "").encode("utf-8"))
            tmp.close()
            subprocess.run([editor, str(tmp_path)], check=True)
            new_body = tmp_path.read_text(encoding="utf-8")
        finally:
            tmp_path.unlink(missing_ok=True)
        if new_body == (node["body"] or ""):
            print("No changes; nothing to save.")
            return 0
        result = writes.update_node(
            conn, args.project, args.node, {"body": new_body},
            expected_revision_id=node["current_revision_id"], actor=_actor(),
            source="cli", change_reason=args.reason,
        )
        if result.get("unchanged"):
            print("No effective change; nothing saved.")
        else:
            print(f"OK: wrote revision {result['revision_id']}")
    finally:
        conn.close()
    return 0


def _cmd_snapshot(args) -> int:
    from manifold import config, durability
    out = durability.snapshot(config.db_path())
    print(f"OK: snapshot at {out}")
    return 0


def _cmd_dump(args) -> int:
    from manifold import db, schema, durability
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        durability.dump(conn, Path(args.path))
    finally:
        conn.close()
    print(f"OK: dumped to {args.path}")
    return 0


def _cmd_restore(args) -> int:
    from manifold import config, durability
    durability.restore(Path(args.path), config.db_path())
    print(f"OK: restored to {config.db_path()}")
    return 0


def _cmd_next_leaves(args) -> int:
    from manifold import db, schema, queries
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        rows = queries.next_leaves(
            conn, args.project_id, layer=args.layer, project_root=args.repo,
        )
        show_computed = bool((args.repo or "").strip())
        if show_computed:
            print(f"{'NODE':<14} {'LAYER':<16} {'TARGET':<14} {'STORED':<14} "
                  f"{'COMPUTED':<14} {'MECH':<20} TITLE")
            print("-" * 114)
            for r in rows:
                print(f"{r['node_id']:<14} {r['layer']:<16} "
                      f"{(r['target_status'] or '(unset)'):<14} "
                      f"{(r['verdict_status'] or '(none)'):<14} "
                      f"{(r.get('computed_verdict_status') or '(none)'):<14} "
                      f"{(r['verdict_mechanism'] or '(none)'):<20} {r['title']}")
        else:
            print(f"{'NODE':<14} {'LAYER':<16} {'TARGET':<14} {'STORED':<14} "
                  f"{'MECH':<20} TITLE")
            print("-" * 100)
            for r in rows:
                print(f"{r['node_id']:<14} {r['layer']:<16} "
                      f"{(r['target_status'] or '(unset)'):<14} "
                      f"{(r['verdict_status'] or '(none)'):<14} "
                      f"{(r['verdict_mechanism'] or '(none)'):<20} {r['title']}")
        if args.verbose:
            excluded = queries.next_leaves_excluded(
                conn, args.project_id, layer=args.layer)
            if excluded:
                print()
                print("EXCLUDED (cross-blocked):")
                print(f"  {'NODE':<14} {'BLOCKED BY'}")
                print("  " + "-" * 60)
                for row in excluded:
                    blockers = ", ".join(row.get("blocked_by") or []) or "(unknown)"
                    print(f"  {row['node_id']:<14} {blockers}")
    finally:
        conn.close()
    return 0


def _cmd_spec_audit(args) -> int:
    from manifold import db, schema, queries
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        flagged = queries.spec_audit_flagged_revisions(
            conn, args.project_id,
            since=args.since,
            include_other=args.include_other,
        )
        rationale = queries.spec_audit_unclarified_rationale(
            conn, args.project_id,
            since=args.since,
        )
        print(f"Spec Audit — {args.project_id}")
        print(f"  since:    {args.since or 'beginning of time'}")
        print(f"  flagged revisions:             {len(flagged)}")
        print(f"  unclarified rationale changes:   {len(rationale)}")
        if flagged:
            print()
            print("Flagged Revisions:")
            print(f"  {'NODE':<14} {'REASON':<16} {'TIMESTAMP':<28} SUMMARY")
            print("  " + "-" * 80)
            for r in flagged:
                reason = r.get("change_reason") or "(unset)"
                summary = (r.get("change_summary") or "")[:60]
                ts = r.get("ts") or ""
                node_id = r.get("node_id") or ""
                print(f"  {node_id:<14} {reason:<16} {ts:<28} {summary}")
        if rationale:
            print()
            print("Unclarified Rationale Changes:")
            print(f"  {'NODE':<14} {'REASON':<16} {'TIMESTAMP':<28} SUMMARY")
            print("  " + "-" * 80)
            for r in rationale:
                reason = r.get("change_reason") or "(unset)"
                summary = (r.get("change_summary") or "")[:60]
                ts = r.get("ts") or ""
                node_id = r.get("node_id") or ""
                print(f"  {node_id:<14} {reason:<16} {ts:<28} {summary}")
    finally:
        conn.close()
    return 0


def _cmd_drift_report(args) -> int:
    from manifold import db, schema, queries
    from manifold.drift_report import format_terminal, format_markdown

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        report = queries.drift_report(
            conn, args.project_id,
            project_root=args.repo,
            layer=args.layer,
            all_layers=args.all_layers,
            force=args.force,
        )
    finally:
        conn.close()

    if args.format == "md":
        print(format_markdown(report), end="")
    else:
        print(format_terminal(report, verbose=args.verbose), end="")

    violated = (report.get("summary") or {}).get("violated", 0)
    return 1 if violated else 0


def _cmd_portfolio_report(args) -> int:
    from manifold import db, schema, queries
    from manifold.portfolio_report import format_terminal, format_markdown

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        report = queries.portfolio_report(conn, theme_node_id=args.theme)
    finally:
        conn.close()

    if args.format == "md":
        print(format_markdown(report), end="")
    else:
        print(format_terminal(report), end="")
    return 0


def _cmd_diagram_view(args) -> int:
    from manifold import db, presentation_format, presentation_views, schema, view_registry

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        if args.named_view:
            view = view_registry.build_registered_view(
                conn, args.project_id, args.named_view,
                focus_node_id=args.focus,
                trajectory_id=args.trajectory_id,
            )
        elif args.view == "mindmap":
            view = presentation_views.build_mindmap_view(
                conn, args.project_id,
                mindmap_type=args.type,
                focus_node_id=args.focus,
            )
        else:
            view = presentation_views.build_diagram_view(
                conn, args.project_id,
                diagram_type=args.type,
                focus_node_id=args.focus,
                trajectory_id=args.trajectory_id,
            )
    finally:
        conn.close()

    if args.format == "md":
        print(presentation_format.format_markdown(view), end="")
    else:
        print(presentation_format.format_terminal(view), end="")
    return 0


def _cmd_render(args) -> int:
    from manifold import db, schema, queries, presentation_format, status_brief
    from manifold.portfolio_report import render_quarter_roadmap

    if args.format != "md":
        print("manifold render: only --format md is supported in v1",
              file=sys.stderr)
        return 2

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        if args.subject == "portfolio":
            if args.template != "quarter-roadmap":
                print(f"manifold render: unknown portfolio template {args.template!r} "
                      "(v1: quarter-roadmap)", file=sys.stderr)
                return 2
            report = queries.portfolio_report(conn, theme_node_id=args.theme)
            print(render_quarter_roadmap(report), end="")
            return 0

        if args.subject == "project":
            if not args.project_id:
                print("manifold render project: project_id required",
                      file=sys.stderr)
                return 2
            if args.template != "status-brief":
                print(f"manifold render: unknown project template {args.template!r} "
                      "(v1: status-brief)", file=sys.stderr)
                return 2
            view = status_brief.build_status_brief_view(conn, args.project_id)
            print(presentation_format.format_status_brief_markdown(view), end="")
            return 0
    finally:
        conn.close()

    print(f"manifold render: unknown subject {args.subject!r}", file=sys.stderr)
    return 2


def _cmd_validate(args) -> int:
    from manifold import db, schema, writes
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        result = writes.run_validation(
            conn, args.project,
            with_verdicts=args.with_verdicts,
            with_targets=args.with_targets,
            force=args.force,
            actor=_actor(),
        )
        conn.commit()
    finally:
        conn.close()
    print(f"OK: validation {result['validation_id']} finished")
    print(f"     nodes:    {result['nodes_total']}")
    print(f"     issues:   {result['issues_total']}")
    print(f"     verdicts: {result['verdicts_run']}")
    issues = result.get("issues") or []
    if issues:
        print()
        print("Issues:")
        for i in issues[:20]:
            print(f"  - [{i['kind']}] {i.get('message','')}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
    return 0 if not issues else 1


def _parse_leg_seqs(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def _cmd_trajectory(args) -> int:
    import json as _json
    from manifold import db, schema, trajectory, writes

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        if args.traj_cmd == "propose":
            brief = Path(args.target_brief_file).read_text(encoding="utf-8")
            legs = _json.loads(Path(args.legs_file).read_text(encoding="utf-8"))
            result = trajectory.propose_trajectory(
                conn,
                args.project_id,
                brief,
                legs,
                proposed_by=args.proposed_by or _actor(),
            )
            conn.commit()
            print(_json.dumps(result, indent=2))
            return 0

        if args.traj_cmd == "show":
            report = trajectory.peek_trajectory(
                conn,
                args.trajectory_id,
                leg_seqs=_parse_leg_seqs(args.legs),
            )
            if args.format == "json":
                import json as _json
                print(_json.dumps(report, indent=2))
            else:
                print(trajectory.format_show_markdown(report), end="")
            return 0

        if args.traj_cmd == "accept":
            result = trajectory.accept_trajectory_legs(
                conn,
                args.trajectory_id,
                leg_seqs=_parse_leg_seqs(args.legs),
                actor=args.actor or _actor(),
            )
            conn.commit()
            import json as _json
            print(_json.dumps(result, indent=2))
            return 0

        if args.traj_cmd == "reject":
            result = trajectory.reject_trajectory(
                conn,
                args.trajectory_id,
                actor=args.actor or _actor(),
            )
            conn.commit()
            import json as _json
            print(_json.dumps(result, indent=2))
            return 0

        print(f"unknown trajectory subcommand: {args.traj_cmd}", file=sys.stderr)
        return 2
    except (trajectory.TrajectoryError, writes.WritesError) as exc:
        print(f"trajectory: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
