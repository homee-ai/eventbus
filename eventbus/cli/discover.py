"""
Shared auto-discovery utilities for event handler modules.

This module imports all modules from one or more packages so that any functions
decorated with @register or @dlq_register are executed at import-time and added
into the registries.

Configure packages to scan using the environment variable EVENTBUS_TASKS_PACKAGES,
which accepts a comma-separated list of Python package names. If not provided, we
fallback to a sensible default of scanning the "app_tasks" package if it exists.
"""

import importlib

import pkgutil
from typing import Iterable
from eventbus.cli.setting import Settings


def _iter_modules_in_package(pkg_name: str) -> Iterable[str]:
    """Yield fully-qualified module names contained in the given package."""
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError:
        return []
    if not hasattr(pkg, "__path__"):
        return []
    return (m.name for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."))


def auto_discover() -> None:
    """Discover and import task modules from configured packages.

    Scans packages listed in the EVENTBUS_TASKS_PACKAGES env variable
    (comma-separated). If not set, will try to scan the "app_tasks" package.
    """
    setting = Settings()
    raw = setting.eventbus_tasks_packages

    packages: list[str] = [p.strip() for p in raw.split(",") if p.strip()] if raw else ["tasks"]

    for pkg_name in packages:
        # Import the package itself
        try:
            importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            continue

        # Import all submodules to trigger decorators
        for mod_name in _iter_modules_in_package(pkg_name):
            importlib.import_module(mod_name)
