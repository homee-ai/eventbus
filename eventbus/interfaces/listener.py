"""Listener interface contract.

Implementations define a unique name() and a handle() method that processes
an incoming message payload with optional context.
"""
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class ListenerContract(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__
    @abstractmethod
    def handle(self, payload: bytes, context: Optional[Dict[str, Any]] = None) -> None: ...
