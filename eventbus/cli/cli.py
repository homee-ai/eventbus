from __future__ import annotations

import argparse
from typing import Callable, Dict
from rich.console import Console
from pydantic import ValidationError

from .handler import (
    handle_show_config,
    handle_publish,
    handle_worker,
    handle_dlq_worker,
)
from .logging import setup_logging_config, format_settings_error
from .setting import Settings

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
        help="Task name(s) registered via @register (repeat to subscribe multiple)",
    )

    p_dlq_worker = subs.add_parser(
        "dlq-worker",
        help="Start a DLQ worker that consumes events and dispatches to jobs",
    )
    p_dlq_worker.add_argument(
        "--registry-job-name",
        action="append",
        required=True,
        help="Task name(s) registered via @dlq_register (repeat to subscribe multiple)",
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
    try:
        Settings()
    except ValidationError as e:
        msg = format_settings_error(e)
        console.print(f"[red]Configuration error:\n{msg}[/]")
        raise SystemExit(1)

    parser = build_parser()
    args = parser.parse_args()
    setup_logging_config()

    handlers: Dict[str, CommandHandler] = {
        "show-config": handle_show_config,
        "publish": handle_publish,
        "worker": handle_worker,
        "dlq-worker": handle_dlq_worker,
    }

    handler = handlers.get(args.cmd)
    handler(args)
