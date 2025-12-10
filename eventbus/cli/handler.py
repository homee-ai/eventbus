from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Callable

from rich.console import Console
from rich.table import Table

from .setting import Settings
from eventbus.models import Event
from eventbus.tracing import setup_tracing
from eventbus.bus.google import PubSubEventBus
from .discover import auto_discover
from .registry import REGISTRY, RegistryError, DLQ_REGISTRY

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


def _registry_job_name() -> None:
    try:
        auto_discover()
    except RegistryError as e:
        console.print(f"[red]Error during auto-discovery task. {e}[/]")
        raise SystemExit(1)


def handle_show_config(args: argparse.Namespace) -> None:
    setting = Settings()
    _registry_job_name()
    console.print()

    def _table(title: str, columns: list[str], data: dict) -> Table:
        table = Table(
            title=f"[bold]{title}[/bold]",
            show_header=True,
            header_style="bold magenta",
            title_justify="left",
        )
        table.add_column(columns[0], style="cyan", no_wrap=True)
        table.add_column(columns[1], style="green")

        for key, value in data.items():
            table.add_row(key, str(value))
        return table

    console.print(
        _table(
            title="Eventbus Settings",
            columns=["Key", "Value"],
            data=dict(vars(setting).items()),
        )
    )
    console.print()
    for registry in [REGISTRY, DLQ_REGISTRY]:
        if not registry:
            console.print("[yellow]No tasks registered yet.[/yellow]")
            continue

        _registry = {key: value.__code__.co_filename for key, value in registry.items()}
        console.print(
            _table(
                title=f"Eventbus Task List ({len(registry)} tasks)",
                columns=["Task Name", "Func"],
                data=_registry,
            )
        )

        task_details = {}
        for task_name, task_func in registry.items():
            func_name = task_func.__name__
            line_no = task_func.__code__.co_firstlineno
            task_details[task_name] = f"{func_name} (line {line_no})"


def handle_publish(args: argparse.Namespace) -> None:
    """
    Example command:
        eventbus-cli publish --type test --payload '{"x":1}'
    """
    setting = Settings()
    setup_tracing(
        otlp_endpoint=setting.otlp_endpoint,
        service_name=setting.otlp_service_name,
    )
    payload = _parse_payload(args.payload)

    event = Event(type=args.type, detail=payload)

    with PubSubEventBus(
        project_id=setting.gcp_project_id,
        topic_name=setting.pubsub_topic_name,
        subscription_name=None,
        auto_create=True,
    ) as bus:
        bus.publish(event)


def handle_worker(args: argparse.Namespace) -> None:
    """
    Start a long-running worker to consume events and dispatch to selected jobs.
    """
    _registry_job_name()

    setting = Settings()
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

    filter_types = None
    if setting.enable_filter_attributes and len(execution_job_mapping) == 1:
        console.print("[yellow]Enabling filter attributes.[/yellow]")
        filter_types = args.registry_job_name

    with PubSubEventBus(
        project_id=setting.gcp_project_id,
        topic_name=setting.pubsub_topic_name,
        subscription_name=setting.pubsub_subscription_name,
        auto_create=True,
        filter_types=filter_types
    ) as bus:
        bus.subscribe(execution_job_mapping)
        bus.run_forever()

def handle_dlq_worker(args: argparse.Namespace) -> None:
    """
    Start a long-running worker to consume events and dispatch to selected jobs.
    """
    _registry_job_name()

    setting = Settings()
    setup_tracing(
        otlp_endpoint=setting.otlp_endpoint,
        service_name=setting.otlp_service_name,
    )
    try:
        execution_job_mapping: Dict[str, Callable[..., Any]] = {
            job_name: DLQ_REGISTRY[job_name] for job_name in args.registry_job_name
        }
    except KeyError as e:
        console.print(f"[red]Task name not found: {e}")
        console.print(f"Available tasks: {', '.join(DLQ_REGISTRY.keys())}")
        raise SystemExit(1)

    with PubSubEventBus(
        project_id=setting.gcp_project_id,
        topic_name=setting.pubsub_dlq_topic_name,
        subscription_name=setting.pubsub_dlq_subscription_name,
        auto_create=True,
    ) as bus:
        bus.subscribe(execution_job_mapping)
        bus.run_forever()