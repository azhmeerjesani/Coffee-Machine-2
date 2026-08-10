#!/usr/bin/env python3
"""One-command launcher for the coffee machine website.

Installs dependencies if they're missing, applies database migrations
(which also seeds the 6 pumps on a fresh database), and starts the Django
server. Just run:

    python3 run.py

The site listens on 0.0.0.0:8000 so it's reachable from any browser on the
same network (e.g. through Raspberry Pi Connect).
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOST_PORT = "0.0.0.0:8000"


def ensure_dependencies():
    try:
        import django  # noqa: F401

        return
    except ImportError:
        pass
    print("Installing dependencies from requirements.txt...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", os.path.join(BASE_DIR, "requirements.txt")]
    )


def main():
    ensure_dependencies()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coffeeserver.settings")
    sys.path.insert(0, BASE_DIR)

    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "migrate", "--noinput"])
    execute_from_command_line(["manage.py", "runserver", HOST_PORT])


if __name__ == "__main__":
    main()
