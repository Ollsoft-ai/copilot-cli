"""Deciding whether a graphical web browser is actually available.

The browser login flow is worthless without one: the user stares at a
"Waiting for authentication" line for two minutes and then gets a timeout that
explains nothing. Knowing up front lets `login` prompt in the terminal instead.
"""

import os
import platform
import shutil
import sys
import webbrowser

# Console browsers. On a headless Unix box `webbrowser` will cheerfully hand
# one of these back, and opening it seizes the terminal to render a JavaScript
# SPA that a text browser cannot display anyway -- strictly worse than not
# trying at all, because the user then has to escape from lynx.
_TEXT_BROWSERS = frozenset({"www-browser", "links", "elinks", "lynx", "w3m"})


def _is_wsl() -> bool:
    return "microsoft" in platform.uname().release.lower()


def has_gui_browser() -> bool:
    """True when opening a URL is likely to put it in front of the user."""
    # Windows and macOS register a default handler unconditionally, without
    # probing for anything, so webbrowser.get() can never fail there and tells
    # us nothing. Both effectively always have a browser.
    if sys.platform in ("win32", "darwin"):
        return True

    # WSL reports itself as Linux and normally has no $DISPLAY, yet it can pass
    # the URL to the Windows browser -- provided one of the interop shims is
    # installed. Checking for those is the only reliable signal.
    if _is_wsl():
        return bool(shutil.which("wslview") or shutil.which("powershell.exe"))

    # A Unix box with no display server has no graphical browser to reach,
    # whatever happens to be installed on disk.
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False

    try:
        # Honours $BROWSER, which is how VS Code Remote and similar forward the
        # URL back to the machine the user is sitting at.
        return webbrowser.get().name not in _TEXT_BROWSERS
    except webbrowser.Error:
        return False
