import sys
from datetime import datetime
from config import LOG_PATH


def _is_mac_bundle() -> bool:
    # UNUserNotificationCenter only works inside a real .app bundle
    # (it crashes with "bundleProxyForCurrentProcess is nil" from a bare python).
    return sys.platform == "darwin" and bool(getattr(sys, "frozen", False))


def request_permission():
    """Ask macOS for notification permission (shows the system dialog once)."""
    if not _is_mac_bundle():
        return
    try:
        from UserNotifications import (
            UNUserNotificationCenter,
            UNAuthorizationOptionAlert,
            UNAuthorizationOptionSound,
        )

        def done(granted, error):
            print(f"  [notify] permission granted={granted} error={error}")

        UNUserNotificationCenter.currentNotificationCenter().requestAuthorizationWithOptions_completionHandler_(
            UNAuthorizationOptionAlert | UNAuthorizationOptionSound, done
        )
    except Exception as exc:
        print(f"  [notify] permission request failed: {exc}")


def _notify_mac_native(title: str, message: str) -> bool:
    try:
        import uuid
        from UserNotifications import (
            UNUserNotificationCenter,
            UNMutableNotificationContent,
            UNNotificationRequest,
            UNNotificationSound,
        )
        content = UNMutableNotificationContent.alloc().init()
        content.setTitle_(title)
        content.setBody_(message)
        content.setSound_(UNNotificationSound.defaultSound())
        request = UNNotificationRequest.requestWithIdentifier_content_trigger_(
            str(uuid.uuid4()), content, None
        )
        def done(error):
            if error is not None:
                print(f"  [notify] delivery error: {error}")

        UNUserNotificationCenter.currentNotificationCenter().addNotificationRequest_withCompletionHandler_(
            request, done
        )
        return True
    except Exception as exc:
        print(f"  [notify] native notification failed: {exc}")
        return False


def notify(title: str, message: str):
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
        notification.notify(title=title, message=message, app_name="Aluguel", timeout=8)
    except Exception as exc:
        print(f"  [notify] failed: {exc}")


def log_listing(listing: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"[{timestamp}] "
        f"{listing.get('bedrooms')}q · "
        f"{listing.get('area')}m² · "
        f"R${listing.get('price'):,} · "
        f"{listing.get('title', '')} · "
        f"{listing.get('url')}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
