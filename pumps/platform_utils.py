"""Detect whether this process is running on the Raspberry Pi itself.

Used to gate anything that should only ever happen on the real machine:
driving GPIO pins for real, and pulling code updates from git (pulling on a
dev machine could collide with local edits and never stops being "behind").
"""

import functools
import os

_DEVICE_TREE_MODEL = "/proc/device-tree/model"


@functools.lru_cache(maxsize=1)
def is_raspberry_pi():
    override = os.environ.get("COFFEE_MACHINE_IS_PI")
    if override is not None:
        return override == "1"
    try:
        with open(_DEVICE_TREE_MODEL) as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False
