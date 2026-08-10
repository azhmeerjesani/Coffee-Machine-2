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
                try:
                    import RPi.GPIO as GPIO

                    GPIO.setmode(GPIO.BCM)
                except Exception as exc:
                    logger.exception("Failed to initialize RPi.GPIO")
                    raise RuntimeError(
                        f"Couldn't initialize RPi.GPIO ({exc}). Is it installed "
                        "(pip install RPi.GPIO), and is this user in the gpio group?"
                    ) from exc
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
    try:
        _ensure_pin_ready(gpio, pin)
        gpio.output(pin, gpio.LOW)
        time.sleep(seconds)
    except Exception:
        logger.exception("Pump on pin %s failed while running", pin)
        raise
    finally:
        try:
            gpio.output(pin, gpio.HIGH)
        except Exception:
            logger.exception("Failed to turn OFF pump on pin %s -- check it manually", pin)


def run_pumps_concurrently(pin_durations):
    """Run several pumps in parallel and block until all have finished.

    pin_durations: iterable of (pin, seconds) pairs. Raises RuntimeError
    (after every pump has had a chance to finish/shut off) if any pump
    failed, naming which pins and why.
    """
    errors = []

    def _run(pin, seconds):
        try:
            run_pump(pin, seconds)
        except Exception as exc:
            errors.append((pin, exc))

    threads = [
        threading.Thread(target=_run, args=(pin, seconds))
        for pin, seconds in pin_durations
        if seconds > 0
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        summary = "; ".join(f"pin {pin}: {exc}" for pin, exc in errors)
        raise RuntimeError(f"{len(errors)} pump(s) failed -- {summary}")
