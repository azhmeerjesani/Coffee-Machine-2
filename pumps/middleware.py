from .git_autoupdate import check_for_updates


class GitAutoUpdateMiddleware:
    """Triggers the (RPi-only, once-per-process) git update check on the
    first request the server receives, i.e. when the website is opened."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        check_for_updates()
        return self.get_response(request)
