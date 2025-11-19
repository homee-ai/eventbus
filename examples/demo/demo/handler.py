from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Callable

from rich.console import Console
from rich.table import Table

from .setting import load_settings
from eventbus.models import Event
from eventbus.tracing import setup_tracing
from eventbus.bus.google import PubSubEventBus
from .discover import auto_discover
from .registry import REGISTRY, RegistryError

console = Console()


def _parse_payload(raw: str | None) -> Dict[str, Any]:
    """Parse JSON payload string into dict, with a nice error message."""
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON payload:[/] {e}")
        raise SystemExit(1)
    if not isinstance(value, dict):
        console.print("[red]Payload must be a JSON object (e.g. '{\"x\": 1}').[/]")
        raise SystemExit(1)
    return value


def handle_show_config(args: argparse.Namespace) -> None:
    setting = load_settings()

    table = Table(title="Config")
    table.add_column("Key")
    table.add_column("Value")

    for key, value in vars(setting).items():
        table.add_row(key, str(value))

    console.print(table)


def handle_publish(args: argparse.Namespace) -> None:
    """
    Example command:
        eventbus-cli publish --type test --payload '{"x":1}'
    """
    setting = load_settings()
    setup_tracing(
        otlp_endpoint=setting.otlp_endpoint,
        service_name=setting.otlp_service_name,
    )
    payload = _parse_payload(args.payload)

    event = Event(type=args.type, detail=payload)

    with PubSubEventBus(
            project_id=setting.project_id,
            topic_name=setting.topic_id,
            subscription_name=setting.subscription_id,
            auto_create=True,
    ) as bus:
        bus.publish(event)


def handle_worker(args: argparse.Namespace) -> None:
    """
    Start a long-running worker to consume events and dispatch to selected jobs.
    """
    try:
        auto_discover()
    except RegistryError as e:
        console.print(f"[red]Error during auto-discovery task. {e}[/]")
        raise SystemExit(1)

    setting = load_settings()
    setup_tracing(
        otlp_endpoint=setting.otlp_endpoint,
        service_name=setting.otlp_service_name,
    )
    try:
        execution_job_mapping: Dict[str, Callable[..., Any]] = {
            job_name: REGISTRY[job_name] for job_name in args.registry_job_name
        }
    except KeyError as e:
        console.print(f"[red]Task name not found: {e}")
        console.print(f"Available tasks: {', '.join(REGISTRY.keys())}")
        raise SystemExit(1)

    with PubSubEventBus(
            project_id=setting.project_id,
            topic_name=setting.topic_id,
            subscription_name=setting.subscription_id,
            auto_create=True,
    ) as bus:
        bus.subscribe(execution_job_mapping)
        bus.run_forever()
