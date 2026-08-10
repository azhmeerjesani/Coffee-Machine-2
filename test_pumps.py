#!/usr/bin/env python3
"""Run each coffee machine pump individually to confirm it's wired and working.

Pin/relay setup is loaded from pump_config.json (same format/pins as the
Hacker Shack Smart Bartender this project is based on). The relay board is
active-low: GPIO.LOW energizes the relay (pump on), GPIO.HIGH de-energizes
it (pump off).

Usage:
    python3 test_pumps.py                  # test every pump, 3s each
    python3 test_pumps.py --pump 3         # test only pump 3
    python3 test_pumps.py --duration 5     # run each pump for 5 seconds
    python3 test_pumps.py --delay 2        # pause 2s between pumps
    python3 test_pumps.py --list           # show configured pumps and pins
"""

import argparse
import json
import sys
import time

CONFIG_PATH = "pump_config.json"


def load_pumps(path):
    with open(path) as f:
        config = json.load(f)
    # sort by pump name (pump_1, pump_2, ...) so testing order matches physical numbering
    return sorted(config.items(), key=lambda item: item[0])


def test_pump(GPIO, name, pin, duration):
    print(f"-> {name} (GPIO {pin}): ON for {duration}s...")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(pin, GPIO.HIGH)
    print(f"   {name}: OFF")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=CONFIG_PATH, help="path to pump_config.json (default: %(default)s)")
    parser.add_argument("--pump", type=int, help="only test this pump number (e.g. 3 for pump_3)")
    parser.add_argument("--duration", type=float, default=3.0, help="seconds to run each pump (default: %(default)s)")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to pause between pumps (default: %(default)s)")
    parser.add_argument("--list", action="store_true", help="list configured pumps and pins, then exit")
    args = parser.parse_args()

    pumps = load_pumps(args.config)

    if args.list:
        for key, cfg in pumps:
            print(f"{key}: {cfg['name']} -> GPIO {cfg['pin']}")
        return

    if args.pump is not None:
        key = f"pump_{args.pump}"
        pumps = [(k, cfg) for k, cfg in pumps if k == key]
        if not pumps:
            sys.exit(f"No pump named '{key}' in {args.config}")

    try:
        import RPi.GPIO as GPIO
    except ImportError:
        sys.exit(
            "RPi.GPIO isn't available. This script controls real GPIO pins and "
            "must be run on the Raspberry Pi, not on a dev machine."
        )

    GPIO.setmode(GPIO.BCM)
    for _, cfg in pumps:
        GPIO.setup(cfg["pin"], GPIO.OUT, initial=GPIO.HIGH)

    try:
        for key, cfg in pumps:
            test_pump(GPIO, cfg["name"], cfg["pin"], args.duration)
            if (key, cfg) != pumps[-1]:
                time.sleep(args.delay)
        print("Done. Confirm each pump you tested actually dispensed liquid.")
    except KeyboardInterrupt:
        print("\nInterrupted, turning off all tested pumps.")
        for _, cfg in pumps:
            GPIO.output(cfg["pin"], GPIO.HIGH)
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
