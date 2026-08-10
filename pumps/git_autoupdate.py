"""Pull the latest code from git the first time the site is opened.

Only ever runs on the Raspberry Pi itself. Running this on a dev machine
would fight with whatever is being edited locally and would never do
anything useful there anyway, so it's a strict no-op everywhere else.
"""

import logging
import subprocess
import threading

from django.conf import settings

from .platform_utils import is_raspberry_pi

logger = logging.getLogger(__name__)

_checked = False
_lock = threading.Lock()


def _git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=settings.BASE_DIR,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


def check_for_updates():
    global _checked
    if _checked:
        return
    with _lock:
        if _checked:
            return
        _checked = True
        if not is_raspberry_pi():
            return
        try:
            _git("fetch", "--quiet")
            local = _git("rev-parse", "HEAD").stdout.strip()
            remote = _git("rev-parse", "@{u}").stdout.strip()
            if local and remote and local != remote:
                logger.info("Coffee machine: update found, pulling latest code from git.")
                result = _git("pull", "--ff-only")
                logger.info(result.stdout)
        except Exception:
            logger.exception("Coffee machine: git auto-update check failed")
