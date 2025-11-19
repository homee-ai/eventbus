"""
Module for auto-discovering task handlers in the demo application.

This module provides functionality to automatically import all modules under the task
package, which allows for registration of task handlers without explicitly importing
them in the main application code.
"""

import importlib
import pkgutil


def auto_discover():
    """
    Automatically discover and import all modules in the task package.
    
    This function walks through all modules in the task package and imports them,
    which triggers the registration of task handlers through the @register decorator.
    The discovered modules are expected to contain task handler functions that are
    registered using the registry decorator pattern.

    Returns:
        None

    Example:
        >>> auto_discover()
        # This will import all modules under the demo.tasks package
    """
    root_pkg = __package__
    handlers_pkg_name = root_pkg + ".tasks"

    handlers_pkg = importlib.import_module(handlers_pkg_name)

    for mod_info in pkgutil.walk_packages(handlers_pkg.__path__, handlers_pkg.__name__ + "."):
        importlib.import_module(mod_info.name)
