#!/usr/bin/env python3
"""One-command launcher for the coffee machine website.

Creates a virtual environment (Raspberry Pi OS refuses system-wide pip
installs, PEP 668), installs dependencies into it if missing, applies
database migrations (which also seeds the 6 pumps on a fresh database), and
starts the Django server. Just run:

    python3 run.py

The site listens on 0.0.0.0:8000 so it's reachable from any browser on the
same network (e.g. through Raspberry Pi Connect).
"""

import os
import subprocess
import sys
import venv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, ".venv")
HOST_PORT = "0.0.0.0:8000"


def fail(message):
    print(f"\nERROR: {message}\n", file=sys.stderr)
    sys.exit(1)


def venv_python():
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python"
    return os.path.join(VENV_DIR, bin_dir, exe)


def ensure_venv():
    if os.path.exists(venv_python()):
        return
    print(f"Creating virtual environment at {VENV_DIR} ...")
    try:
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    except Exception as exc:
        fail(
            f"Couldn't create a virtual environment ({exc}).\n"
            "On Raspberry Pi OS this usually means the venv module isn't installed.\n"
            "Try: sudo apt install python3-venv   (or python3-full), then run this again."
        )
    if not os.path.exists(venv_python()):
        fail(
            f"Virtual environment creation reported success, but {venv_python()} "
            "still doesn't exist. Try deleting the .venv folder and running this again."
        )


def relaunch_in_venv():
    """Re-exec this script with the venv's interpreter so pip installs land
    in an isolated environment instead of hitting the system Python (which
    Raspberry Pi OS locks down against direct pip installs)."""
    if os.path.realpath(sys.executable) == os.path.realpath(venv_python()):
        return
    ensure_venv()
    try:
        os.execv(venv_python(), [venv_python(), os.path.abspath(__file__), *sys.argv[1:]])
    except OSError as exc:
        fail(f"Couldn't re-launch inside the virtual environment ({exc}).")


def ensure_dependencies():
    try:
        import django  # noqa: F401

        return
    except ImportError:
        pass
    requirements = os.path.join(BASE_DIR, "requirements.txt")
    if not os.path.exists(requirements):
        fail(f"Couldn't find requirements.txt at {requirements}.")
    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements], check=True)
    except subprocess.CalledProcessError as exc:
        fail(
            f"pip install failed (exit code {exc.returncode}). "
            "Check your internet connection and requirements.txt, then try again."
        )


def run_django(args, description):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coffeeserver.settings")
    sys.path.insert(0, BASE_DIR)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        fail(f"Django still isn't importable after installing dependencies ({exc}).")

    try:
        execute_from_command_line(args)
    except SystemExit as exc:
        if exc.code:
            fail(f"{description} failed (exit code {exc.code}). See the output above for details.")
        raise
    except Exception as exc:
        fail(f"{description} raised an unexpected error: {exc!r}")


def main():
    relaunch_in_venv()
    ensure_dependencies()
    run_django(["manage.py", "migrate", "--noinput"], "Database migration")
    run_django(["manage.py", "runserver", HOST_PORT], "Django server")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down.")
        sys.exit(0)
