"""System notifications and the alerts.log.

macOS inside the .app: UNUserNotificationCenter (asks for permission on first launch).
macOS from source: osascript. Windows/Linux: plyer.
"""

import logging
import sys
from datetime import datetime

from farejador import paths
from farejador.config import APP_NAME

log = logging.getLogger(__name__)


def _is_mac_bundle() -> bool:
    # UNUserNotificationCenter only works inside a real .app bundle
    # (it crashes with "bundleProxyForCurrentProcess is nil" from a bare python).
    return sys.platform == "darwin" and bool(getattr(sys, "frozen", False))


def request_permission() -> None:
    """Ask macOS for notification permission (shows the system dialog once)."""
    if not _is_mac_bundle():
        return
    try:
        from UserNotifications import (
            UNAuthorizationOptionAlert,
            UNAuthorizationOptionSound,
            UNUserNotificationCenter,
        )

        def done(granted, error):
            log.info("permission granted=%s error=%s", granted, error)

        UNUserNotificationCenter.currentNotificationCenter().requestAuthorizationWithOptions_completionHandler_(
            UNAuthorizationOptionAlert | UNAuthorizationOptionSound, done
        )
    except Exception as exc:
        log.warning("permission request failed: %s", exc)


def _notify_mac_native(title: str, message: str) -> bool:
    try:
        import uuid

        from UserNotifications import (
            UNMutableNotificationContent,
            UNNotificationRequest,
            UNNotificationSound,
            UNUserNotificationCenter,
        )

        content = UNMutableNotificationContent.alloc().init()
        content.setTitle_(title)
        content.setBody_(message)
        content.setSound_(UNNotificationSound.defaultSound())
        request = UNNotificationRequest.requestWithIdentifier_content_trigger_(str(uuid.uuid4()), content, None)

        def done(error):
            if error is not None:
                log.warning("delivery error: %s", error)

        UNUserNotificationCenter.currentNotificationCenter().addNotificationRequest_withCompletionHandler_(
            request, done
        )
        return True
    except Exception as exc:
        log.warning("native notification failed: %s", exc)
        return False


def notify(title: str, message: str) -> None:
    if sys.platform == "darwin":
        if _is_mac_bundle() and _notify_mac_native(title, message):
            return
        # Dev fallback (plyer needs pyobjus on mac, which we don't ship):
        # osascript, shown as coming from Script Editor.
        import subprocess

        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=False)
        return
    try:
        from plyer import notification  # Windows / Linux

        notification.notify(title=title, message=message, app_name=APP_NAME, timeout=8)
    except Exception as exc:
        log.warning("notification failed: %s", exc)


def log_listing(listing: dict) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"[{timestamp}] "
        f"{listing.get('bedrooms')}q · "
        f"{listing.get('area')}m² · "
        f"R${listing.get('price'):,} · "
        f"{listing.get('title', '')} · "
        f"{listing.get('url')}\n"
    )
    with open(paths.alerts_log_path(), "a", encoding="utf-8") as f:
        f.write(line)
