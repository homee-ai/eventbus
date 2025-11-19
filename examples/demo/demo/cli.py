from __future__ import annotations

import argparse
from typing import Callable, Dict
from rich.console import Console

from .handler import handle_show_config, handle_publish, handle_worker
from .logging import setup_logging_config

console = Console()
CommandHandler = Callable[[argparse.Namespace], None]


# ========= Helpers =========
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eventbus-cli")
    subs = parser.add_subparsers(dest="cmd", required=True)

    # publish
    p_pub = subs.add_parser("publish", help="Publish a single event to the bus")
    p_pub.add_argument("--type", required=True, help="Event type")
    p_pub.add_argument(
        "--payload",
        help="Event payload as JSON string, e.g. '{\"x\":1}'",
    )

    # worker
    p_worker = subs.add_parser(
        "worker",
        help="Start a worker that consumes events and dispatches to jobs",
    )
    p_worker.add_argument(
        "--registry-job-name",
        action="append",
        required=True,
        help="Job name(s) registered in demo.tasks.job_registry (can repeat)",
    )

    # show-config
    subs.add_parser(
        "show-config",
        description="Get current environment settings",
        help="Show current configuration",
    )

    return parser


# ========= Entry point =========


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging_config()

    handlers: Dict[str, CommandHandler] = {
        "show-config": handle_show_config,
        "publish": handle_publish,
        "worker": handle_worker,
    }

    handler = handlers.get(args.cmd)
    handler(args)
