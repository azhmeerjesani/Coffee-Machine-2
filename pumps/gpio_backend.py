"""Drive the relay board that switches each pump.

The relay board is active-low (same board/wiring as the Hacker Shack Smart
Bartender this project is based on): GPIO.LOW energizes a relay and turns its
pump on, GPIO.HIGH turns it off.

On the Raspberry Pi this uses RPi.GPIO for real. Anywhere else it falls back
to a simulated backend that just logs pin changes, so the website can be
clicked through and reviewed on a dev machine before being pulled to the Pi.
"""

import logging
import threading
import time

from .platform_utils import is_raspberry_pi

logger = logging.getLogger(__name__)

_setup_lock = threading.Lock()
_gpio = None
_initialized_pins = set()


class _SimulatedGPIO:
    """Stand-in for RPi.GPIO when real hardware isn't attached."""

    OUT = "OUT"
    HIGH = 1
    LOW = 0

    def setup(self, pin, mode, initial=None):
        logger.info("[simulated GPIO] setup pin %s (initial=%s)", pin, initial)

    def output(self, pin, value):
        logger.info("[simulated GPIO] pin %s -> %s", pin, "HIGH" if value else "LOW")


def _get_gpio():
    global _gpio
    if _gpio is not None:
        return _gpio
    with _setup_lock:
        if _gpio is None:
            if is_raspberry_pi():
                import RPi.GPIO as GPIO

                GPIO.setmode(GPIO.BCM)
                _gpio = GPIO
            else:
                _gpio = _SimulatedGPIO()
    return _gpio


def _ensure_pin_ready(gpio, pin):
    if pin not in _initialized_pins:
        gpio.setup(pin, gpio.OUT, initial=gpio.HIGH)
        _initialized_pins.add(pin)


def run_pump(pin, seconds):
    """Turn one pump on for `seconds`, then off. Blocks the calling thread."""
    gpio = _get_gpio()
    _ensure_pin_ready(gpio, pin)
    gpio.output(pin, gpio.LOW)
    try:
        time.sleep(seconds)
    finally:
        gpio.output(pin, gpio.HIGH)


def run_pumps_concurrently(pin_durations):
    """Run several pumps in parallel and block until all have finished.

    pin_durations: iterable of (pin, seconds) pairs.
    """
    threads = [
        threading.Thread(target=run_pump, args=(pin, seconds))
        for pin, seconds in pin_durations
        if seconds > 0
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
