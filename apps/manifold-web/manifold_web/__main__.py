"""python3 -m manifold_web serve — start the web UI (same as `manifold serve`)."""
import sys


def main(argv: list[str] | None = None) -> int:
    from manifold_web.web import serve

    import argparse

    parser = argparse.ArgumentParser(prog="manifold-web")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("serve", help="Start the web server.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7779)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--pidfile", default="")
    args = parser.parse_args(argv)
    if args.cmd == "serve":
        return serve(host=args.host, port=args.port, verbose=args.verbose)
    return 2


if __name__ == "__main__":
    sys.exit(main())
