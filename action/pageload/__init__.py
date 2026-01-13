"""
Page load utilities module.
"""

from .wait import (
    config,
    PageLoadConfig,
    wait_for_network_idle,
    wait_for_page_load,
    set_timeout,
    set_idle_time,
)

__all__ = [
    "config",
    "PageLoadConfig",
    "wait_for_network_idle",
    "wait_for_page_load",
    "set_timeout",
    "set_idle_time",
]
